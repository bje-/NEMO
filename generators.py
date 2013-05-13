# -*- Python -*-
# Copyright (C) 2011, 2012 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import locale
import numpy as np
import simplesys

from matplotlib.patches import Patch

# Needed for currency formatting.
locale.setlocale  (locale.LC_ALL, '')

class Generator:
    def __init__ (self, region, capacity, label):
        "Base generator class"
        self.setters = [(self.set_capacity, 1000)]
        self.storage_p = False
        self.label = label
        self.capacity = capacity
        self.region = region

        # Time series of dispatched power and spills
        self.hourly_power = np.zeros (8760)
        self.hourly_spilled = np.zeros (8760)

    def capcost (self, costs):
        "Returns annual capital cost"
        return costs.capcost_per_kw_per_yr[self.__class__] * self.capacity * 1000

    def opcost (self, costs):
        "Returns annual operating and maintenance cost"
        return int (self.hourly_power.sum()) * costs.opcost_per_mwh[self.__class__]

    def reset (self):
        self.hourly_power.fill (0)
        self.hourly_spilled.fill (0)

    def summary (self, costs):
        s = 'supplied %.1f TWh' % (self.hourly_power.sum () / 1000000.)
        if self.hourly_spilled.sum () > 0:
            s += ', spilled %.1f TWh' % (self.hourly_spilled.sum () / 1000000.)
        if self.capcost(costs) > 0:
            s += ', capcost $%s' % locale.format ('%d', self.capcost(costs), grouping=True)
        if self.opcost(costs) > 0:
            s += ', opcost $%s' % locale.format ('%d', self.opcost(costs), grouping=True)
        return s

    def set_capacity (self, cap):
        self.capacity = cap

    def __str__ (self):
        return '%s (%s), %.1f GW' \
            % (self.label, self.region, self.capacity / 1000.)

    def __repr__ (self):
        return self.__str__ ()

class Wind(Generator):
    patch=Patch (facecolor='green') 
    def __init__ (self, region, capacity, h5file, label='wind'):
	Generator.__init__ (self, region, capacity, label)
	self.generation = h5file.root.aux.aemo2010.wind[::]
	# Normalise the generation (1555 MW installed in 2010)
	self.generation /= 1555.

    def step (self, hr, demand):
	generation = self.generation[hr] * self.capacity
	power = min (generation, demand)
	spilled = generation - power
        self.hourly_power[hr] = power
        self.hourly_spilled[hr] = spilled
	return power, spilled

class SAMWind(Wind):
    patch=Patch (facecolor='lightgreen')
    def __init__ (self, region, capacity, filename, modelcapacity, label='wind'):
	Generator.__init__ (self, region, capacity, label)
        self.generation = np.genfromtxt (filename, delimiter=',', skip_header=1)
	# SAM data is in kWh
	self.generation /= 1000.
	# Normalise into MW
	self.generation /= modelcapacity 

class CST(Generator):
    patch=Patch (facecolor='yellow')
    def __init__ (self, region, capacity, solarmult, tes, filename, locn, label='CST', dispHour=0):
        Generator.__init__ (self, region, capacity, label)
        self.turbine_effcy = 0.40
        self.capacity_th = capacity / self.turbine_effcy
        self.solarmult = solarmult
        self.tes = tes
        self.collectorseries = np.genfromtxt (filename, delimiter=',', skip_header=1, usecols=(locn))
        self.s = simplesys.Context (ep=0.2, qf=0.1, sl=0.03, sm=self.capacity_th*tes)
        self.dispHour = dispHour
        self.still_running_p = False

        # The collector data is for a field with SM=1.
        # Then we can scale it here to anything we like.
        self.s.COLLECTOR = self.collectorseries * self.capacity * self.solarmult

        self.hourly_dumped = np.zeros (8760)
        self.hourly_stored = np.zeros (8760)
        self.hourly_storage_level = np.zeros (8760)
        self.storage_p = True

    def step (self, hr, demand):
        demand_th = demand / self.turbine_effcy
        Qload = min (demand_th, self.capacity_th)
        if hr % 24 > 7 and hr % 24 < self.dispHour:
            Qload = 0
        elif not self.still_running_p and hr % 24 < self.dispHour:
            Qload = 0
        result = self.s.nexthour (Qload)
        # energy served = load minus auxiliary energy
        served = (result['QL'] - result['QA']) * self.turbine_effcy
        self.hourly_power[hr] = served
        self.hourly_dumped[hr] = result['QD']
        self.hourly_storage_level[hr] = result['ES']
        self.hourly_spilled[hr] = 0

        if served == 0:
            self.still_running_p = False
        elif served > 0:
            self.still_running_p = True

        return served, 0

    def store (self, hr, power):
        "Accept spilled energy by heating the CST storage (1.0 efficiency)."
        # Only accept some energy if storage is near full.
        rejected = self.s.storageInput (power)
        power -= rejected
        self.hourly_stored[hr] = power
        return power

    def set_capacity (self, cap):
        self.capacity = cap
        self.capacity_th = cap / self.turbine_effcy
        self.s.COLLECTOR = self.collectorseries * self.capacity * self.solarmult
        self.s.SM = self.capacity_th * self.tes
       
    def reset (self):
        Generator.reset (self)
        self.hourly_dumped.fill (0)
        self.hourly_stored.fill (0)
        self.hourly_storage_level.fill (0)
        self.s.reset ()

    def capcost (self, costs):
        "Calculate the capital cost based on the solar field and storage size"
        fom = costs.fixed_om_costs[self.__class__]
        af = costs.annuityf
        anncost = costs.capcost_per_kw_per_yr[self.__class__]

        # Reverse engineer the capital cost
        capcost = (anncost - fom) * af
        cost = capcost * 0.57
        # Solar field is 33% of costs
        cost += capcost * 0.33 * (self.solarmult / 2.)
        # Storage is 10% of costs
        cost += capcost * 0.10 * (self.tes / 6.)

        # Put back in annualised terms
        anncost = cost / af + fom
        return anncost

    def summary (self, costs):
	return Generator.summary (self, costs) + ', stored %d MWh' % self.hourly_stored.sum () + \
            ', dumped %d MWh-t' % self.hourly_dumped.sum () + \
            ', solar mult %.2f' % self.solarmult + ', %dh storage' % self.tes

