# Copyright (C) 2011, 2012, 2013, 2014 Ben Elliston
# Copyright (C) 2014 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Simulated generators for the NEMO framework."""
import locale

import numpy as np
from matplotlib.patches import Patch

import consts


# Needed for currency formatting.
locale.setlocale(locale.LC_ALL, '')


class Generator:

    """Base generator class."""

    def __init__(self, region, capacity, label):
        """Base class constructor.

        Arguments: installed region, installed capacity, descriptive label.
        """
        self.setters = [(self.set_capacity, 0, 40)]
        self.storage_p = False
        self.label = label
        self.capacity = capacity
        self.region = region

        # Is the generator a rotating machine?
        self.non_synchronous_p = False

        # Time series of dispatched power and spills
        self.hourly_power = {}
        self.hourly_spilled = {}

    def capcost(self, costs):
        """Return the annual capital cost."""
        return costs.capcost_per_kw_per_yr[self.__class__] * self.capacity * 1000

    def opcost(self, costs):
        """Return the annual operating and maintenance cost."""
        return sum(self.hourly_power.values()) * self.opcost_per_mwh(costs)

    def opcost_per_mwh(self, costs):
        return costs.opcost_per_mwh[self.__class__]

    def reset(self):
        """Reset the generator."""
        self.hourly_power.clear()
        self.hourly_spilled.clear()

    def summary(self, costs):
        """Return a summary of the generator activity."""
        s = 'supplied %.4g TWh' % (sum(self.hourly_power.values()) / consts.twh)
        if sum(self.hourly_spilled.values()) > 0:
            s += ', spilled %.1f TWh' % (sum(self.hourly_spilled.values()) / consts.twh)
        if self.capcost(costs) > 0:
            s += ', capcost $%s' % locale.format('%d', self.capcost(costs), grouping=True)
        if self.opcost(costs) > 0:
            s += ', opcost $%s' % locale.format('%d', self.opcost(costs), grouping=True)
        return s

    def set_capacity(self, cap):
        """Change the capacity of the generator to 'cap' GW."""
        self.capacity = cap * 1000

    def __str__(self):
        """A short string representation of the generator."""
        return '%s (%s), %.2f GW' \
            % (self.label, self.region, self.capacity / 1000.)

    def __repr__(self):
        """A representation of the generator."""
        return self.__str__()


class Wind(Generator):

    """Wind power."""

    patch = Patch(facecolor='green')
    csvfilename = None
    csvdata = None

    def __init__(self, region, capacity, filename, column, delimiter=None, build_limit=None, label='wind'):
        Generator.__init__(self, region, capacity, label)
        if build_limit is not None:
            # Override default capacity limit with build_limit
            _, _, limit = self.setters[0]
            self.setters = [(self.set_capacity, 0, min(build_limit, limit))]
        self.non_synchronous_p = True
        if Wind.csvfilename != filename:
            # Optimisation:
            # Only if the filename changes do we invoke genfromtxt.
            Wind.csvdata = np.genfromtxt(filename, comments='#', delimiter=delimiter)
            Wind.csvdata = np.maximum(0, Wind.csvdata)
            Wind.csvfilename = filename
        self.generation = Wind.csvdata[::, column]

    def step(self, hr, demand):
        generation = self.generation[hr] * self.capacity
        power = min(generation, demand)
        spilled = generation - power
        self.hourly_power[hr] = power
        self.hourly_spilled[hr] = spilled
        return power, spilled


class PV(Generator):

    """Solar photovoltaic (PV) model."""

    patch = Patch(facecolor='darkblue')
    csvfilename = None
    csvdata = None

    def __init__(self, region, capacity, filename, column, build_limit=None, label='PV'):
        Generator.__init__(self, region, capacity, label)
        self.non_synchronous_p = True
        if build_limit is not None:
            # Override default capacity limit with build_limit
            _, _, limit = self.setters[0]
            self.setters = [(self.set_capacity, 0, min(build_limit, limit))]
        if PV.csvfilename != filename:
            PV.csvdata = np.genfromtxt(filename, comments='#', delimiter=',')
            PV.csvdata = np.maximum(0, PV.csvdata)
            PV.csvfilename = filename
        self.generation = PV.csvdata[::, column]

    def step(self, hr, demand):
        generation = self.generation[hr] * self.capacity
        power = min(generation, demand)
        spilled = generation - power
        self.hourly_power[hr] = power
        self.hourly_spilled[hr] = spilled
        return power, spilled


class PV1Axis(PV):
    """Single-axis tracking PV."""

    def __init__(self, region, capacity, filename, column, build_limit=None, label='PV 1-axis'):
        PV.__init__(self, region, capacity, filename, column, build_limit, label)


