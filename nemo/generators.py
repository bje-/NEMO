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

import locale
from math import isclose

import numpy as np
import pandas as pd
import pint
import requests
from matplotlib.patches import Patch

from nemo import polygons

# Needed for currency formatting.
locale.setlocale(locale.LC_ALL, '')

# Default to abbreviated units when formatting
ureg = pint.UnitRegistry()
ureg.default_format = '.2f~P'


def _thousands(value):
    """
    Format a value with thousands separator(s).

    No doctest provided as the result will be locale specific.
    """
    return locale.format_string('%d', value, grouping=True)


def _currency(value):
    """
    Format a value into currency with thousands separator(s).

    If there are zero cents, remove .00 for brevity.  No doctest
    provided as the result will be locale specific.
    """
    cents = locale.localeconv()['mon_decimal_point'] + '00'
    return locale.currency(round(value), grouping=True).replace(cents, '')


class Generator():
    """Base generator class."""

    # Is the generator a rotating machine?
    synchronous_p = True
    """Is this a synchronous generator?"""

    storage_p = False
    """A generator is not capable of storage by default."""

    def __init__(self, polygon, capacity, label=None):
        """
        Construct a base Generator.

        Arguments: installed polygon, installed capacity, descriptive label.
        """
        assert capacity >= 0
        self.setters = [(self.set_capacity, 0, 40)]
        self.label = self.__class__.__name__ if label is None else label
        self.capacity = capacity
        self.polygon = polygon

        # Sanity check polygon argument.
        assert not isinstance(polygon, polygons.regions.Region)
        assert 0 < polygon <= polygons.NUMPOLYGONS, polygon

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
        """Return the annual capital cost."""
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
        try:
            capfactor = supplied / (self.capacity * hours) * 100
            return capfactor
        except ZeroDivisionError:
            return float('nan')

    def lcoe(self, costs, years):
        """Calculate the LCOE in $/MWh."""
        total_cost = self.capcost(costs) / costs.annuityf * years \
            + self.opcost(costs)
        supplied = sum(self.series_power.values())
        if supplied > 0:
            cost_per_mwh = total_cost / supplied
            return cost_per_mwh
        return np.inf

    def summary(self, context):
        """Return a summary of the generator activity."""
        costs = context.costs
        supplied = sum(self.series_power.values()) * ureg.MWh
        string = f'supplied {supplied.to_compact()}'
        if self.capacity > 0:
            if self.capfactor() > 0:
                string += f', CF {self.capfactor():.1f}%'
        if sum(self.series_spilled.values()) > 0:
            spilled = sum(self.series_spilled.values()) * ureg.MWh
            string += f', surplus {spilled.to_compact()}'
        if self.capcost(costs) > 0:
            string += f', capcost {_currency(self.capcost(costs))}'
        if self.opcost(costs) > 0:
            string += f', opcost {_currency(self.opcost(costs))}'
        lcoe = self.lcoe(costs, context.years)
        if np.isfinite(lcoe) and lcoe > 0:
            string += f', LCOE {_currency(int(lcoe))}'
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


class Storage():
    """A class to give a generator storage capability."""

    storage_p = True
    """This generator is capable of storage."""

    def __init__(self):
        """Storage constructor."""
        # Time series of charges
        self.series_charge = {}

    def record(self, hour, power):
        """Record storage."""
        if hour not in self.series_charge:
            self.series_charge[hour] = 0
        self.series_charge[hour] += power

    def charge_capacity(self, gen, hour):
        """Return available storage capacity.

        Since a storage-capable generator can be called on multiple
        times to store energy in a single timestep, we keep track of
        how much remaining capacity is available for charging in the
        given timestep.
        """
        try:
            result = gen.capacity - self.series_charge[hour]
            assert result >= 0
            return result
        except KeyError:
            return gen.capacity

    def series(self):
        """Return generation and spills series."""
        return {'charge': pd.Series(self.series_charge, dtype=float)}

    def store(self, hour, power):
        """Abstract method to ensure that derived classes define this."""
        raise NotImplementedError

    def reset(self):
        """Reset a generator with storage."""
        self.series_charge.clear()


