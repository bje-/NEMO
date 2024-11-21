# Copyright (C) 2011, 2012, 2013, 2014, 2022 Ben Elliston
# Copyright (C) 2014, 2015, 2016 The University of New South Wales
# Copyright (C) 2016, 2017 IT Power (Australia)
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Simulated electricity generators for the NEMO framework."""

# pylint: disable=too-many-lines
# We use class names here that upset Pylint.
# pylint: disable=invalid-name

from math import inf, isclose

import numpy as np
import pandas as pd
import requests
from matplotlib.patches import Patch

from nemo import polygons, storage
from nemo.utils import currency, thousands, ureg


class Generator:
    """Base generator class."""

    # Economic lifetime of the generator in years (default 30)
    lifetime = 30

    # Is the generator a rotating machine?
    synchronous_p = True
    """Is this a synchronous generator?"""

    storage_p = False
    """A generator is not capable of storage by default."""

    def __init__(self, polygon, capacity, label=None):
        """Construct a base Generator.

        Arguments: installed polygon, installed capacity, descriptive label.
        """
        if capacity < 0:
            raise ValueError(capacity)
        self.setters = [(self.set_capacity, 0, 40)]
        self.label = self.__class__.__name__ if label is None else label
        self.capacity = capacity
        self.polygon = polygon

        # Sanity check polygon argument.
        if isinstance(polygon, polygons.regions.Region):
            raise TypeError
        if not 0 < polygon <= polygons.NUMPOLYGONS:
            raise AssertionError

        # Time series of dispatched power and spills
        self.series_power = {}
        self.series_spilled = {}

    def series(self):
        """Return generation and spills series."""
        return {'power': pd.Series(self.series_power, dtype=float),
                'spilled': pd.Series(self.series_spilled, dtype=float)}

    def step(self, hour, demand):
        """Step the generator by one hour."""
        raise NotImplementedError

    def region(self):
        """Return the region the generator is in."""
        return polygons.region(self.polygon)

    def capcost(self, costs):
        """Return the capital cost."""
        return costs.capcost_per_kw[type(self)] * self.capacity * 1000

    def opcost(self, costs):
        """Return the annual operating and maintenance cost."""
        return self.fixed_om_costs(costs) + \
            sum(self.series_power.values()) * self.opcost_per_mwh(costs)

    def fixed_om_costs(self, costs):
        """Return the fixed O&M costs."""
        return costs.fixed_om_costs[type(self)] * self.capacity * 1000

    def opcost_per_mwh(self, costs):
        """Return the variable O&M costs."""
        return costs.opcost_per_mwh[type(self)]

    def reset(self):
        """Reset the generator."""
        self.series_power.clear()
        self.series_spilled.clear()

    def capfactor(self):
        """Capacity factor of this generator (in %)."""
        supplied = sum(self.series_power.values())
        hours = len(self.series_power)
        if self.capacity * hours == 0:
            return float('nan')
        return supplied / (self.capacity * hours) * 100

    def lcoe(self, costs, years):
        """Calculate the LCOE in $/MWh."""
        annuityf = costs.annuity_factor(self.lifetime)
        total_cost = self.capcost(costs) / annuityf * years \
            + self.opcost(costs)
        supplied = sum(self.series_power.values())
        if supplied > 0:
            return total_cost / supplied  # cost per MWh
        return inf

    def summary(self, context):
        """Return a summary of the generator activity."""
        costs = context.costs
        supplied = sum(self.series_power.values()) * ureg.MWh
        string = f'supplied {supplied.to_compact()}'
        if self.capacity > 0 and self.capfactor() > 0:
            string += f', CF {self.capfactor():.1f}%'
        if sum(self.series_spilled.values()) > 0:
            spilled = sum(self.series_spilled.values()) * ureg.MWh
            string += f', surplus {spilled.to_compact()}'
        if self.capcost(costs) > 0:
            string += f', capcost {currency(self.capcost(costs))}'
        if self.opcost(costs) > 0:
            string += f', opcost {currency(self.opcost(costs))}'
        lcoe = self.lcoe(costs, context.years())
        if np.isfinite(lcoe) and lcoe > 0:
            string += f', LCOE {currency(int(lcoe))}'
        return string

    def set_capacity(self, cap):
        """Change the capacity of the generator to cap GW."""
        self.capacity = cap * 1000

    def __str__(self):
        """Return a short string representation of the generator."""
        return f'{self.label} ({self.region()}:{self.polygon}), ' + \
            str(self.capacity * ureg.MW)

    def __repr__(self):
        """Return a representation of the generator."""
        return self.__str__()


# This class is not to be confused with storage.py.
# This class will go away soon.

class Storage:
    """A class to give a generator storage capability."""

    storage_p = True
    """This generator is capable of storage."""

    def __init__(self):
        """Storage constructor."""
        # Time series of charges
        self.series_charge = {}
        self.series_soc = {}

    def soc(self):
        """Return the storage SOC (state of charge)."""
        raise NotImplementedError

    def record(self, hour, energy):
        """Record storage."""
        if hour not in self.series_charge:
            self.series_charge[hour] = 0
        self.series_charge[hour] += energy
        self.series_soc[hour] = self.soc()

    def charge_capacity(self, gen, hour):
        """Return available storage capacity.

        Since a storage-capable generator can be called on multiple
        times to store energy in a single timestep, we keep track of
        how much remaining capacity is available for charging in the
        given timestep.
        """
        try:
            result = gen.capacity - self.series_charge[hour]
        except KeyError:
            return gen.capacity
        if result < 0 and isclose(result, 0, abs_tol=1e-6):
            result = 0
        if result < 0:
            raise AssertionError
        return result

    def series(self):
        """Return generation and spills series."""
        return {'charge': pd.Series(self.series_charge, dtype=float),
                'soc': pd.Series(self.series_soc, dtype=float)}

    def store(self, hour, power):
        """Abstract method to ensure that derived classes define this."""
        raise NotImplementedError

    def reset(self):
        """Reset a generator with storage."""
        self.series_charge.clear()
        self.series_soc.clear()


class TraceGenerator(Generator):
    """A generator that gets its hourly dispatch from a trace."""

    def __init__(self, polygon, capacity, label=None, build_limit=None):
        """Construct a generator with a specified trace file."""
        Generator.__init__(self, polygon, capacity, label)
        if build_limit is not None:
            # Override default capacity limit with build_limit
            _, _, limit = self.setters[0]
            self.setters = [(self.set_capacity, 0, min(build_limit, limit))]

    def step(self, hour, demand):
        """Step method for any generator using traces."""
        # self.generation must be defined by derived classes
        # pylint: disable=no-member
        generation = self.generation[hour] * self.capacity
        power = min(generation, demand)
        spilled = generation - power
        self.series_power[hour] = power
        self.series_spilled[hour] = spilled
        return power, spilled


class CSVTraceGenerator(TraceGenerator):
    """A generator that gets its hourly dispatch from a CSV trace file."""

    csvfilename = None
    csvdata = None

    def __init__(self, polygon, capacity, filename, column, label=None,
                 build_limit=None):
        """Construct a generator with a specified trace file."""
        TraceGenerator.__init__(self, polygon, capacity, label, build_limit)
        cls = self.__class__
        if cls.csvfilename != filename:
            # Optimisation:
            # Only if the filename changes do we invoke genfromtxt.
            if not filename.startswith('http'):
                # Local file path
                traceinput = filename
            else:
                try:
                    resp = requests.request('GET', filename, timeout=5)
                except requests.exceptions.Timeout as exc:
                    msg = f'timeout fetching {filename}'
                    raise TimeoutError(msg) from exc
                if not resp.ok:
                    msg = f'HTTP {resp.status_code}: {filename}'
                    raise ConnectionError(msg)
                traceinput = resp.text.splitlines()
            cls.csvdata = np.genfromtxt(traceinput, encoding='UTF-8',
                                        delimiter=',')
            cls.csvdata = np.maximum(0, cls.csvdata)
            # check no elements are NaNs
            msg = f'Trace file {filename} contains NaNs; inspect file'
            if np.any(np.isnan(cls.csvdata)):
                raise AssertionError(msg)
            cls.csvfilename = filename
        # pylint limitation: https://github.com/pylint-dev/pylint/issues/9250
        # pylint: disable=unsubscriptable-object
        self.generation = cls.csvdata[::, column]


class Wind(CSVTraceGenerator):
    """Wind power."""

    patch = Patch(facecolor='#417505')
    """Patch for plotting"""
    synchronous_p = False
    """Is this a synchronous generator?"""


class WindOffshore(Wind):
    """Offshore wind power."""

    patch = Patch(facecolor='darkgreen')
    """Colour for plotting"""


class PV(CSVTraceGenerator):
    """Solar photovoltaic (PV) model."""

    synchronous_p = False
    """Is this a synchronous generator?"""


class PV1Axis(PV):
    """Single-axis tracking PV."""

    patch = Patch(facecolor='#fed500')
    """Colour for plotting"""


class Behind_Meter_PV(PV):
    """Behind the meter PV."""

    patch = Patch(facecolor='#ffe03d')


class CST(CSVTraceGenerator):
    """Concentrating solar thermal (CST) model."""

    patch = Patch(facecolor='orange')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, solarmult, shours, filename,
                 column, label=None, build_limit=None):
        """Construct a CST generator.

        Arguments include capacity (in MW), sm (solar multiple) and
        shours (hours of storage).
        """
        CSVTraceGenerator.__init__(self, polygon, capacity, filename, column,
                                   label)
        self.maxstorage = None
        self.stored = None
        self.set_storage(shours)
        self.set_multiple(solarmult)

    def set_capacity(self, cap):
        """Change the capacity of the generator to cap GW."""
        Generator.set_capacity(self, cap)
        self.maxstorage = self.capacity * self.shours

    def set_multiple(self, solarmult):
        """Change the solar multiple of a CST plant."""
        self.solarmult = solarmult

    def set_storage(self, shours):
        """Change the storage capacity of a CST plant."""
        self.shours = shours
        self.maxstorage = self.capacity * shours
        self.stored = 0.5 * self.maxstorage

    def step(self, hour, demand):
        """Step method for CST generators."""
        generation = self.generation[hour] * self.capacity * self.solarmult
        remainder = min(self.capacity, demand)
        if generation > remainder:
            to_storage = generation - remainder
            generation -= to_storage
            self.stored += to_storage
            self.stored = min(self.stored, self.maxstorage)
        else:
            from_storage = min(remainder - generation, self.stored)
            generation += from_storage
            self.stored -= from_storage
            if self.stored < 0:
                raise AssertionError
        if self.stored > self.maxstorage:
            raise AssertionError
        if self.stored < 0:
            raise AssertionError
        self.series_power[hour] = generation
        self.series_spilled[hour] = 0

        # This can happen due to rounding errors.
        generation = min(generation, demand)
        return generation, 0

    def reset(self):
        """Reset the generator."""
        Generator.reset(self)
        self.stored = 0.5 * self.maxstorage

    def summary(self, context):
        """Return a summary of the generator activity."""
        return Generator.summary(self, context) + \
            f', solar mult {self.solarmult:.2f}' + \
            f', {self.shours}h storage'


class ParabolicTrough(CST):
    """Parabolic trough CST generator.

    This stub class allows differentiated CST costs in costs.py.
    """


class CentralReceiver(CST):
    """Central receiver CST generator.

    This stub class allows differentiated CST costs in costs.py.
    """


class Fuelled(Generator):
    """The class of generators that consume fuel."""

    def __init__(self, polygon, capacity, label):
        """Construct a fuelled generator."""
        Generator.__init__(self, polygon, capacity, label)
        self.runhours = 0

    def reset(self):
        """Reset the generator."""
        Generator.reset(self)
        self.runhours = 0

    def step(self, hour, demand):
        """Step method for fuelled generators."""
        power = min(self.capacity, demand)
        if power > 0:
            self.runhours += 1
        self.series_power[hour] = power
        self.series_spilled[hour] = 0
        return power, 0

    def summary(self, context):
        """Return a summary of the generator activity."""
        return Generator.summary(self, context) + \
            f', ran {thousands(self.runhours)} hours'


class Hydro(Fuelled):
    """Hydro power stations."""

    patch = Patch(facecolor='#4582b4')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, label=None):
        """Construct a hydroelectric generator."""
        Fuelled.__init__(self, polygon, capacity, label)
        # capacity is in MW, but build limit is in GW
        self.setters = [(self.set_capacity, 0, capacity / 1000.)]


class PumpedHydroPump(Storage, Generator):
    """Pumped hydro (pump side) model."""

    patch = Patch(facecolor='darkblue')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, reservoirs, rte=0.8, label=None):
        """Construct a pumped hydro storage generator."""
        if not isinstance(reservoirs, storage.PumpedHydroStorage):
            raise TypeError
        Storage.__init__(self)
        Generator.__init__(self, polygon, capacity, label)
        # capacity is in MW, but build limit is in GW
        self.setters = [(self.set_capacity, 0, capacity / 1000.)]
        self.reservoirs = reservoirs
        self.rte = rte

    def step(self, hour, demand):
        """Return 0 as this is not a generator."""
        return 0, 0

    def series(self):
        """Return the combined series."""
        dict1 = Hydro.series(self)
        dict2 = Storage.series(self)
        dict1.update(dict2)
        return dict1

    def soc(self):
        """Return the pumped hydro SOC (state of charge)."""
        return self.reservoirs.soc()

    def store(self, hour, power):
        """Pump water uphill for one hour."""
        if self.reservoirs.last_gen == hour:
            # Can't pump and generate in the same hour.
            return 0
        power = min(self.charge_capacity(self, hour), power,
                    self.capacity)

        stored = self.reservoirs.charge(power * self.rte)
        if stored < power * self.rte:
            power = (self.reservoirs.maxstorage - self.reservoirs.storage) \
                / self.rte

        if power > 0:
            self.record(hour, power)
            self.reservoirs.last_pump = hour
        return power

    def reset(self):
        """Reset the generator."""
        Generator.reset(self)
        Storage.reset(self)
        self.reservoirs.reset()

    def summary(self, context):
        """Return a summary of the generator activity."""
        stg = (self.reservoirs.maxstorage * ureg.MWh).to_compact()
        return Generator.summary(self, context) + \
            f', charged {thousands(len(self.series_charge))} hours' + \
            f', {stg} storage'


class PumpedHydroTurbine(Hydro):
    """Pumped storage hydro (generator side) model."""

    patch = Patch(facecolor='powderblue')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, reservoirs, label=None):
        """Construct a pumped hydro storage generator."""
        if not isinstance(reservoirs, storage.PumpedHydroStorage):
            raise TypeError
        Hydro.__init__(self, polygon, capacity, label)
        self.reservoirs = reservoirs

    def step(self, hour, demand):
        """Step method for pumped hydro storage."""
        power = min(self.reservoirs.storage, self.capacity, demand)
        if self.reservoirs.last_pump == hour:
            # Can't pump and generate in the same hour.
            self.series_power[hour] = 0
            self.series_spilled[hour] = 0
            return 0, 0

        self.reservoirs.discharge(power)
        self.series_power[hour] = power
        self.series_spilled[hour] = 0
        if power > 0:
            self.runhours += 1
            self.reservoirs.last_gen = hour
        return power, 0


class Biofuel(Fuelled):
    """Model of open cycle gas turbines burning biofuel."""

    patch = Patch(facecolor='wheat')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, label=None):
        """Construct a biofuel generator."""
        Fuelled.__init__(self, polygon, capacity, label)

    def capcost(self, costs):
        """Return the capital cost (of an OCGT)."""
        return costs.capcost_per_kw[OCGT] * self.capacity * 1000

    def fixed_om_costs(self, costs):
        """Return the fixed O&M costs (of an OCGT)."""
        return costs.fixed_om_costs[OCGT] * self.capacity * 1000

    def opcost_per_mwh(self, costs):
        """Return the variable O&M costs."""
        vom = costs.opcost_per_mwh[OCGT]
        fuel_cost = costs.bioenergy_price_per_gj * (3.6 / .31)  # 31% heat rate
        return vom + fuel_cost


class Biomass(Fuelled):
    """Model of steam turbine burning solid biomass."""

    patch = Patch(facecolor='#1d7a7a')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, label=None, heatrate=0.3):
        """Construct a biomass generator."""
        Fuelled.__init__(self, polygon, capacity, label)
        self.heatrate = heatrate

    def opcost_per_mwh(self, costs):
        """Return the variable O&M costs."""
        vom = costs.opcost_per_mwh[type(self)]
        fuel_cost = costs.bioenergy_price_per_gj * (3.6 / self.heatrate)
        return vom + fuel_cost


class Fossil(Fuelled):
    """Base class for GHG emitting power stations."""

    patch = Patch(facecolor='grey')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, intensity, label=None):
        """Construct a fossil fuelled generator.

        Greenhouse gas emissions intensity is given in tonnes per MWh.
        """
        Fuelled.__init__(self, polygon, capacity, label)
        self.intensity = intensity

    def summary(self, context):
        """Return a summary of the generator activity."""
        generation = sum(self.series_power.values()) * ureg.MWh
        emissions = generation * self.intensity * (ureg.t / ureg.MWh)
        return Fuelled.summary(self, context) + \
            f', {emissions.to("Mt")} CO2'


class Black_Coal(Fossil):
    """Black coal power stations with no CCS."""

    patch = Patch(facecolor='#121212')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, intensity=0.773, label=None):
        """Construct a black coal generator."""
        Fossil.__init__(self, polygon, capacity, intensity, label)

    def opcost_per_mwh(self, costs):
        """Return the variable O&M costs."""
        vom = costs.opcost_per_mwh[type(self)]
        fuel_cost = costs.coal_price_per_gj * 8.57
        carbon_cost = self.intensity * costs.carbon
        return vom + fuel_cost + carbon_cost


class OCGT(Fossil):
    """Open cycle gas turbine (OCGT) model."""

    patch = Patch(facecolor='#ffcd96')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, intensity=0.7, label=None):
        """Construct an OCGT generator."""
        Fossil.__init__(self, polygon, capacity, intensity, label)

    def opcost_per_mwh(self, costs):
        """Return the variable O&M costs."""
        vom = costs.opcost_per_mwh[type(self)]
        fuel_cost = costs.gas_price_per_gj * 11.61
        carbon_cost = self.intensity * costs.carbon
        return vom + fuel_cost + carbon_cost


class CCGT(Fossil):
    """Combined cycle gas turbine (CCGT) model."""

    patch = Patch(facecolor='#fdb462')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, intensity=0.4, label=None):
        """Construct a CCGT generator."""
        Fossil.__init__(self, polygon, capacity, intensity, label)

    def opcost_per_mwh(self, costs):
        """Return the variable O&M costs."""
        vom = costs.opcost_per_mwh[type(self)]
        fuel_cost = costs.gas_price_per_gj * 6.92
        carbon_cost = self.intensity * costs.carbon
        return vom + fuel_cost + carbon_cost


class CCS(Fossil):
    """Base class of carbon capture and storage (CCS)."""

    def __init__(self, polygon, capacity, intensity, capture, label=None):
        """Construct a CCS generator.

        Emissions capture rate is given in the range 0 to 1.
        """
        Fossil.__init__(self, polygon, capacity, intensity, label)
        if not 0 <= capture <= 1:
            raise ValueError(capture)
        self.capture = capture

    def summary(self, context):
        """Return a summary of the generator activity."""
        generation = sum(self.series_power.values()) * ureg.MWh
        emissions = generation * self.intensity * (ureg.t / ureg.MWh)
        captured = emissions * self.capture
        return Fossil.summary(self, context) + \
            f', {captured.to("Mt")} captured'


class Coal_CCS(CCS):
    """Coal with CCS."""

    def __init__(self, polygon, capacity, intensity=0.8, capture=0.85,
                 label=None):
        """Construct a coal CCS generator.

        Emissions capture rate is given in the range 0 to 1.
        """
        CCS.__init__(self, polygon, capacity, intensity, capture, label)

    def opcost_per_mwh(self, costs):
        """Return the variable O&M costs."""
        vom = costs.opcost_per_mwh[type(self)]
        # thermal efficiency 31.4% (AETA 2012)
        fuel_cost = costs.coal_price_per_gj * (3.6 / 0.314)
        # t CO2/MWh
        emissions_rate = 0.103
        carbon_cost = emissions_rate * costs.carbon + \
            self.intensity * self.capture * costs.ccs_storage_per_t
        return vom + fuel_cost + carbon_cost


class CCGT_CCS(CCS):
    """CCGT with CCS."""

    def __init__(self, polygon, capacity, intensity=0.4, capture=0.85,
                 label=None):
        """Construct a CCGT (with CCS) generator.

        Emissions capture rate is given in the range 0 to 1.
        """
        CCS.__init__(self, polygon, capacity, intensity, capture, label)

    def opcost_per_mwh(self, costs):
        """Return the variable O&M costs."""
        vom = costs.opcost_per_mwh[type(self)]
        # thermal efficiency 43.1% (AETA 2012)
        fuel_cost = costs.gas_price_per_gj * (3.6 / 0.431)
        carbon_cost = \
            self.intensity * (1 - self.capture) * costs.carbon + \
            self.intensity * self.capture * costs.ccs_storage_per_t
        return vom + fuel_cost + carbon_cost


class Diesel(Fossil):
    """Diesel genset model."""

    patch = Patch(facecolor='#f35020')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, intensity=1.0, kwh_per_litre=3.3,
                 label=None):
        """Construct a diesel generator."""
        Fossil.__init__(self, polygon, capacity, intensity, label)
        self.kwh_per_litre = kwh_per_litre

    def opcost_per_mwh(self, costs):
        """Return the variable O&M costs."""
        vom = costs.opcost_per_mwh[type(self)]
        litres_per_mwh = (1 / self.kwh_per_litre) * 1000
        fuel_cost = costs.diesel_price_per_litre * litres_per_mwh
        carbon_cost = self.intensity * costs.carbon
        return vom + fuel_cost + carbon_cost


class BatteryLoad(Storage, Generator):
    """Battery storage (load side)."""

    patch = Patch(facecolor='#b2daef')
    """Colour for plotting"""
    synchronous_p = False
    """Is this a synchronous generator?"""

    def __init__(self, polygon, capacity, battery, label=None,
                 discharge_hours=None, rte=0.95):
        """Construct a battery load (battery charging).

        battery must be an instance of storage.BatteryStorage.
        discharge_hours is a list of hours when discharging can occur
          (or, rather, when charging cannot occur).
        """
        Storage.__init__(self)
        Generator.__init__(self, polygon, capacity, label)
        if not isinstance(battery, storage.BatteryStorage):
            raise TypeError
        self.battery = battery
        self.rte = rte
        self.discharge_hours = discharge_hours \
            if discharge_hours is not None else range(18, 24)

    def step(self, hour, demand):
        """Return 0 as this is not a generator."""
        return 0, 0

    def store(self, hour, power):
        """Store power."""
        if power <= 0:
            msg = f'{power} is <= 0'
            raise AssertionError(msg)

        if self.battery.full_p() or \
           hour % 24 in self.discharge_hours:
            return 0

        power = min(self.charge_capacity(self, hour), power,
                    self.capacity)
        stored = self.battery.charge(power * self.rte)
        if power > 0:
            self.record(hour, stored / self.rte)
        return stored / self.rte

    def reset(self):
        """Reset the generator."""
        Generator.reset(self)
        Storage.reset(self)
        self.battery.reset()

    def series(self):
        """Return the combined series."""
        dict1 = Generator.series(self)
        dict2 = Storage.series(self)
        dict1.update(dict2)
        return dict1

    def soc(self):
        """Return the battery SOC (state of charge)."""
        return self.battery.soc()

    # Battery costs are all calculated on the discharge side.
    def capcost(self, costs):
        """Return the capital cost."""
        return 0

    def fixed_om_costs(self, costs):
        """Return the fixed O&M costs."""
        return 0

    def opcost_per_mwh(self, costs):
        """Return the variable O&M costs."""
        return 0

    def summary(self, context):
        """Return a summary of the generator activity."""
        mwh = self.battery.maxstorage * ureg.MWh
        return Generator.summary(self, context) + \
            f', charged {thousands(len(self.series_charge))} hours' + \
            f', {mwh.to_compact()} storage'


class Battery(Generator):
    """Battery storage (of any type)."""

    # Lifespan of the battery in years
    lifetime = 15

    patch = Patch(facecolor='#00a2fa')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, shours, battery,
                 label=None, discharge_hours=None):
        """Construct a battery generator.

        battery must be an instance of storage.BatteryStorage.
        shours is the number of hours of storage at full load.
        discharge_hours is a list of hours when discharging can occur.
        """
        if not isinstance(battery, storage.BatteryStorage):
            raise TypeError
        Generator.__init__(self, polygon, capacity, label)
        self.battery = battery
        self.runhours = 0
        self.shours = shours
        if shours not in [1, 2, 4, 8]:
            raise ValueError(shours)
        if capacity * shours != battery.maxstorage:
            raise ValueError
        self.discharge_hours = discharge_hours \
            if discharge_hours is not None else range(18, 24)

    def set_capacity(self, cap):
        """Change the capacity of the generator to cap GW."""
        Generator.set_capacity(self, cap)
        # now alter the storage to match the new capacity
        newmax = self.capacity * self.shours
        self.battery.set_storage(newmax)

    def step(self, hour, demand):
        """Specialised step method for batteries."""
        if self.battery.empty_p() or \
           hour % 24 not in self.discharge_hours:
            self.series_power[hour] = 0
            self.series_spilled[hour] = 0
            return 0, 0

        power = min(self.battery.storage, self.capacity, demand)
        self.battery.discharge(power)
        self.series_power[hour] = power
        self.series_spilled[hour] = 0
        if power > 0:
            self.runhours += 1
        return power, 0

    def reset(self):
        """Reset the generator."""
        Generator.reset(self)
        self.battery.reset()
        self.runhours = 0

    def soc(self):
        """Return the battery SOC (state of charge)."""
        return self.battery.soc()

    def capcost(self, costs):
        """Return the capital cost."""
        kwh = self.battery.maxstorage * 1000
        if self.shours not in [1, 2, 4, 8]:
            raise ValueError(self.shours)
        cost_per_kwh = costs.totcost_per_kwh[type(self)][self.shours]
        return kwh * cost_per_kwh

    def fixed_om_costs(self, costs):
        """Return the fixed O&M costs."""
        return 0

    def opcost_per_mwh(self, costs):
        """Return the variable O&M costs.

        Per-kWh costs for batteries are included in the capital cost.
        """
        return 0

    def summary(self, context):
        """Return a summary of the generator activity."""
        return Generator.summary(self, context) + \
            f', {self.shours}h storage' + \
            f', ran {thousands(self.runhours)} hours'


class Geothermal(CSVTraceGenerator):
    """Geothermal power plant."""

    patch = Patch(facecolor='indianred')
    """Colour for plotting"""

    def step(self, hour, demand):
        """Specialised step method for geothermal generators.

        Geothermal power plants do not spill.
        """
        generation = self.generation[hour] * self.capacity
        power = min(generation, demand)
        self.series_power[hour] = power
        self.series_spilled[hour] = 0
        return power, 0


class Geothermal_HSA(Geothermal):
    """Hot sedimentary aquifer (HSA) geothermal model."""


class Geothermal_EGS(Geothermal):
    """Enhanced geothermal systems (EGS) geothermal model."""


class DemandResponse(Generator):
    """Load shedding generator.

    >>> dr = DemandResponse(polygons.WILDCARD, 500, 1500)
    """

    patch = Patch(facecolor='white')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, cost_per_mwh, label=None):
        """Construct a demand response 'generator'.

        The demand response opportunity cost is given by
        cost_per_mwh. There is assumed to be no capital cost.
        """
        Generator.__init__(self, polygon, capacity, label)
        self.setters = []
        self.runhours = 0
        self.maxresponse = 0
        self.cost_per_mwh = cost_per_mwh

    def step(self, hour, demand):
        """Specialised step method for demand response.

        >>> dr = DemandResponse(polygons.WILDCARD, 500, 1500)
        >>> dr.step(hour=0, demand=200)
        (200, 0)
        >>> dr.runhours
        1
        """
        power = min(self.capacity, demand)
        self.maxresponse = max(self.maxresponse, power)
        self.series_power[hour] = power
        self.series_spilled[hour] = 0
        if power > 0:
            self.runhours += 1
        return power, 0

    def reset(self):
        """Reset the generator."""
        Generator.reset(self)
        self.runhours = 0
        self.maxresponse = 0

    def opcost_per_mwh(self, costs):
        """Return the variable O&M costs."""
        return self.cost_per_mwh

    def summary(self, context):
        """Return a summary of the generator activity."""
        return Generator.summary(self, context) + \
            f', max response {self.maxresponse} MW' + \
            f', ran {thousands(self.runhours)} hours'


class Block(Generator):
    """A simple block generator."""

    patch = Patch(facecolor='darkgreen')
    """Colour for plotting"""

    def step(self, hour, demand):
        """Step method for GreenPower."""
        power = min(self.capacity, demand)
        self.series_power[hour] = power
        self.series_spilled[hour] = 0
        return power, 0


class Electrolyser(Storage, Generator):
    """A hydrogen electrolyser."""

    patch = Patch(facecolor='teal')
    """Colour for plotting"""

    def __init__(self, tank, polygon, capacity, efficiency=0.8, label=None):
        """Construct a hydrogen electrolyser.

        Arguments include the associated storage vessel (the 'tank'),
        the capacity of the electrolyser (in MW) and electrolysis
        conversion efficiency.
        """
        if not isinstance(tank, storage.HydrogenStorage):
            raise TypeError
        Storage.__init__(self)
        Generator.__init__(self, polygon, capacity, label)
        self.efficiency = efficiency
        self.tank = tank
        self.setters += [(self.tank.set_storage, 0, 10000)]

    def soc(self):
        """Return the hydrogen tank state of charge (SOC)."""
        return self.tank.soc()

    def series(self):
        """Return the combined series."""
        dict1 = Generator.series(self)
        dict2 = Storage.series(self)
        dict1.update(dict2)
        return dict1

    def step(self, hour, demand):
        """Return 0 as this is not a generator."""
        return 0, 0

    def reset(self):
        """Reset the generator."""
        Storage.reset(self)
        Generator.reset(self)

    def store(self, _, power):
        """Store power."""
        power = min(power, self.capacity)
        stored = self.tank.charge(power * self.efficiency)
        return stored / self.efficiency


class HydrogenGT(Fuelled):
    """A combustion turbine fuelled by hydrogen."""

    patch = Patch(facecolor='violet')
    """Colour for plotting"""

    def __init__(self, tank, polygon, capacity, efficiency=0.36, label=None):
        """Construct a HydrogenGT object.

        >>> h = storage.HydrogenStorage(1000, 'test')
        >>> gt = HydrogenGT(h, 1, 100, efficiency=0.5)
        >>> gt
        HydrogenGT (QLD1:1), 100.00 MW
        >>> gt.step(0, 100) # discharge 100 MWh-e of hydrogen
        (100.0, 0)
        >>> gt.step(0, 100) # discharge another 100 MWh-e of hydrogen
        (100.0, 0)
        >>> h.storage == (1000 / 2.) - (200 / gt.efficiency)
        True
        """
        if not isinstance(tank, storage.HydrogenStorage):
            raise TypeError(tank)
        Fuelled.__init__(self, polygon, capacity, label)
        self.tank = tank
        self.efficiency = efficiency

    def step(self, hour, demand):
        """Step method for hydrogen comubstion turbine generators."""
        # calculate hydrogen requirement
        hydrogen = min(self.capacity, demand) / self.efficiency
        # discharge that amount of hydrogen
        power = self.tank.discharge(hydrogen) * self.efficiency
        self.series_power[hour] = power
        self.series_spilled[hour] = 0
        if power > 0:
            self.runhours += 1
        return power, 0

    def capcost(self, costs):
        """Return the capital cost (of an OCGT)."""
        return costs.capcost_per_kw[OCGT] * self.capacity * 1000

    def fixed_om_costs(self, costs):
        """Return the fixed O&M costs (of an OCGT)."""
        return costs.fixed_om_costs[OCGT] * self.capacity * 1000

    def opcost_per_mwh(self, costs):
        """Return the variable O&M costs (of an OCGT)."""
        return costs.opcost_per_mwh[OCGT]