class CST(Generator):

    """Solar thermal (CST) model."""

    csvfilename = None
    csvdata = None

    def __init__(self, region, capacity, sm, shours, filename, column, build_limit=None, label='CST'):
        Generator.__init__(self, region, capacity, label)
        if build_limit is not None:
            # Override default capacity limit with build_limit
            _, _, limit = self.setters[0]
            self.setters = [(self.set_capacity, 0, min(build_limit, limit))]
        self.sm = sm
        if CST.csvfilename != filename:
            CST.csvdata = np.genfromtxt(filename, comments='#', delimiter=',')
            CST.csvfilename = filename
        self.generation = CST.csvdata[::, column]
        self.shours = shours
        self.maxstorage = capacity * shours
        self.stored = 0.5 * self.maxstorage

    def set_capacity(self, cap):
        Generator.set_capacity(self, cap)
        self.maxstorage = cap * 1000 * self.shours

    def step(self, hr, demand):
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
        self.hourly_power[hr] = generation
        self.hourly_spilled[hr] = 0

        if generation > demand:
            # This can happen due to rounding errors.
            generation = demand
        return generation, 0

    def reset(self):
        Generator.reset(self)
        self.stored = 0.5 * self.maxstorage

    def summary(self, costs):
        return Generator.summary(self, costs) + \
            ', solar mult %.2f' % self.sm + ', %dh storage' % self.shours


class ParabolicTrough(CST):

    """Parabolic trough CST generator.

    This stub class allows differentiated CST costs in costs.py.
    """
    patch = Patch(facecolor='yellow')

    def __init__(self, region, capacity, sm, shours, filename, column, build_limit=None, label='CST'):
        CST.__init__(self, region, capacity, sm, shours, filename, column, build_limit, label)


class CentralReceiver(CST):

    """Central receiver CST generator.

    This stub class allows differentiated CST costs in costs.py.
    """
    patch = Patch(facecolor='orange')

    def __init__(self, region, capacity, sm, shours, filename, column, build_limit=None, label='CST'):
        CST.__init__(self, region, capacity, sm, shours, filename, column, build_limit, label)


class Fuelled(Generator):

    """The class of generators that consume fuel."""

    def __init__(self, region, capacity, label):
        Generator.__init__(self, region, capacity, label)
        self.runhours = 0

    def reset(self):
        Generator.reset(self)
        self.runhours = 0

    def step(self, hr, demand):
        power = min(self.capacity, demand)
        if power > 0:
            self.runhours += 1
        self.hourly_power[hr] = power
        return power, 0

    def summary(self, costs):
        return Generator.summary(self, costs) + ', ran %s hours' \
            % locale.format('%d', self.runhours, grouping=True)


class Hydro(Fuelled):

    """Hydro power stations."""

    patch = Patch(facecolor='lightskyblue')

    def __init__(self, region, capacity, label='hydro'):
        Fuelled.__init__(self, region, capacity, label)
        # capacity is in MW, but build limit is in GW
        self.setters = [(self.set_capacity, 0, capacity / 1000.)]