class PV(Generator):
    patch=Patch (facecolor='blue')
    def __init__ (self, region, capacity, table, filename, locn, label='PV'):
        Generator.__init__ (self, region, capacity, label)
        # Normalised to 1 MW
        self.generation = np.genfromtxt (filename, delimiter=',', skip_header=1)
        self.generation = np.maximum (0, self.generation)
        self.generation = self.generation[::,locn]
        self.generation /= 1000.

    def step (self, hr, demand):
        generation = self.generation[hr] * self.capacity
        power = min (generation, demand)
        spilled = generation - power
        self.hourly_power[hr] = power
        self.hourly_spilled[hr] = spilled
        return power, spilled

class Fuelled(Generator):
    "The class of generators that consume fuel."
    def __init__ (self, region, capacity, label):
        Generator.__init__ (self, region, capacity, label)
        self.runhours = 0

    def reset (self):
        Generator.reset (self)
        self.runhours = 0
            
    def step (self, hr, demand):
        power = min (self.capacity, demand)
        if power > 0:
            self.runhours += 1
        self.hourly_power[hr] = power
        return power, 0

    def summary (self, costs):
        return Generator.summary (self, costs) + ', ran %s hours' \
            % locale.format ('%d', self.runhours, grouping=True)

class Hydro(Fuelled):
    patch=Patch (facecolor='lightskyblue')
    def __init__ (self, region, capacity, label='hydro'):
        Fuelled.__init__ (self, region, capacity, label)

class PumpedHydro(Hydro):
    patch=Patch (facecolor='powderblue')
    def __init__ (self, region, capacity, maxstorage, rte=0.8, label='pumped-hydro'):
        Fuelled.__init__ (self, region, capacity, label)
        self.maxstorage = maxstorage
        # Half the water starts in the lower reservoir.
        self.stored = self.maxstorage * .5
        self.rte = rte
        self.storage_p = True
        self.last_run = None
 
    def store (self, hr, power):
        "Pump water uphill for one hour."
        if self.last_run == hr:
            # Can't pump in the same hour as the turbine.
            return 0
        energy = power * self.rte
        if self.stored + energy > self.maxstorage:
            power = (self.maxstorage - self.stored) / self.rte
            self.stored = self.maxstorage
        else:
            self.stored += energy
        return power

    def step (self, hr, demand):
        power = min (self.stored, min (self.capacity, demand))
        self.hourly_power[hr] = power
        self.stored -= power
        if power > 0:
            self.runhours += 1
            self.last_run = hr
        return power, 0

    def reset (self):
        Fuelled.reset (self)
        self.stored = self.maxstorage * .5
        self.last_run = None

class Biofuel(Fuelled):
    patch=Patch (facecolor='wheat')
    def __init__ (self, region, capacity, label='biofuel'):
        Fuelled.__init__ (self, region, capacity, label)
        self.prev = 0

    def step (self, hr, demand):
        power = min (self.capacity, demand)
        self.hourly_power[hr] = power
        # calculate delta power
        delta = abs (self.prev - power)
        self.prev = power
        if power > 0:
            self.runhours += 1
        return power, 0

    def reset (self):
        Fuelled.reset (self)

class Fossil(Fuelled):
    patch=Patch (facecolor='brown')
    def __init__ (self, region, capacity, intensity, label='fossil'):
        # Greenhouse gas intensity in tonnes per MWh
        Fuelled.__init__ (self, region, capacity, label)
        self.intensity = intensity

    def summary (self, costs):
        return Fuelled.summary (self, costs) + ', %.1f Mt CO2' \
            % (self.hourly_power.sum () * self.intensity / 1000000.)

