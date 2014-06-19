# -*- Python -*-
#
# A script for Mark that tries out a few alternative wind sites.
# Copyright (C) 2012 Ben Elliston

import nem
import wind
import regions

from nem import twh
from generators import Generator, Wind, SAMWind
import generators

from pylab import *


class SingleWindFarm(Wind):
    patch = generators.Patch(facecolor='green')

    def __init__(self, region, capacity, duid, rated, label='wind'):
        Generator.__init__(self, region, capacity, label)
        self.generation = wind.generation(duid, interval=60)
        # Normalise the generation
        self.generation /= rated


def print_stats(c):
  bioenergy = 0
  runhours = 0
  wind_energy = 0
  for g in c.generators:
      if g.__class__ == generators.Biofuel:
          bioenergy += g.hourly_power.sum()
          runhours += g.runhours
      elif g.__class__ == Wind or g.__class__ == SAMWind or g.__class__ == SingleWindFarm:
          wind_energy += g.hourly_power.sum()

  print '%.2f, %.2f, %d, %.1f, %.3f, %d' % \
        (wind_energy / twh, bioenergy / twh, runhours, c.spilled_energy / twh,
         c.unserved_percent, c.unserved_hours)

# A baseline run to calculate avg CF for the wind farms.
print 'baseline'
c = nem.Context()
nem.run(c)
print c
for g in c.generators[0:4]:
    print g, g.summary()
total_wind_energy = 0
total_wind_capacity = 0
for g in c.generators:
  if g.__class__ == Wind:
    total_wind_energy += g.hourly_power.sum()
    total_wind_capacity += g.capacity
avg_cap_factor = (total_wind_energy / float(nem.hours)) / total_wind_capacity

# Calculate a reduction in capacity to reduce energy by 5 TWh.
cap = 5 * twh / (avg_cap_factor * nem.hours)

f = open('/data/windfarm.info.csv')
sites = []
for line in f:
    #ID,Name,Region,Latitude,Longitude,Capacity (MW),Capacity Factor* (%)
    if line[0] == '#':
        continue
    fields = line.split(',')
    if fields[0] == 'wpwf':
        break
    if fields[0] == 'gunning1' or fields[0] == 'woodlwn1' or fields[0] == 'bluff1':
        continue
    wf = SingleWindFarm(regions.nsw, 1, fields[0].upper(), float(fields[5]), label=fields[1])
    # print wf
    c.generators = [wf]
    nem.run(c)
    # compute capacity factor
    wf.cf = (wf.hourly_power.sum() / float(nem.hours)) / wf.capacity
    sites.append(wf)
f.close()

kennedy = SAMWind(regions.qld, 1, '/data/kennedy.data.csv', 57.6, label='Kennedy wind')
c.generators = [kennedy]
nem.run(c)
kennedy.cf = (kennedy.hourly_power.sum() / float(nem.hours)) / kennedy.capacity

cooranga = SAMWind(regions.qld, 1, '/data/cooranga.data.csv', 57.6, label='Cooranga wind')
c.generators = [cooranga]
nem.run(c)
cooranga.cf = (cooranga.hourly_power.sum() / float(nem.hours)) / cooranga.capacity

capital = SingleWindFarm(regions.nsw, 1, 'CAPTL_WF', 140, label='Capital')
c.generators = [capital]
nem.run(c)
capital.cf = (capital.hourly_power.sum() / float(nem.hours)) / capital.capacity

sites = [kennedy, cooranga, capital]
for windfarm in sites:
    for quantum in range(25):
        oldcap = quantum * twh / (avg_cap_factor * nem.hours)
        capacity = total_wind_capacity - oldcap
        newcap = quantum * twh / (windfarm.cf * nem.hours)
        windfarm.set_capacity(newcap)
        newWind = [windfarm, Wind(regions.sa, capacity, nem.h5file, label='existing wind')]
        c = nem.Context()
        c.generators = newWind + c.generators[4:]
        nem.run(c)
        print windfarm.label, ', %d, %.1f, %.1f, ' % (quantum, c.generators[0].capacity, c.generators[1].capacity),
        print_stats(c)