class TraceGenerator(Generator):
    """A generator that gets its hourly dispatch from a CSV trace file."""

    csvfilename = None
    csvdata = None

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
                    raise TimeoutError(f'timeout fetching {filename}') from exc
                if not resp.ok:
                    msg = f'HTTP {resp.status_code}: {filename}'
                    raise ConnectionError(msg)
                traceinput = resp.text.splitlines()
            cls.csvdata = np.genfromtxt(traceinput, encoding='UTF-8',
                                        delimiter=',')
            cls.csvdata = np.maximum(0, cls.csvdata)
            cls.csvfilename = filename
        self.generation = cls.csvdata[::, column]


class Wind(CSVTraceGenerator):
    """Wind power."""

    patch = Patch(facecolor='green')
    """Patch for plotting"""
    synchronous_p = False
    """Is this a synchronous generator?"""


class WindOffshore(Wind):
    """Offshore wind power."""

    patch = Patch(facecolor='darkgreen')
    """Colour for plotting"""


class PV(CSVTraceGenerator):
    """Solar photovoltaic (PV) model."""

    patch = Patch(facecolor='yellow')
    """Colour for plotting"""
    synchronous_p = False
    """Is this a synchronous generator?"""


class PV1Axis(PV):
    """
    Single-axis tracking PV.

    This stub class allows differentiated PV costs in costs.py.
    """


class Behind_Meter_PV(PV):
    """
    Behind the meter PV.

    This stub class allows differentiated PV costs in costs.py.
    """


class CST(CSVTraceGenerator):
    """Concentrating solar thermal (CST) model."""

    patch = Patch(facecolor='gold')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, solarmult, shours, filename,
                 column, label=None, build_limit=None):
        """
        Construct a CST generator.

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
            assert self.stored >= 0
        assert self.stored <= self.maxstorage
        assert self.stored >= 0
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
            f', ran {_thousands(self.runhours)} hours'


class Hydro(Fuelled):
    """Hydro power stations."""

    patch = Patch(facecolor='lightskyblue')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, label=None):
        """Construct a hydroelectric generator."""
        Fuelled.__init__(self, polygon, capacity, label)
        # capacity is in MW, but build limit is in GW
        self.setters = [(self.set_capacity, 0, capacity / 1000.)]


class PumpedHydro(Storage, Hydro):
    """Pumped storage hydro (PSH) model."""

    patch = Patch(facecolor='powderblue')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, maxstorage, rte=0.8, label=None):
        """Construct a pumped hydro storage generator."""
        Hydro.__init__(self, polygon, capacity, label)
        Storage.__init__(self)
        self.maxstorage = maxstorage
        # Half the water starts in the lower reservoir.
        self.stored = self.maxstorage * .5
        self.rte = rte
        self.last_run = None

    def series(self):
        """Return the combined series."""
        dict1 = Hydro.series(self)
        dict2 = Storage.series(self)
        # combine dictionaries
        return {**dict1, **dict2}

    def store(self, hour, power):
        """Pump water uphill for one hour."""
        if self.last_run == hour:
            # Can't pump and generate in the same hour.
            return 0
        power = min(self.charge_capacity(self, hour), power,
                    self.capacity)
        energy = power * self.rte
        if self.stored + energy > self.maxstorage:
            power = (self.maxstorage - self.stored) / self.rte
            self.stored = self.maxstorage
        else:
            self.stored += energy
        if power > 0:
            self.last_run = hour
        return power

    def step(self, hour, demand):
        """Step method for pumped hydro storage."""
        power = min(self.stored, self.capacity, demand)
        if self.last_run == hour:
            # Can't pump and generate in the same hour.
            self.series_power[hour] = 0
            self.series_spilled[hour] = 0
            return 0, 0
        self.series_power[hour] = power
        self.series_spilled[hour] = 0
        self.stored -= power
        if power > 0:
            self.runhours += 1
            self.last_run = hour
        return power, 0

    def summary(self, context):
        """Return a summary of the generator activity."""
        storage = (self.maxstorage * ureg.MWh).to_compact()
        return Generator.summary(self, context) + \
            f', ran {_thousands(self.runhours)} hours' + \
            f', {storage} storage'

    def reset(self):
        """Reset the generator."""
        Fuelled.reset(self)
        self.stored = self.maxstorage * .5
        self.last_run = None


class Biofuel(Fuelled):
    """Model of open cycle gas turbines burning biofuel."""

    patch = Patch(facecolor='wheat')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, label=None):
        """Construct a biofuel generator."""
        Fuelled.__init__(self, polygon, capacity, label)

    def capcost(self, costs):
        """Return the annual capital cost (of an OCGT)."""
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

    patch = Patch(facecolor='greenyellow')
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

    patch = Patch(facecolor='brown')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, intensity, label=None):
        """
        Construct a fossil fuelled generator.

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

    patch = Patch(facecolor='black')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, intensity=0.773, label=None):
        """Construct a black coal generator."""
        Fossil.__init__(self, polygon, capacity, intensity, label)

    def opcost_per_mwh(self, costs):
        """Return the variable O&M costs."""
        vom = costs.opcost_per_mwh[type(self)]
        fuel_cost = costs.coal_price_per_gj * 8.57
        total_opcost = vom + fuel_cost + self.intensity * costs.carbon
        return total_opcost