class PumpedHydro(Hydro):

    """Pumped storage hydro (PSH) model."""

    patch = Patch(facecolor='powderblue')

    def __init__(self, region, capacity, maxstorage, rte=0.8, label='pumped-hydro'):
        Hydro.__init__(self, region, capacity, label)
        self.maxstorage = maxstorage
        # Half the water starts in the lower reservoir.
        self.stored = self.maxstorage * .5
        self.rte = rte
        self.storage_p = True
        self.last_run = None

    def store(self, hr, power):
        """Pump water uphill for one hour.

        >>> import regions
        >>> psh = PumpedHydro(regions.nsw, 100, 1000)
        >>> psh.step(hr=0, demand=100)
        (100, 0)

        Cannot pump and generate at the same time.
        >>> psh.store(hr=0, power=100)
        0
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
        return power

    def step(self, hr, demand):
        power = min(self.stored, min(self.capacity, demand))
        self.hourly_power[hr] = power
        self.stored -= power
        if power > 0:
            self.runhours += 1
            self.last_run = hr
        return power, 0

    def reset(self):
        Fuelled.reset(self)
        self.stored = self.maxstorage * .5
        self.last_run = None


class Biofuel(Fuelled):

    """Model of open cycle gas turbines burning biofuel."""

    patch = Patch(facecolor='wheat')

    def __init__(self, region, capacity, label='biofuel'):
        Fuelled.__init__(self, region, capacity, label)

    def step(self, hr, demand):
        power = min(self.capacity, demand)
        self.hourly_power[hr] = power
        if power > 0:
            self.runhours += 1
        return power, 0

    def opcost_per_mwh(self, costs):
        vom = costs.opcost_per_mwh[self.__class__]
        fuel_cost = costs.bioenergy_price_per_gj * (3.6 / .31)  # 31% heat rate
        return vom + fuel_cost

    def reset(self):
        Fuelled.reset(self)


class Fossil(Fuelled):

    """Base class for GHG emitting power stations."""

    patch = Patch(facecolor='brown')

    def __init__(self, region, capacity, intensity, label='fossil'):
        # Greenhouse gas intensity in tonnes per MWh
        Fuelled.__init__(self, region, capacity, label)
        self.intensity = intensity

    def summary(self, costs):
        return Fuelled.summary(self, costs) + ', %.1f Mt CO2' \
            % (sum(self.hourly_power.values()) * self.intensity / 1000000.)


class Black_Coal(Fossil):

    """Black coal power stations with no CCS."""

    patch = Patch(facecolor='black')

    def __init__(self, region, capacity, intensity=0.773, label='coal'):
        Fossil.__init__(self, region, capacity, intensity, label)

    def opcost_per_mwh(self, costs):
        vom = costs.opcost_per_mwh[self.__class__]
        fuel_cost = costs.coal_price_per_gj * 8.57
        total_opcost = vom + fuel_cost + self.intensity * costs.carbon
        return total_opcost


class OCGT(Fossil):

    """Open cycle gas turbine (OCGT) model."""

    patch = Patch(facecolor='brown')

    def __init__(self, region, capacity, intensity=0.7, label='OCGT'):
        Fossil.__init__(self, region, capacity, intensity, label)

    def opcost_per_mwh(self, costs):
        vom = costs.opcost_per_mwh[self.__class__]
        fuel_cost = costs.gas_price_per_gj * 11.61
        total_opcost = vom + fuel_cost + self.intensity * costs.carbon
        return total_opcost


class CCGT(Fossil):

    """Combined cycle gas turbine (CCGT) model."""

    patch = Patch(facecolor='brown')

    def __init__(self, region, capacity, intensity=0.4, label='CCGT'):
        Fossil.__init__(self, region, capacity, intensity, label)

    def opcost_per_mwh(self, costs):
        vom = costs.opcost_per_mwh[self.__class__]
        fuel_cost = costs.gas_price_per_gj * 6.92
        total_opcost = vom + fuel_cost + self.intensity * costs.carbon
        return total_opcost


class CCS(Fossil):

    """Base class of carbon capture and storage (CCS)."""

    def __init__(self, region, capacity, intensity, capture, label='CCS'):
        Fossil.__init__(self, region, capacity, intensity, label)
        # capture fraction ranges from 0 to 1
        self.capture = capture

    def summary(self, costs):
        return Fossil.summary(self, costs) + ', %.1f Mt captured' \
            % (sum(self.hourly_power.values()) * self.intensity / 1000000. * self.capture)


class Coal_CCS(CCS):

    """Coal with CCS."""

    def __init__(self, region, capacity, intensity=0.8, capture=0.85, label='Coal-CCS'):
        CCS.__init__(self, region, capacity, intensity, capture, label)

    def opcost_per_mwh(self, costs):
        vom = costs.opcost_per_mwh[self.__class__]
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

    def __init__(self, region, capacity, intensity=0.4, capture=0.85, label='CCGT-CCS'):
        CCS.__init__(self, region, capacity, intensity, capture, label)

    def opcost_per_mwh(self, costs):
        vom = costs.opcost_per_mwh[self.__class__]
        # thermal efficiency 43.1% (AETA 2012)
        fuel_cost = costs.gas_price_per_gj * (3.6 / 0.431)
        total_opcost = vom + fuel_cost + \
            (self.intensity * (1 - self.capture) * costs.carbon) + \
            (self.intensity * self.capture * costs.ccs_storage_per_t)
        return total_opcost


class Battery(Generator):

    """Battery storage (of any type)."""

    patch = Patch(facecolor='grey')

    def __init__(self, region, capacity, maxstorage, rte=0.95, label='battery'):
        Generator.__init__(self, region, capacity, label)
        self.non_synchronous_p = True
        self.setters += [(self.set_storage, 0, 10000)]
        self.maxstorage = maxstorage
        self.stored = 0
        self.rte = rte
        self.storage_p = True
        self.runhours = 0
        self.chargehours = 0

    def set_storage(self, maxstorage):
        """Vary the storage capacity (GWh)."""
        self.maxstorage = maxstorage * 1000

    # pylint: disable=unused-argument
    def store(self, hr, power):
        """Store power.

        >>> import regions
        >>> b = Battery(regions.nsw, 400, 1000, rte=1.0)
        >>> b.store(hr=0, power=400)
        400
        >>> b.store(hr=0, power=700)
        400
        """
        power = min(power, self.capacity)
        energy = power * self.rte
        if self.stored + energy > self.maxstorage:
            power = (self.maxstorage - self.stored) / self.rte
            self.stored = self.maxstorage
        else:
            self.chargehours += 1
            self.stored += energy
        return int(power)

    def step(self, hr, demand):
        """
        >>> import regions
        >>> b = Battery(regions.nsw, 400, 1000, rte=1.0)
        >>> b.step(hr=0, demand=200)
        (0, 0)
        >>> b.store(hr=0, power=400)
        400
        >>> b.step(hr=2, demand=200)
        (200, 0)
        """
        power = min(self.stored, min(self.capacity, demand))
        self.hourly_power[hr] = power
        self.stored -= power
        if power > 0:
            self.runhours += 1
        return power, 0

    def reset(self):
        Generator.reset(self)
        self.runhours = 0
        self.chargehours = 0
        self.stored = 0

    def capcost(self, costs):
        # capital cost of batteries has power and energy components
        # $400/kW and $400/kWh respectively
        power = 400 * self.capacity * 1000
        energy = 400 * self.maxstorage * 1000
        # fixed O&M of $28/kW/yr
        fom = 28 * self.capacity * 1000
        return (power + energy) / costs.annuityf + fom

    def opcost_per_mwh(self, costs):
        # per-kWh costs for batteries are included in capital costs
        return 0

    def summary(self, costs):
        return Generator.summary(self, costs) + \
            ', ran %s hours' % locale.format('%d', self.runhours, grouping=True) + \
            ', charged %s hours' % locale.format('%d', self.chargehours, grouping=True) + \
            ', %.2f GWh storage' % (self.maxstorage / 1000.)


class Geothermal(Generator):

    """Hot dry rocks geothermal power plant."""

    patch = Patch(facecolor='brown')
    csvfilename = None
    csvdata = None

    def __init__(self, region, capacity, filename, column, label):
        Generator.__init__(self, region, capacity, label)
        if Geothermal.csvfilename != filename:
            Geothermal.csvdata = np.genfromtxt(filename, comments='#', delimiter=',')
            Geothermal.csvdata = np.maximum(0, Geothermal.csvdata)
            Geothermal.csvfilename = filename
        self.generation = Geothermal.csvdata[::, column]

    def step(self, hr, demand):
        generation = self.generation[hr] * self.capacity
        power = min(generation, demand)
        self.hourly_power[hr] = power
        self.hourly_spilled[hr] = 0
        return power, 0


class Geothermal_HSA(Geothermal):

    """Hot sedimentary aquifer (HSA) geothermal model."""

    def __init__(self, region, capacity, filename, column, label='HSA'):
        Geothermal.__init__(self, region, capacity, filename, column, label)


class Geothermal_EGS(Geothermal):

    """Enhanced geothermal systems (EGS) geothermal model."""

    def __init__(self, region, capacity, filename, column, label='EGS'):
        Geothermal.__init__(self, region, capacity, filename, column, label)


class DemandResponse(Generator):

    """Load shedding generator."""

    patch = Patch(facecolor='white')

    # pylint: disable=unused-argument
    def __init__(self, region, capacity, cost_per_mwh, label='demand-response'):
        Generator.__init__(self, region, capacity, label)
        self.setters = []
        self.runhours = 0
        self.maxresponse = 0
        self.cost_per_mwh = cost_per_mwh

    def step(self, hr, demand):
        """
        >>> import regions
        >>> dr = DemandResponse(regions.nsw, 500, 1500)
        >>> dr.step(hr=0, demand=200)
        (200, 0)
        >>> dr.runhours
        1
        """
        power = min(self.capacity, demand)
        self.maxresponse = max(self.maxresponse, power)
        self.hourly_power[hr] = power
        self.hourly_spilled[hr] = 0
        if power > 0:
            self.runhours += 1
        return power, 0

    def reset(self):
        Generator.reset(self)
        self.runhours = 0
        self.maxresponse = 0

    def opcost_per_mwh(self, costs):
        return self.cost_per_mwh

    def summary(self, costs):
        return Generator.summary(self, costs) + \
            ', max response %d MW' % self.maxresponse + \
            ', ran %s hours' % locale.format('%d', self.runhours, grouping=True)