class Black_Coal(Fossil):
    patch=Patch (facecolor='black')
    def __init__ (self, region, capacity, intensity=0.773, label='coal'):
        Fossil.__init__ (self, region, capacity, intensity, label)

    def opcost (self, costs):
        vom = costs.opcost_per_mwh[self.__class__]
        fuel_cost = costs.coal_price_per_gj * 8.57
	total_opcost = vom + fuel_cost + self.intensity * costs.carbon
        return self.hourly_power.sum () * total_opcost

class OCGT(Fossil):
    patch=Patch (facecolor='brown')
    def __init__ (self, region, capacity, intensity=0.7, label='OCGT'):
        Fossil.__init__ (self, region, capacity, intensity, label)

    def opcost (self, costs):
        vom = costs.opcost_per_mwh[self.__class__]
        fuel_cost = costs.gas_price_per_gj * 11.61
	total_opcost = vom + fuel_cost + self.intensity * costs.carbon
        return self.hourly_power.sum () * total_opcost

class CCGT(Fossil):
    patch=Patch (facecolor='brown')
    def __init__ (self, region, capacity, intensity=0.4, label='CCGT'):
        Fossil.__init__ (self, region, capacity, intensity, label)

    def opcost (self, costs):
        vom = costs.opcost_per_mwh[self.__class__] 
        fuel_cost = costs.gas_price_per_gj * 6.92
	total_opcost = vom + fuel_cost + self.intensity * costs.carbon
        return self.hourly_power.sum () * total_opcost

class CCS(Fossil):
    def __init__ (self, region, capacity, intensity, capture, label='CCS'):
        Fossil.__init__ (self, region, capacity, intensity, label)
        # capture fraction ranges from 0 to 1
        self.capture = capture

    def summary (self, costs):
        return Fossil.summary (self, costs) + ', %.1f Mt captured' \
            % (self.hourly_power.sum () * self.intensity / 1000000. * self.capture)

class Coal_CCS(CCS):
    def __init__ (self, region, capacity, intensity=0.8, capture=0.85, label='Coal-CCS'):
        CCS.__init__ (self, region, capacity, intensity, capture, label)

    def opcost (self, costs):
        vom = costs.opcost_per_mwh[self.__class__]
        # thermal efficiency 31.4% (AETA 2012)
        fuel_cost = costs.coal_price_per_gj * (3.6 / 0.314)
	# t CO2/MWh
	emissions_rate = 0.103
	total_opcost = vom + fuel_cost + \
            (emissions_rate * costs.carbon) + \
            (self.intensity * self.capture * costs.ccs_storage_per_t)
	return self.hourly_power.sum () * total_opcost

class CCGT_CCS(CCS):
    def __init__ (self, region, capacity, intensity=0.4, capture=0.85, label='CCGT-CCS'):
        CCS.__init__ (self, region, capacity, intensity, capture, label)

    def opcost (self, costs):
        vom = costs.opcost_per_mwh[self.__class__]
        # thermal efficiency 43.1% (AETA 2012)
        fuel_cost = costs.gas_price_per_gj * (3.6 / 0.431)
	total_opcost = vom + fuel_cost + \
            (self.intensity * (1-self.capture) * costs.carbon) + \
            (self.intensity * self.capture * costs.ccs_storage_per_t)
	return self.hourly_power.sum () * total_opcost

class Battery(Generator):
    patch=Patch (facecolor='grey')
    def __init__ (self, region, capacity, maxstorage, rte=0.95, label='battery'):
        Generator.__init__ (self, region, capacity, label)
        self.setters = [(self.set_capacity, 1000), (self.set_storage, 1000000)]
        self.maxstorage = maxstorage
        self.stored = 0
        self.rte = rte
        self.storage_p = True
        self.runhours = 0
        self.chargehours = 0

    def set_storage (self, maxstorage):
        self.maxstorage = maxstorage
        
    def store (self, hr, power):
        "Charge for one hour."
        energy = power * self.rte
        if self.stored + energy > self.maxstorage:
            power = (self.maxstorage - self.stored) / self.rte
            self.stored = self.maxstorage
        else:
            self.chargehours += 1
            self.stored += energy
        return power

    def step (self, hr, demand):
        power = min (self.stored, min (self.capacity, demand))
        self.hourly_power[hr] = power
        self.stored -= power
        if power > 0:
            self.runhours += 1
        return power, 0

    def reset (self):
        Generator.reset (self)
        self.runhours = 0
        self.chargehours = 0
        self.stored = 0

    def capcost (self, costs):
        # capital cost of batteries has power and energy components
        # $400/kW and $400/kWh respectively
        power = 400 * self.capacity * 1000
        energy = 400 * self.maxstorage * 1000
        # fixed O&M of $28/kW/yr
        fom = 28 * self.capacity * 1000
        return (power + energy) / costs.annuityf + fom

    def opcost (self, costs):
        # per-kWh costs for batteries are included in capital costs
        return 0

    def summary (self, costs):
        return Generator.summary (self, costs) + \
            ', ran %s hours' % locale.format ('%d', self.runhours, grouping=True) + \
            ', charged %s hours' % locale.format ('%d', self.chargehours, grouping=True) + \
            ', %.2f GWh storage' % (self.maxstorage / 1000.)