class OCGT(Fossil):
    """Open cycle gas turbine (OCGT) model."""

    patch = Patch(facecolor='purple')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, intensity=0.7, label=None):
        """Construct an OCGT generator."""
        Fossil.__init__(self, polygon, capacity, intensity, label)

    def opcost_per_mwh(self, costs):
        """Return the variable O&M costs."""
        vom = costs.opcost_per_mwh[type(self)]
        fuel_cost = costs.gas_price_per_gj * 11.61
        total_opcost = vom + fuel_cost + self.intensity * costs.carbon
        return total_opcost


class CCGT(Fossil):
    """Combined cycle gas turbine (CCGT) model."""

    patch = Patch(facecolor='purple')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, intensity=0.4, label=None):
        """Construct a CCGT generator."""
        Fossil.__init__(self, polygon, capacity, intensity, label)

    def opcost_per_mwh(self, costs):
        """Return the variable O&M costs."""
        vom = costs.opcost_per_mwh[type(self)]
        fuel_cost = costs.gas_price_per_gj * 6.92
        total_opcost = vom + fuel_cost + self.intensity * costs.carbon
        return total_opcost


class CCS(Fossil):
    """Base class of carbon capture and storage (CCS)."""

    def __init__(self, polygon, capacity, intensity, capture, label=None):
        """Construct a CCS generator.

        Emissions capture rate is given in the range 0 to 1.
        """
        Fossil.__init__(self, polygon, capacity, intensity, label)
        assert 0 <= capture <= 1
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
        total_opcost = vom + fuel_cost + \
            (emissions_rate * costs.carbon) + \
            (self.intensity * self.capture * costs.ccs_storage_per_t)
        return total_opcost


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
        total_opcost = vom + fuel_cost + \
            (self.intensity * (1 - self.capture) * costs.carbon) + \
            (self.intensity * self.capture * costs.ccs_storage_per_t)
        return total_opcost


class Diesel(Fossil):
    """Diesel genset model."""

    patch = Patch(facecolor='dimgrey')
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
        total_opcost = vom + fuel_cost + self.intensity * costs.carbon
        return total_opcost


