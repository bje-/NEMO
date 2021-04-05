# Copyright (C) 2012, 2013, 2014 Ben Elliston
# Copyright (C) 2014, 2015, 2016 The University of New South Wales
# Copyright (C) 2016 IT Power (Australia)
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Supply and demand side scenarios."""
import numpy as np
import pandas as pd

from nemo import configfile
from nemo import generators
from nemo import polygons
from nemo.polygons import wildcard
from nemo import regions
from nemo.generators import CentralReceiver, Wind, PV1Axis, Hydro, PumpedHydro, Biofuel


def _demand_response():
    """
    Return a list of DR 'generators'.

    >>> dr = _demand_response()
    >>> len(dr)
    3
    """
    dr1 = generators.DemandResponse(wildcard, 1000, 100, "DR100")
    dr2 = generators.DemandResponse(wildcard, 1000, 500, "DR500")
    dr3 = generators.DemandResponse(wildcard, 1000, 1000, "DR1000")
    return [dr1, dr2, dr3]


def _hydro():
    """
    Return a list of existing hydroelectric generators.

    >>> h = _hydro()
    >>> len(h)
    12
    """
    hydro24 = generators.Hydro(24, 42.5, label='poly 24 hydro')
    hydro31 = generators.Hydro(31, 43, label='poly 31 hydro')
    hydro35 = generators.Hydro(35, 71, label='poly 35 hydro')
    hydro36 = generators.Hydro(36, 2513.9, label='poly 36 hydro')
    hydro38 = generators.Hydro(38, 450, label='poly 38 hydro')
    hydro39 = generators.Hydro(39, 13.8, label='poly 39 hydro')
    hydro40 = generators.Hydro(40, 586.6, label='poly 40 hydro')
    hydro41 = generators.Hydro(41, 280, label='poly 41 hydro')
    hydro42 = generators.Hydro(42, 590.4, label='poly 42 hydro')
    hydro43 = generators.Hydro(43, 462.5, label='poly 43 hydro')

    # Pumped hydro
    # QLD: Wivenhoe (http://www.csenergy.com.au/content-%28168%29-wivenhoe.htm)
    psh17 = generators.PumpedHydro(17, 500, 5000, label='poly 17 pumped-hydro')
    # NSW: Tumut 3 (6x250), Bendeela (2x80) and Kangaroo Valley (2x40)
    psh36 = generators.PumpedHydro(36, 1740, 15000, label='poly 36 pumped-hydro')
    return [psh17, psh36] + \
        [hydro24, hydro31, hydro35, hydro36, hydro38, hydro39] + \
        [hydro40, hydro41, hydro42, hydro43]


def replacement(context):
    """The current NEM fleet, more or less.

    >>> class C: pass
    >>> c = C()
    >>> replacement(c)
    >>> len(c.generators)
    14
    """
    coal = generators.Black_Coal(wildcard, 0)
    ocgt = generators.OCGT(wildcard, 0)
    context.generators = [coal] + _hydro() + [ocgt]


def _one_ccgt(context):
    """One CCGT only.

    >>> class C: pass
    >>> c = C()
    >>> _one_ccgt(c)
    >>> len(c.generators)
    1
    """
    context.generators = [generators.CCGT(wildcard, 0)]


def ccgt(context):
    """All gas scenario.

    >>> class C: pass
    >>> c = C()
    >>> ccgt(c)
    >>> len(c.generators)
    14
    """
    # pylint: disable=redefined-outer-name
    ccgt = generators.CCGT(wildcard, 0)
    ocgt = generators.OCGT(wildcard, 0)
    context.generators = [ccgt] + _hydro() + [ocgt]


def ccgt_ccs(context):
    """CCGT CCS scenario.

    >>> class C: pass
    >>> c = C()
    >>> ccgt_ccs(c)
    >>> len(c.generators)
    14
    """
    # pylint: disable=redefined-outer-name
    ccgt = generators.CCGT_CCS(wildcard, 0)
    ocgt = generators.OCGT(wildcard, 0)
    context.generators = [ccgt] + _hydro() + [ocgt]


def coal_ccs(context):
    """Coal CCS scenario.

    >>> class C: pass
    >>> c = C()
    >>> coal_ccs(c)
    >>> len(c.generators)
    14
    """
    coal = generators.Coal_CCS(wildcard, 0)
    ocgt = generators.OCGT(wildcard, 0)
    context.generators = [coal] + _hydro() + [ocgt]


def re100(context):
    """100% renewable electricity.

    >>> class C: pass
    >>> c = C()
    >>> re100(c)
    >>> len(c.generators)
    184
    """
    result = []
    # The following list is in merit order.
    for g in [PV1Axis, Wind, PumpedHydro, Hydro, CentralReceiver, Biofuel]:
        if g == PumpedHydro:
            result += [h for h in _hydro() if isinstance(h, PumpedHydro)]
        elif g == Hydro:
            result += [h for h in _hydro() if isinstance(h, Hydro) and not isinstance(h, PumpedHydro)]
        elif g == Biofuel:
            for poly in range(1, 44):
                result.append(g(poly, 0, label='polygon %d GT' % poly))
        elif g == PV1Axis:
            for poly in range(1, 44):
                result.append(g(poly, 0,
                                configfile.get('generation', 'pv1axis-trace'),
                                poly - 1,
                                build_limit=polygons.pv_limit[poly],
                                label='polygon %d PV' % poly))
        elif g == CentralReceiver:
            for poly in range(1, 44):
                result.append(g(poly, 0, 2, 6,
                                configfile.get('generation', 'cst-trace'),
                                poly - 1,
                                build_limit=polygons.cst_limit[poly],
                                label='polygon %d CST' % poly))
        elif g == Wind:
            for poly in range(1, 44):
                result.append(g(poly, 0,
                                configfile.get('generation', 'wind-trace'),
                                poly - 1,
                                build_limit=polygons.wind_limit[poly],
                                label='polygon %d wind' % poly))
        else:  # pragma: no cover
            raise ValueError

    context.generators = result


def re100_batteries(context):
    """Use lots of renewables plus battery storage.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> re100_batteries(c)
    >>> len(c.generators)
    185
    """
    re100(context)
    # discharge between 6pm and 6am daily
    hrs = list(range(0, 7)) + list(range(18, 24))
    battery = generators.Battery(wildcard, 0, 0, discharge_hours=hrs)
    g = context.generators
    context.generators = [battery] + g


def _one_per_poly(region):
    """Return three lists of wind, PV and CST generators, one per polygon.

    >>> from nemo import regions
    >>> wind, pv, cst = _one_per_poly(regions.tas)
    >>> len(wind), len(pv), len(cst)
    (4, 4, 4)
    """
    pv = []
    wind = []
    cst = []

    for poly in region.polygons:
        wind.append(generators.Wind(poly, 0,
                                    configfile.get('generation', 'wind-trace'),
                                    poly - 1,
                                    build_limit=polygons.wind_limit[poly],
                                    label='poly %d wind' % poly))
        pv.append(generators.PV1Axis(poly, 0,
                                     configfile.get('generation', 'pv1axis-trace'),
                                     poly - 1,
                                     build_limit=polygons.pv_limit[poly],
                                     label='poly %d PV' % poly))
        cst.append(generators.CentralReceiver(poly, 0, 2, 6,
                                              configfile.get('generation', 'cst-trace'),
                                              poly - 1,
                                              build_limit=polygons.cst_limit[poly],
                                              label='poly %d CST' % poly))
    return wind, pv, cst


def re100_one_region(context, region):
    """100% renewables in one region only.

    >>> from nemo import regions
    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> re100_one_region(c, regions.tas)
    >>> for g in c.generators: assert g.region() is regions.tas
    """
    re100(context)
    context.regions = [region]
    wind, pv, cst = _one_per_poly(region)
    newlist = wind
    newlist += pv
    newlist += [g for g in context.generators if
                isinstance(g, generators.Hydro) and g.region() is region]
    newlist += cst
    newlist += [g for g in context.generators if
                isinstance(g, generators.Biofuel) and g.region() is region]
    context.generators = newlist


def re_plus_ccs(context):
    """Mostly renewables with fossil and CCS augmentation.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> re_plus_ccs(c)
    >>> len(c.generators)
    185
    """
    re100(context)
    coal = generators.Black_Coal(wildcard, 0)
    # pylint: disable=redefined-outer-name
    coal_ccs = generators.Coal_CCS(wildcard, 0)
    # pylint: disable=redefined-outer-name
    ccgt = generators.CCGT(wildcard, 0)
    ccgt_ccs = generators.CCGT_CCS(wildcard, 0)
    ocgt = generators.OCGT(wildcard, 0)
    g = context.generators
    context.generators = [coal, coal_ccs, ccgt, ccgt_ccs] + g[:-4] + [ocgt]


def re_plus_fossil(context):
    """Mostly renewables with some fossil augmentation.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> re_plus_fossil(c)
    >>> len(c.generators)
    183
    """
    re100(context)
    # pylint: disable=redefined-outer-name
    coal = generators.Black_Coal(wildcard, 0)
    ccgt = generators.CCGT(wildcard, 0)
    ocgt = generators.OCGT(wildcard, 0)
    g = context.generators
    context.generators = [coal, ccgt] + g[:-4] + [ocgt]


def re100_dsp(context):
    """Mostly renewables with demand side participation.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> re100_dsp(c)
    >>> len(c.generators)
    187
    >>> isinstance(c.generators[-1], generators.DemandResponse)
    True
    """
    re100(context)
    g = context.generators
    context.generators = g + _demand_response()


def re100_nocst(context):
    """100% renewables, but no CST.

    >>> class C: pass
    >>> c = C()
    >>> re100_nocst(c)
    >>> for g in c.generators: assert not isinstance(g, generators.CST)
    """
    re100(context)
    newlist = [g for g in context.generators if not isinstance(g, generators.CST)]
    context.generators = newlist


def re100_nsw(context):
    """100% renewables in New South Wales only.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> re100_nsw(c)
    >>> for g in c.generators: assert g.region() is regions.nsw
    """
    re100_one_region(context, regions.nsw)


def re100_qld(context):
    """100% renewables in Queensland only.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> re100_qld(c)
    >>> for g in c.generators: assert g.region() is regions.qld
    """
    re100_one_region(context, regions.qld)


def re100_south_aus(context):
    """100% renewables in South Australia only.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> re100_south_aus(c)
    >>> for g in c.generators: assert g.region() is regions.sa
    """
    re100_one_region(context, regions.sa)


def theworks(context):
    """All technologies."""

    re100(context)
    # pylint: disable=redefined-outer-name
    egs = generators.Geothermal_EGS(wildcard, 0,
                                    configfile.get('generation', 'egs-geothermal-trace'), 38)
    hsa = generators.Geothermal_HSA(wildcard, 0,
                                    configfile.get('generation', 'hsa-geothermal-trace'), 38)
    pt = generators.ParabolicTrough(wildcard, 0, 2, 6,
                                    configfile.get('generation', 'cst-trace'), 12)
    thermals = [generators.Black_Coal(wildcard, 0),
                generators.Coal_CCS(wildcard, 0),
                generators.CCGT(wildcard, 0),
                generators.CCGT_CCS(wildcard, 0)]

    ocgt = generators.OCGT(wildcard, 0)
    batt = generators.Battery(wildcard, 0, 0)
    diesel = generators.Diesel(wildcard, 0)
    dem = generators.DemandResponse(wildcard, 0, 300)
    biomass = generators.Biomass(wildcard, 0)
    greenpower = generators.GreenPower(wildcard, 0)
    btm_pv = generators.Behind_Meter_PV(wildcard, 0,
                                        configfile.get('generation', 'rooftop-pv-trace'),
                                        0)
    g = context.generators

    context.generators = [hsa, egs, pt] + thermals + g[:-4] + \
        [btm_pv, ocgt, diesel, batt, dem, biomass, greenpower]


supply_scenarios = {'__one_ccgt__': _one_ccgt,  # nb. for testing only
                    'ccgt': ccgt,
                    'ccgt-ccs': ccgt_ccs,
                    'coal-ccs': coal_ccs,
                    're+ccs': re_plus_ccs,
                    're+fossil': re_plus_fossil,
                    're100': re100,
                    're100-qld': re100_qld,
                    're100-nsw': re100_nsw,
                    're100-sa': re100_south_aus,
                    're100+batteries': re100_batteries,
                    're100+dsp': re100_dsp,
                    're100-nocst': re100_nocst,
                    'replacement': replacement,
                    'theworks': theworks}


# Demand modifiers

def demand_switch(label):
    """Return a callback function to modify the demand.

    >>> demand_switch('unchanged')	  # doctest: +ELLIPSIS
    <function unchanged at ...>
    >>> demand_switch('roll:10')      # doctest: +ELLIPSIS
    <function ...>
    >>> demand_switch('scale:5')    # doctest: +ELLIPSIS
    <function ...>
    >>> demand_switch('scalex:0:10:5')    # doctest: +ELLIPSIS
    <function ...>
    >>> demand_switch('shift:100:10:12') # doctest: +ELLIPSIS
    <function ...>
    >>> demand_switch('shift:100:-2:12')
    Traceback (most recent call last):
      ...
    ValueError: hour < 0
    >>> demand_switch('shift:100:12:25')
    Traceback (most recent call last):
      ...
    ValueError: hour > 24
    >>> demand_switch('scalex:-1:12:20')
    Traceback (most recent call last):
      ...
    ValueError: hour < 0
    >>> demand_switch('scalex:12:25:20')
    Traceback (most recent call last):
      ...
    ValueError: hour > 24
    >>> demand_switch('scalex:20:8:20')
    Traceback (most recent call last):
      ...
    ValueError: to_hour comes before from_hour
    >>> demand_switch('peaks:10:34000') # doctest: +ELLIPSIS
    <function ...>
    >>> demand_switch('npeaks:10:5') # doctest: +ELLIPSIS
    <function ...>
    >>> demand_switch('foo')
    Traceback (most recent call last):
      ...
    ValueError: invalid scenario: foo
    """
    # pylint: disable=too-many-branches
    if label == 'unchanged':
        return unchanged

    if label.startswith('roll:'):
        # label form: "roll:X" rolls the load by X timesteps
        _, posns = label.split(':')
        posns = int(posns)
        return lambda context: roll_demand(context, posns)

    if label.startswith('scale:'):
        # label form: "scale:X" scales all of the load by X%
        _, factor = label.split(':')
        factor = 1 + float(factor) / 100
        return lambda context: scale_demand_by(context, factor)

    if label.startswith('scalex:'):
        # label form: "scalex:H1:H2:X" scales hours H1 to H2 by X%
        _, h1, h2, factor = label.split(':')
        from_hour = int(h1)
        to_hour = int(h2)
        if from_hour < 0 or to_hour < 0:
            raise ValueError("hour < 0")
        if from_hour > 24 or to_hour > 24:
            raise ValueError("hour > 24")
        if to_hour <= from_hour:
            raise ValueError("to_hour comes before from_hour")
        factor = 1 + float(factor) / 100
        return lambda context: scale_range_demand(context,
                                                  from_hour, to_hour, factor)

    if label.startswith('scaletwh:'):
        # label form: "scaletwh:N" scales demand to N TWh
        _, n = label.split(':')
        new_demand = float(n)
        return lambda context: scale_demand_twh(context, new_demand)

    if label.startswith('shift:'):
        # label form: "shift:N:H1:H2" load shifts N MW every day
        _, demand, h1, h2 = label.split(':')
        demand = int(demand)
        from_hour = int(h1)
        to_hour = int(h2)
        if from_hour < 0 or to_hour < 0:
            raise ValueError("hour < 0")
        if from_hour > 24 or to_hour > 24:
            raise ValueError("hour > 24")
        return lambda context: shift_demand(context, demand, from_hour, to_hour)

    if label.startswith('peaks:'):
        # label form: "peaks:N:X" adjust demand peaks over N megawatts
        # by X%
        _, power, factor = label.split(':')
        power = int(power)
        factor = 1 + float(factor) / 100
        return lambda context: scale_peaks(context, power, factor)

    if label.startswith('npeaks:'):
        # label form: "npeaks:N:X" adjust top N demand peaks by X%
        _, topn, factor = label.split(':')
        topn = int(topn)
        factor = 1 + float(factor) / 100
        return lambda context: scale_npeaks(context, topn, factor)

    raise ValueError('invalid scenario: %s' % label)


# pylint: disable=unused-argument
def unchanged(context):
    """No demand modification.

    >>> class C: pass
    >>> c = C()
    >>> unchanged(c)
    """


def roll_demand(context, posns):
    """
    Roll demand by posns timesteps.

    >>> class C: pass
    >>> c = C()
    >>> c.demand = pd.DataFrame(list(range(10)))
    >>> roll_demand(c, 1)
    >>> print(c.demand)
       0
    0  9
    1  0
    2  1
    3  2
    4  3
    5  4
    6  5
    7  6
    8  7
    9  8
    """
    idx = context.demand.index
    values = np.roll(context.demand.values, posns)
    context.demand = pd.DataFrame(data=values, index=idx)


def scale_range_demand(context, from_hour, to_hour, factor):
    """
    Scale demand between from_hour and to_hour by factor%.

    >>> class C: pass
    >>> c = C()
    >>> c.demand = pd.DataFrame(list(range(10)))
    >>> scale_range_demand(c, 0, 4, 1.2)
    >>> print(c.demand)
         0
    0  0.0
    1  1.2
    2  2.4
    3  3.6
    4  4.0
    5  5.0
    6  6.0
    7  7.0
    8  8.0
    9  9.0
    """
    for hour in range(from_hour, to_hour):
        context.demand[hour::24] *= factor


def scale_demand_twh(context, new_demand):
    """
    Scale demand to new_demand TWh.

    >>> class C: pass
    >>> c = C()
    >>> c.demand = pd.DataFrame([100]*10)
    >>> scale_demand_twh(c, 0.0002)
    >>> print(c.demand.loc[0])
    0    20.0
    Name: 0, dtype: float64
    """
    total_demand = context.demand.values.sum()
    new_demand *= 10 ** 6
    context.demand *= new_demand / total_demand


def scale_demand_by(context, factor):
    """
    Scale demand by factor%.

    >>> class C: pass
    >>> c = C()
    >>> c.demand = pd.DataFrame([0, 1, 2])
    >>> scale_demand_by(c, 1.2)
    >>> print(c.demand)
         0
    0  0.0
    1  1.2
    2  2.4
    """
    context.demand *= factor


def shift_demand(context, demand, from_hour, to_hour):
    """Move N MW of demand from from_hour to to_hour."""
    # Shift demand within in each polygon
    for p in range(43):
        for r in context.regions:
            if p + 1 in r.polygons:
                weight = r.polygons[p + 1]
                if context.demand[p].sum() > 0:
                    context.demand[p, from_hour::24] -= demand * weight
                    context.demand[p, to_hour::24] += demand * weight
    assert np.all(context.demand >= 0), \
        "negative load in hour %d" % from_hour


def scale_peaks(context, power, factor):
    """Adjust demand peaks over N megawatts by factor%.

    >>> class C: pass
    >>> c = C()
    >>> c.demand = pd.DataFrame([[0]*5]*5)
    >>> c.demand.loc[3] = 5000
    >>> scale_peaks(c, 3000, 0.5)
    >>> c.demand.loc[3]
    0    2500.0
    1    2500.0
    2    2500.0
    3    2500.0
    4    2500.0
    Name: 3, dtype: float64
    """
    agg_demand = context.demand.sum(axis=1)
    context.demand[agg_demand > power] *= factor


def scale_npeaks(context, topn, factor):
    """Adjust top N demand peaks by X%.

    >>> class C: pass
    >>> c = C()
    >>> c.demand = pd.DataFrame([[0]*5]*5)
    >>> c.demand.loc[3] = 5000
    >>> c.demand.loc[4] = 3000
    >>> scale_npeaks(c, 1, 0.5)
    >>> c.demand.loc[4]
    0    3000.0
    1    3000.0
    2    3000.0
    3    3000.0
    4    3000.0
    Name: 4, dtype: float64
    >>> c.demand.loc[3]
    0    2500.0
    1    2500.0
    2    2500.0
    3    2500.0
    4    2500.0
    Name: 3, dtype: float64
    """
    agg_demand = context.demand.sum(axis=1).sort_values(ascending=False)
    rng = agg_demand.head(topn).index
    context.demand.loc[rng] *= factor
