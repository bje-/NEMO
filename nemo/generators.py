# Copyright (C) 2011, 2012, 2013, 2014 Ben Elliston
# Copyright (C) 2014, 2015, 2016 The University of New South Wales
# Copyright (C) 2016, 2017 IT Power (Australia)
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Simulated generators for the NEMO framework."""
import locale

import urllib.request, urllib.error, urllib.parse
import numpy as np
from matplotlib.patches import Patch

from nemo.anywh import anyWh
from nemo import polygons


# Needed for currency formatting.
locale.setlocale(locale.LC_ALL, '')


class Generator(object):

    """Base generator class."""

    def __init__(self, polygon, capacity, label):
        """Base class constructor.

        Arguments: installed polygon, installed capacity, descriptive label.
        """
        self.setters = [(self.set_capacity, 0, 40)]
        self.storage_p = False
        self.label = label
        self.capacity = capacity
        self.polygon = polygon

        # Sanity check polygon argument.
        assert not isinstance(polygon, polygons.regions.Region)
        assert polygon >= 1 and polygon <= polygons.numpolygons, polygon

        # Is the generator a rotating machine?
        self.non_synchronous_p = False

        # Time series of dispatched power and spills
        self.series_power = {}
        self.series_spilled = {}

        # By default, generators have infinite ramping capability
        self.power = 0
        self.ramp_up_mw_per_h = np.inf
        self.ramp_down_mw_per_h = np.inf

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
        """Reset the generator.

        >>> g = Generator(1, 0, 'label')
        >>> g.power = 10
        >>> g.reset()
        >>> g.power
        0
        """
        self.series_power.clear()
        self.series_spilled.clear()
        self.power = 0

    def capfactor(self):
        """Capacity factor of this generator (in %).

        >>> g = Generator(1, 0, 'label')
        >>> g.capfactor()  # doctest: +ELLIPSIS
        nan
        """
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
        s = 'supplied %s' % anyWh(sum(self.series_power.values()))
        if self.capacity > 0:
            cf = self.capfactor()
            if cf > 0:
                s += ', CF %.1f%%' % cf
        if sum(self.series_spilled.values()) > 0:
            s += ', surplus %s' % anyWh(sum(self.series_spilled.values()))
        if self.capcost(costs) > 0:
            s += ', capcost $%s' % locale.format('%d', self.capcost(costs), grouping=True)
        if self.opcost(costs) > 0:
            s += ', opcost $%s' % locale.format('%d', self.opcost(costs), grouping=True)
        lcoe = self.lcoe(costs, context.years)
        if np.isfinite(lcoe) and lcoe > 0:
            s += ', LCOE $%d' % int(lcoe)
        return s

    def set_capacity(self, cap):
        """Change the capacity of the generator to 'cap' GW."""
        self.capacity = cap * 1000

    def __str__(self):
        """A short string representation of the generator."""
        return '%s (%s:%s), %s' \
            % (self.label, self.region(), self.polygon,
               anyWh(self.capacity, 'W'))

    def __repr__(self):
        """A representation of the generator."""
        return self.__str__()


class Wind(Generator):

    """Wind power."""

    patch = Patch(facecolor='green')
    csvfilename = None
    csvdata = None

    def __init__(self, polygon, capacity, filename, column, delimiter=None, build_limit=None, label='wind'):
        Generator.__init__(self, polygon, capacity, label)
        if build_limit is not None:
            # Override default capacity limit with build_limit
            _, _, limit = self.setters[0]
            self.setters = [(self.set_capacity, 0, min(build_limit, limit))]
        self.non_synchronous_p = True
        if Wind.csvfilename != filename:
            # Optimisation:
            # Only if the filename changes do we invoke genfromtxt.
            urlobj = urllib.request.urlopen(filename)
            Wind.csvdata = np.genfromtxt(urlobj, comments='#', delimiter=delimiter)
            Wind.csvdata = np.maximum(0, Wind.csvdata)
            Wind.csvfilename = filename
        self.generation = Wind.csvdata[::, column]

    def step(self, hr, demand):
        """Step method for wind generators."""
        generation = self.generation[hr] * self.capacity
        power = min(generation, demand)
        spilled = generation - power
        self.series_power[hr] = power
        self.series_spilled[hr] = spilled
        return power, spilled


class PV(Generator):

    """Solar photovoltaic (PV) model."""

    patch = Patch(facecolor='yellow')
    csvfilename = None
    csvdata = None

    def __init__(self, polygon, capacity, filename, column, build_limit=None, label='PV'):
        Generator.__init__(self, polygon, capacity, label)
        self.non_synchronous_p = True
        if build_limit is not None:
            # Override default capacity limit with build_limit
            _, _, limit = self.setters[0]
            self.setters = [(self.set_capacity, 0, min(build_limit, limit))]
        if PV.csvfilename != filename:
            urlobj = urllib.request.urlopen(filename)
            PV.csvdata = np.genfromtxt(urlobj, comments='#', delimiter=',')
            PV.csvdata = np.maximum(0, PV.csvdata)
            PV.csvfilename = filename
        self.generation = PV.csvdata[::, column]

    def step(self, hr, demand):
        """Step method for PV generators."""
        generation = self.generation[hr] * self.capacity
        power = min(generation, demand)
        spilled = generation - power
        self.series_power[hr] = power
        self.series_spilled[hr] = spilled
        return power, spilled


class PV1Axis(PV):
    """Single-axis tracking PV."""

    patch = Patch(facecolor='lightyellow')

    def __init__(self, polygon, capacity, filename, column, build_limit=None, label='PV 1-axis'):
        PV.__init__(self, polygon, capacity, filename, column, build_limit, label)


class Behind_Meter_PV(PV):
    """Behind the meter PV.

    This stub class allows differentiated PV costs in costs.py."""

    def __init__(self, polygon, capacity, filename, column, build_limit=None, label='Behind-meter PV'):
        PV.__init__(self, polygon, capacity, filename, column, build_limit, label)


class CST(Generator):

    """Concentrating solar thermal (CST) model."""

    patch = Patch(facecolor='yellow')
    csvfilename = None
    csvdata = None

    def __init__(self, polygon, capacity, sm, shours, filename, column, build_limit=None, label='CST'):
        Generator.__init__(self, polygon, capacity, label)
        if build_limit is not None:
            # Override default capacity limit with build_limit
            _, _, limit = self.setters[0]
            self.setters = [(self.set_capacity, 0, min(build_limit, limit))]
        self.sm = sm
        if CST.csvfilename != filename:
            urlobj = urllib.request.urlopen(filename)
            CST.csvdata = np.genfromtxt(urlobj, comments='#', delimiter=',')
            CST.csvfilename = filename
        self.generation = CST.csvdata[::, column]
        self.shours = shours
        self.maxstorage = capacity * shours
        self.stored = 0.5 * self.maxstorage

    def set_capacity(self, cap):
        Generator.set_capacity(self, cap)
        self.maxstorage = cap * 1000 * self.shours

    def step(self, hr, demand):
        """Step method for CST generators."""
        generation = self.generation[hr] * self.capacity * self.sm
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
        # assert generation <= self.capacity
        self.series_power[hr] = generation
        self.series_spilled[hr] = 0

        if generation > demand:
            # This can happen due to rounding errors.
            generation = demand
        return generation, 0

    def reset(self):
        Generator.reset(self)
        self.stored = 0.5 * self.maxstorage

    def summary(self, context):
        return Generator.summary(self, context) + \
            ', solar mult %.2f' % self.sm + ', %dh storage' % self.shours


class ParabolicTrough(CST):

    """Parabolic trough CST generator.

    This stub class allows differentiated CST costs in costs.py.
    """
    pass


class CentralReceiver(CST):

    """Central receiver CST generator.

    This stub class allows differentiated CST costs in costs.py.
    """
    pass


class Fuelled(Generator):

    """The class of generators that consume fuel."""

    def __init__(self, polygon, capacity, label):
        Generator.__init__(self, polygon, capacity, label)
        self.runhours = 0

    def reset(self):
        Generator.reset(self)
        self.runhours = 0

    def step(self, hr, demand):
        """Step method for fuelled generators."""
        power = min(self.capacity, demand)
        if power > 0:
            self.runhours += 1
        self.series_power[hr] = power
        return power, 0

    def summary(self, context):
        return Generator.summary(self, context) + ', ran %s hours' \
            % locale.format('%d', self.runhours, grouping=True)


class Hydro(Fuelled):

    """Hydro power stations."""

    patch = Patch(facecolor='lightskyblue')

    def __init__(self, polygon, capacity, label='hydro'):
        Fuelled.__init__(self, polygon, capacity, label)
        # capacity is in MW, but build limit is in GW
        self.setters = [(self.set_capacity, 0, capacity / 1000.)]


class PumpedHydro(Hydro):

    """Pumped storage hydro (PSH) model."""

    patch = Patch(facecolor='powderblue')

    def __init__(self, polygon, capacity, maxstorage, rte=0.8, label='pumped-hydro'):
        Hydro.__init__(self, polygon, capacity, label)
        self.maxstorage = maxstorage
        # Half the water starts in the lower reservoir.
        self.stored = self.maxstorage * .5
        self.rte = rte
        self.storage_p = True
        self.last_run = None

    def store(self, hr, power):
        """Pump water uphill for one hour.

        >>> psh = PumpedHydro(polygons.wildcard, 250, 1000, rte=1.0)

        Cannot pump and generate at the same time.
        >>> psh.step(hr=0, demand=100)
        (100, 0)
        >>> psh.store(hr=0, power=250)
        0

        Test filling the store.
        >>> for hour in range(1, 4): psh.store(hr=hour, power=250)
        250
        250
        100.0
        """
        if self.last_run == hr:
            # Can't pump and generate in the same hour.
            return 0
        power = min(power, self.capacity)
        energy = power * self.rte
        if self.stored + energy > self.maxstorage:
            power = (self.maxstorage - self.stored) / self.rte
            self.stored = self.maxstorage
        else:
            self.stored += energy
        if power > 0:
            self.last_run = hr
        return power

    def step(self, hr, demand):
        """
        >>> psh = PumpedHydro(polygons.wildcard, 250, 1000, rte=1.0)

        Cannot pump and generate at the same time.
        >>> psh.store(hr=0, power=250)
        250
        >>> psh.step(hr=0, demand=100)
        (0, 0)
        """
        power = min(self.stored, min(self.capacity, demand))
        if self.last_run == hr:
            # Can't pump and generate in the same hour.
            return 0, 0
        self.series_power[hr] = power
        self.stored -= power
        if power > 0:
            self.runhours += 1
            self.last_run = hr
        return power, 0

    def summary(self, context):
        return Generator.summary(self, context) + \
            ', ran %s hours' % locale.format('%d', self.runhours, grouping=True) + \
            ', %s storage' % anyWh(self.maxstorage)

    def reset(self):
        Fuelled.reset(self)
        self.stored = self.maxstorage * .5
        self.last_run = None


class Biofuel(Fuelled):

    """Model of open cycle gas turbines burning biofuel."""

    patch = Patch(facecolor='wheat')

    def __init__(self, polygon, capacity, label='biofuel'):
        Fuelled.__init__(self, polygon, capacity, label)

    def opcost_per_mwh(self, costs):
        vom = costs.opcost_per_mwh[type(self)]
        fuel_cost = costs.bioenergy_price_per_gj * (3.6 / .31)  # 31% heat rate
        return vom + fuel_cost


class Biomass(Fuelled):

    """Model of steam turbine burning solid biomass."""

    patch = Patch(facecolor='greenyellow')

    def __init__(self, polygon, capacity, label='biomass', heatrate=0.3):
        Fuelled.__init__(self, polygon, capacity, label)
        self.heatrate = heatrate

    def opcost_per_mwh(self, costs):
        vom = costs.opcost_per_mwh[type(self)]
        fuel_cost = costs.bioenergy_price_per_gj * (3.6 / self.heatrate)
        return vom + fuel_cost


class Fossil(Fuelled):

    """Base class for GHG emitting power stations."""

    patch = Patch(facecolor='brown')

    def __init__(self, polygon, capacity, intensity, label='fossil'):
        # Greenhouse gas intensity in tonnes per MWh
        Fuelled.__init__(self, polygon, capacity, label)
        self.intensity = intensity

    def summary(self, context):
        return Fuelled.summary(self, context) + ', %.1f Mt CO2' \
            % (sum(self.series_power.values()) * self.intensity / 1000000.)


class Black_Coal(Fossil):

    """Black coal power stations with no CCS."""

    patch = Patch(facecolor='black')

    def __init__(self, polygon, capacity, intensity=0.773, label='coal'):
        Fossil.__init__(self, polygon, capacity, intensity, label)

    def opcost_per_mwh(self, costs):
        vom = costs.opcost_per_mwh[type(self)]
        fuel_cost = costs.coal_price_per_gj * 8.57
        total_opcost = vom + fuel_cost + self.intensity * costs.carbon
        return total_opcost


class OCGT(Fossil):

    """Open cycle gas turbine (OCGT) model."""

    patch = Patch(facecolor='purple')

    def __init__(self, polygon, capacity, intensity=0.7, label='OCGT'):
        Fossil.__init__(self, polygon, capacity, intensity, label)

    def opcost_per_mwh(self, costs):
        vom = costs.opcost_per_mwh[type(self)]
        fuel_cost = costs.gas_price_per_gj * 11.61
        total_opcost = vom + fuel_cost + self.intensity * costs.carbon
        return total_opcost


class CCGT(Fossil):

    """Combined cycle gas turbine (CCGT) model."""

    patch = Patch(facecolor='purple')

    def __init__(self, polygon, capacity, intensity=0.4, label='CCGT'):
        Fossil.__init__(self, polygon, capacity, intensity, label)

    def opcost_per_mwh(self, costs):
        vom = costs.opcost_per_mwh[type(self)]
        fuel_cost = costs.gas_price_per_gj * 6.92
        total_opcost = vom + fuel_cost + self.intensity * costs.carbon
        return total_opcost


class CCS(Fossil):

    """Base class of carbon capture and storage (CCS)."""

    def __init__(self, polygon, capacity, intensity, capture, label='CCS'):
        Fossil.__init__(self, polygon, capacity, intensity, label)
        # capture fraction ranges from 0 to 1
        self.capture = capture

    def summary(self, context):
        return Fossil.summary(self, context) + ', %.1f Mt captured' \
            % (sum(self.series_power.values()) * self.intensity / 1000000. * self.capture)


class Coal_CCS(CCS):

    """Coal with CCS."""

    def __init__(self, polygon, capacity, intensity=0.8, capture=0.85, label='Coal-CCS'):
        CCS.__init__(self, polygon, capacity, intensity, capture, label)

    def opcost_per_mwh(self, costs):
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

    def __init__(self, polygon, capacity, intensity=0.4, capture=0.85, label='CCGT-CCS'):
        CCS.__init__(self, polygon, capacity, intensity, capture, label)

    def opcost_per_mwh(self, costs):
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

    def __init__(self, polygon, capacity, intensity=1.0, kwh_per_litre=3.3, label='diesel'):
        Fossil.__init__(self, polygon, capacity, intensity, label)
        self.kwh_per_litre = kwh_per_litre

    def opcost_per_mwh(self, costs):
        vom = costs.opcost_per_mwh[type(self)]
        litres_per_mwh = (1 / self.kwh_per_litre) * 1000
        fuel_cost = costs.diesel_price_per_litre * litres_per_mwh
        total_opcost = vom + fuel_cost + self.intensity * costs.carbon
        return total_opcost


class Battery(Generator):

    """Battery storage (of any type)."""

    patch = Patch(facecolor='grey')

    def __init__(self, polygon, capacity, maxstorage, dischargeHours=list(range(24)), rte=0.95, label='battery'):
        Generator.__init__(self, polygon, capacity, label)
        self.non_synchronous_p = True
        self.setters += [(self.set_storage, 0, 10000)]
        self.maxstorage = maxstorage
        self.stored = 0
        self.dischargeHours = dischargeHours
        self.rte = rte
        self.storage_p = True
        self.last_run = None
        self.runhours = 0
        self.chargehours = 0

    def set_storage(self, maxstorage):
        """Vary the storage capacity (recorded in MWh)."""
        self.maxstorage = maxstorage * 1000
        self.stored = 0

    def store(self, hr, power):
        """Store power.

        >>> b = Battery(polygons.wildcard, 400, 1000, rte=1.0)
        >>> b.store(hr=0, power=400)
        400
        >>> b.store(hr=1, power=700)
        400
        >>> b.store(hr=2, power=400)
        200.0
        """
        if self.last_run == hr:
            # Can't charge and discharge in the same hour.
            return 0
        power = min(power, self.capacity)
        energy = power * self.rte
        if self.stored + energy > self.maxstorage:
            power = (self.maxstorage - self.stored) / self.rte
            self.stored = self.maxstorage
        else:
            self.chargehours += 1
            self.stored += energy
        if power > 0:
            self.last_run = hr
        return power

    def step(self, hr, demand):
        """
        >>> dischg = range(18, 24)
        >>> b = Battery(polygons.wildcard, 400, 1000, dischg, rte=1.0)
        >>> b.stored = 400

        Cannot discharge outside of discharge hours.
        >>> b.step(hr=0, demand=200)
        (0, 0)

        Normal operation.
        >>> b.store(hr=0, power=400)
        400
        >>> b.step(hr=18, demand=200)
        (200, 0)

        Cannot generate and then store at the same time.
        >>> b.store(hr=18, power=200)
        0

        Cannot store and then generate at the same time.
        >>> b.store(hr=19, power=200)
        200
        >>> b.step(hr=19, demand=200)
        (0, 0)
        """
        if hr % 24 not in self.dischargeHours:
            return 0, 0

        if hr == self.last_run:
            # Can't charge and discharge in the same hour.
            return 0, 0

        power = min(self.stored, min(self.capacity, demand))
        self.series_power[hr] = power
        self.stored -= power
        if power > 0:
            self.runhours += 1
            self.last_run = hr
        return power, 0

    def reset(self):
        Generator.reset(self)
        self.runhours = 0
        self.chargehours = 0
        self.stored = 0
        self.last_run = None

    def capcost(self, costs):
        # capital cost of batteries has power and energy components
        # $400/kW and $400/kWh respectively
        power = 400 * self.capacity * 1000
        energy = 400 * self.maxstorage * 1000
        return power + energy

    def fixed_om_costs(self, costs):
        # fixed O&M of $28/kW/yr
        fom = 28 * self.capacity * 1000
        return fom

    def opcost_per_mwh(self, costs):
        # per-kWh costs for batteries are included in capital costs
        return 0

    def summary(self, context):
        return Generator.summary(self, context) + \
            ', ran %s hours' % locale.format('%d', self.runhours, grouping=True) + \
            ', charged %s hours' % locale.format('%d', self.chargehours, grouping=True) + \
            ', %s storage' % anyWh(self.maxstorage)


class Geothermal(Generator):

    """Geothermal power plant."""

    patch = Patch(facecolor='brown')
    csvfilename = None
    csvdata = None

    def __init__(self, polygon, capacity, filename, column, label):
        Generator.__init__(self, polygon, capacity, label)
        if Geothermal.csvfilename != filename:
            urlobj = urllib.request.urlopen(filename)
            Geothermal.csvdata = np.genfromtxt(urlobj, comments='#', delimiter=',')
            Geothermal.csvdata = np.maximum(0, Geothermal.csvdata)
            Geothermal.csvfilename = filename
        self.generation = Geothermal.csvdata[::, column]

    def step(self, hr, demand):
        """Step method for geothermal generators."""
        generation = self.generation[hr] * self.capacity
        power = min(generation, demand)
        self.series_power[hr] = power
        self.series_spilled[hr] = 0
        return power, 0


class Geothermal_HSA(Geothermal):

    """Hot sedimentary aquifer (HSA) geothermal model."""

    def __init__(self, polygon, capacity, filename, column, label='HSA geothermal'):
        Geothermal.__init__(self, polygon, capacity, filename, column, label)


class Geothermal_EGS(Geothermal):

    """Enhanced geothermal systems (EGS) geothermal model."""

    def __init__(self, polygon, capacity, filename, column, label='EGS geothermal'):
        Geothermal.__init__(self, polygon, capacity, filename, column, label)


class DemandResponse(Generator):

    """Load shedding generator."""

    patch = Patch(facecolor='white')

    def __init__(self, polygon, capacity, cost_per_mwh, label='demand-response'):
        Generator.__init__(self, polygon, capacity, label)
        self.setters = []
        self.runhours = 0
        self.maxresponse = 0
        self.cost_per_mwh = cost_per_mwh

    def step(self, hr, demand):
        """
        >>> dr = DemandResponse(polygons.wildcard, 500, 1500)
        >>> dr.step(hr=0, demand=200)
        (200, 0)
        >>> dr.runhours
        1
        """
        power = min(self.capacity, demand)
        self.maxresponse = max(self.maxresponse, power)
        self.series_power[hr] = power
        self.series_spilled[hr] = 0
        if power > 0:
            self.runhours += 1
        return power, 0

    def reset(self):
        Generator.reset(self)
        self.runhours = 0
        self.maxresponse = 0

    def opcost_per_mwh(self, costs):
        return self.cost_per_mwh

    def summary(self, context):
        return Generator.summary(self, context) + \
            ', max response %d MW' % self.maxresponse + \
            ', ran %s hours' % locale.format('%d', self.runhours, grouping=True)


class GreenPower(Generator):
    """GreenPower"""

    patch = Patch(facecolor='darkgreen')

    def __init__(self, polygon, capacity, label='GreenPower'):
        Generator.__init__(self, polygon, capacity, label)

    def step(self, hr, demand):
        """Step method for GreenPower."""
        power = min(self.capacity, demand)
        self.series_power[hr] = power
        return power, 0