class Battery(Storage, Generator):
    """Battery storage (of any type)."""

    patch = Patch(facecolor='grey')
    """Colour for plotting"""
    synchronous_p = False
    """Is this a synchronous generator?"""

    def __init__(self, polygon, capacity, shours, label=None,
                 discharge_hours=None, rte=0.95):
        """
        Construct a battery generator.

        Storage (shours) is specified in duration hours at full power.
        Discharge hours is a list of hours when discharging can occur.
        Round-trip efficiency (rte) defaults to 95% for good Li-ion.
        """
        Storage.__init__(self)
        Generator.__init__(self, polygon, capacity, label)
        self.stored = 0
        assert shours in [1, 2, 4, 8]
        self.set_storage(shours)
        self.discharge_hours = discharge_hours \
            if discharge_hours is not None else range(18, 24)
        self.rte = rte
        self.runhours = 0

    def series(self):
        """Return the combined series."""
        dict1 = Generator.series(self)
        dict2 = Storage.series(self)
        # combine dictionaries
        return {**dict1, **dict2}

    def set_capacity(self, cap):
        """Change the capacity of the generator to cap GW."""
        Generator.set_capacity(self, cap)
        self.set_storage(self.shours)

    def set_storage(self, shours):
        """Vary the full load hours of battery storage."""
        assert shours in [1, 2, 4, 8]
        self.shours = shours
        self.maxstorage = self.capacity * shours
        self.stored = 0

    def empty_p(self):
        """Return True if the storage is empty."""
        return self.stored == 0

    def full_p(self):
        """Return True if the storage is full."""
        return self.maxstorage == self.stored

    def store(self, hour, power):
        """Store power."""
        assert power > 0, f'{power} is <= 0'

        if self.full_p() or \
           hour % 24 in self.discharge_hours:
            return 0

        power = min(self.charge_capacity(self, hour), power,
                    self.capacity)
        energy = power
        if self.stored + energy > self.maxstorage:
            energy = self.maxstorage - self.stored
        self.stored += energy
        if energy > 0:
            self.record(hour, energy)
        assert self.stored <= self.maxstorage or \
            isclose(self.stored, self.maxstorage)
        return energy

    def step(self, hour, demand):
        """Specialised step method for batteries."""
        if self.empty_p() or \
           hour % 24 not in self.discharge_hours:
            self.series_power[hour] = 0
            self.series_spilled[hour] = 0
            return 0, 0

        assert demand > 0
        power = min(self.stored, self.capacity, demand) * self.rte
        self.series_power[hour] = power
        self.series_spilled[hour] = 0
        self.stored -= power
        if power > 0:
            self.runhours += 1
        assert self.stored >= 0 or isclose(self.stored, 0)
        return power, 0

    def reset(self):
        """Reset the generator."""
        Generator.reset(self)
        self.runhours = 0
        self.stored = 0

    def capcost(self, costs):
        """Return the annual capital cost."""
        assert self.shours in [1, 2, 4, 8]
        cost_per_kwh = costs.totcost_per_kwh[type(self)][self.shours]
        capcost = cost_per_kwh * self.shours
        return capcost * self.capacity * 1000

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
            f', ran {_thousands(self.runhours)} hours' + \
            f', charged {_thousands(len(self.series_charge))} hours' + \
            f', {self.shours}h storage'


