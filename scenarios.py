import heapq
import numpy as np

import nem

def supply_switch (label):
  "Return a callback function to set up a given scenario."
  if label == 're100':
      return re100
  elif label == 'ccgt':
      return ccgt
  elif label == 'ccgt-ccs':
      return ccgt_ccs
  elif label == 'coal-ccs':
      return coal_ccs
  elif label == 're100+batteries':
      return re100_batteries
  elif label == 'replacement':
      return replacement
  elif label == 're100+dsp':
      return re100_dsp
  elif label == 're+fossil':
      return re_plus_fossil
  elif label == 'theworks':
      return theworks
  else:
      raise ValueError ('unknown supply scenario %s' % label)
    
def _hydro ():
    "Return a list of existing hydroelectric generators"
    hydro1 = nem.generators.Hydro (nem.regions.tas, 2740, label=nem.regions.tas.id + ' hydro')
    hydro2 = nem.generators.Hydro (nem.regions.nsw, 1160, label=nem.regions.nsw.id + ' hydro')
    hydro3 = nem.generators.Hydro (nem.regions.vic,  960, label=nem.regions.vic.id + ' hydro')
    psh1 = nem.generators.PumpedHydro (nem.regions.qld, 500, 5000, label='QLD1 pumped-hydro')
    psh2 = nem.generators.PumpedHydro (nem.regions.nsw, 1740, 15000, label='NSW1 pumped-hydro')
    hydros = [hydro1, hydro2, hydro3, psh1, psh2]
    for h in hydros:
      h.setters = [] 
    return hydros

def replacement (context):
    "The current NEM fleet, more or less."
    coal = nem.generators.Black_Coal (nem.regions.nsw, 0)
    ocgt = nem.generators.OCGT (nem.regions.nsw, 0)
    context.generators = [coal] + _hydro () + [ocgt]

def ccgt (context):
    "All gas scenario"
    ccgt = nem.generators.CCGT (nem.regions.nsw, 0)
    ocgt = nem.generators.OCGT (nem.regions.nsw, 0)
    context.generators = [ccgt] + _hydro () + [ocgt]

def ccgt_ccs (context):
    "Gas CCS scenario"
    ccgt = nem.generators.CCGT_CCS (nem.regions.nsw, 0)
    ocgt = nem.generators.OCGT (nem.regions.nsw, 0)
    context.generators = [ccgt] + _hydro () + [ocgt]

def coal_ccs (context):
    "Coal CCS scenario"
    coal = nem.generators.Coal_CCS (nem.regions.nsw, 0)
    ocgt = nem.generators.OCGT (nem.regions.nsw, 0)
    context.generators = [coal] + _hydro () + [ocgt]

def re100 (context):
    "100% renewable electricity"
    pass

def re100_batteries (context):
    "Lots of renewables plus battery storage"
    nsw_battery = nem.generators.Battery (nem.regions.nsw, 0, 0)
    g = context.generators
    context.generators = g[0:9] + [nsw_battery] + g[9:]

def re_plus_fossil (context):
    "Mostly renewables with some fossil augmentation"
    ccgt = nem.generators.CCGT (nem.regions.nsw, 0)
    ocgt = nem.generators.OCGT (nem.regions.nsw, 0)
    g = context.generators
    context.generators = [ccgt] + g[:-5] + [ocgt]

def re100_dsp (context):
    "Mostly renewables with demand side participation"
    dr1 = nem.generators.DemandResponse (nem.regions.nsw, 2000, 300)
    dr2 = nem.generators.DemandResponse (nem.regions.nsw, 2000, 1000)
    dr3 = nem.generators.DemandResponse (nem.regions.nsw, 2000, 3000)
    g = context.generators
    context.generators = g + [dr1, dr2, dr3]

def theworks (context):
    "All technologies"
    coal = nem.generators.Black_Coal (nem.regions.nsw, 0)
    coal_ccs = nem.generators.Coal_CCS (nem.regions.nsw, 0)
    ccgt = nem.generators.CCGT (nem.regions.nsw, 0)
    ccgt_ccs = nem.generators.CCGT_CCS (nem.regions.nsw, 0)
    ocgt = nem.generators.OCGT (nem.regions.nsw, 0)
    g = context.generators
    context.generators = [coal, coal_ccs, ccgt, ccgt_ccs] + g[:-4] + [ocgt]

### Demand modifiers

def demand_switch (label):
  "Return a callback function to modify the demand."
  try:
    if label == 'unchanged':
      return unchanged

    elif label.startswith ('roll:'):
      # label form: "roll:X" rolls the load by X hours
      _, posns = label.split (':')
      posns = int (posns)
      return lambda context: roll_demand (context, posns)

    elif label.startswith ('scale:'):
      # label form: "scale:X" scales the load by X%
      _, factor = label.split (':')
      factor = 1 + int (factor) / 100.
      return lambda context: scale_demand (context, factor)
    
    elif label.startswith ('shift:'):
      # label form: "shift:N:H1:H2" load shifts N MW every day
      _, demand, h1, h2 = label.split (':')
      demand = int (demand)
      fromHour = int (h1)
      toHour = int (h2)
      if fromHour < 0 or fromHour >= 24 or toHour < 0 or toHour >= 24:
        raise ValueError
      return lambda context: shift_demand (context, demand, fromHour, toHour)
    
    elif label.startswith ('peaks:'):
      # label form: "peaks:N:X" adjust demand peaks over N megawatts
      # by X%
      _, power, factor = label.split (':')
      power = int (power)
      factor = 1 + int (factor) / 100.
      return lambda context: scale_peaks (context, power, factor)

    elif label.startswith ('npeaks:'):
      # label form: "npeaks:N:X" adjust top N demand peaks by X%
      _, topn, factor = label.split (':')
      topn = int (topn)
      factor = 1 + int (factor) / 100.
      return lambda context: scale_npeaks (context, topn, factor)
    else:
      raise ValueError

  except ValueError:
      raise ValueError ('invalid scenario: %s' % label)

def unchanged (context):
  pass

def roll_demand (context, posns):
  "Roll demand by posns hours"
  np.roll (context.demand, posns)

def scale_demand (context, factor):
  "Scale demand by factor%"
  context.demand *= factor

def shift_demand (context, demand, fromHour, toHour):
  "Move N MW of demand from fromHour to toHour"
  # Shed equally in each region for simplicity
  demand /= 5
  context.demand[::,fromHour::24] -= demand
  context.demand[::,toHour::24] += demand
  # Ensure load never goes negative
  context.demand = np.where (context.demand < 0, 0, context.demand)

def scale_peaks (context, power, factor):
  "Adjust demand peaks over N megawatts by X%"
  agg_demand = context.demand.sum (axis = 0)
  where = np.where (agg_demand > power)
  context.demand[::,where] *= factor

def scale_npeaks (context, topn, factor):
  "Adjust top N demand peaks by X%"
  agg_demand = context.demand.sum (axis = 0)
  top_demands = heapq.nlargest (topn, agg_demand)
  # A trick from:
  # http://docs.scipy.org/doc/numpy/reference/generated/numpy.where.html#numpy.where
  ix = np.in1d (agg_demand.ravel(), top_demands).reshape (agg_demand.shape)
  where = np.where (ix)
  context.demand[::,where] *= factor