class Geothermal(CSVTraceGenerator):
    """Geothermal power plant."""

    patch = Patch(facecolor='brown')
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
    """
    Load shedding generator.

    >>> dr = DemandResponse(polygons.WILDCARD, 500, 1500)
    """

    patch = Patch(facecolor='white')
    """Colour for plotting"""

    def __init__(self, polygon, capacity, cost_per_mwh, label=None):
        """
        Construct a demand response 'generator'.

        The demand response opportunity cost is given by
        cost_per_mwh. There is assumed to be no capital cost.
        """
        Generator.__init__(self, polygon, capacity, label)
        self.setters = []
        self.runhours = 0
        self.maxresponse = 0
        self.cost_per_mwh = cost_per_mwh

    def step(self, hour, demand):
        """
        Specialised step method for demand response.

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
            f', ran {_thousands(self.runhours)} hours'


class GreenPower(Generator):
    """A simple block GreenPower generator."""

    patch = Patch(facecolor='darkgreen')
    """Colour for plotting"""

    def step(self, hour, demand):
        """Step method for GreenPower."""
        power = min(self.capacity, demand)
        self.series_power[hour] = power
        self.series_spilled[hour] = 0
        return power, 0


class HydrogenStorage():
    """A simple hydrogen storage vessel."""

    def __init__(self, maxstorage, label=None):
        """Construct a hydrogen storage vessel.

        The storage capacity (in MWh) is specified by maxstorage.
        """
        # initialise these for good measure
        self.maxstorage = None
        self.storage = None
        self.set_storage(maxstorage)
        self.label = label

    def set_storage(self, maxstorage):
        """
        Change the storage capacity.

        >>> h = HydrogenStorage(1000, 'test')
        >>> h.set_storage(1200)
        >>> h.maxstorage
        1200
        >>> h.storage
        600.0
        """
        self.maxstorage = maxstorage
        self.storage = self.maxstorage / 2

    def charge(self, amt):
        """
        Charge the storage by amt.

        >>> h = HydrogenStorage(1000, 'test')
        >>> h.charge(100)
        100
        >>> h.charge(600)
        400.0
        >>> h.storage == h.maxstorage
        True
        """
        assert amt >= 0
        delta = min(self.maxstorage - self.storage, amt)
        self.storage = min(self.maxstorage, self.storage + amt)
        return delta

    def discharge(self, amt):
        """
        Discharge the storage by 'amt'.

        >>> h = HydrogenStorage(1000, 'test')
        >>> h.discharge(100)
        100
        >>> h.discharge(600)
        400.0
        """
        assert amt >= 0
        delta = min(self.storage, amt)
        self.storage = max(0, self.storage - amt)
        return delta


class Electrolyser(Storage, Generator):
    """A hydrogen electrolyser."""

    patch = Patch()
    """Colour for plotting"""

    def __init__(self, tank, polygon, capacity, efficiency=0.8, label=None):
        """
        Construct a hydrogen electrolyser.

        Arguments include the associated storage vessel (the 'tank'),
        the capacity of the electrolyser (in MW) and electrolysis
        conversion efficiency.
        """
        if not isinstance(tank, HydrogenStorage):
            raise TypeError
        Storage.__init__(self)
        Generator.__init__(self, polygon, capacity, label)
        self.efficiency = efficiency
        self.tank = tank
        self.setters += [(self.tank.set_storage, 0, 10000)]

    def series(self):
        """Return the combined series."""
        dict1 = Generator.series(self)
        dict2 = Storage.series(self)
        # combine dictionaries
        return {**dict1, **dict2}

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
        """
        Construct a HydrogenGT object.

        >>> h = HydrogenStorage(1000, 'test')
        >>> gt = HydrogenGT(h, 1, 100, efficiency=0.5)
        >>> print(gt)
        HydrogenGT (QLD1:1), 100.00 MW
        >>> gt.step(0, 100) # discharge 100 MWh-e of hydrogen
        (100.0, 0)
        >>> gt.step(0, 100) # discharge another 100 MWh-e of hydrogen
        (100.0, 0)
        >>> h.storage == (1000 / 2.) - (200 / gt.efficiency)
        True
        """
        assert isinstance(tank, HydrogenStorage)
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
        """Return the annual capital cost (of an OCGT)."""
        return costs.capcost_per_kw[OCGT] * self.capacity * 1000

    def fixed_om_costs(self, costs):
        """Return the fixed O&M costs (of an OCGT)."""
        return costs.fixed_om_costs[OCGT] * self.capacity * 1000

    def opcost_per_mwh(self, costs):
        """Return the variable O&M costs (of an OCGT)."""
        return costs.opcost_per_mwh[OCGT]
