# Copyright (C) 2012, 2013, 2014 Ben Elliston
# Copyright (C) 2014 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Supply and demand side scenarios."""

import heapq
import numpy as np

import consts
import generators
import polygons
import regions
import configfile


def supply_switch(label):
    """
    Return a callback function to set up a given scenario.

    >>> supply_switch('re100') # doctest: +ELLIPSIS
    <function re100 at 0x...>
    >>> supply_switch('foo')
    Traceback (most recent call last):
      ...
    ValueError: unknown supply scenario foo
    """
    try:
        callback = supply_scenarios[label]
    except KeyError:
        raise ValueError('unknown supply scenario %s' % label)
    return callback


def _demand_response():
    """
    Return a list of DR 'generators'.

    >>> dr = _demand_response()
    >>> len(dr)
    3
    """
    dr1 = generators.DemandResponse(regions.nsw, 1000, 100, "DR100")
    dr2 = generators.DemandResponse(regions.nsw, 1000, 500, "DR500")
    dr3 = generators.DemandResponse(regions.nsw, 1000, 1000, "DR1000")
    return [dr1, dr2, dr3]


def _hydro():
    """
    Return a list of existing hydroelectric generators.

    >>> h = _hydro()
    >>> len(h)
    5
    """
    hydro1 = generators.Hydro(regions.tas, 2740,
                              label=regions.tas.id + ' hydro')
    hydro2 = generators.Hydro(regions.nsw, 1160,
                              label=regions.nsw.id + ' hydro')
    hydro3 = generators.Hydro(regions.vic, 960,
                              label=regions.vic.id + ' hydro')
    psh1 = generators.PumpedHydro(regions.qld, 500, 5000,
                                  label='QLD1 pumped-hydro')
    psh2 = generators.PumpedHydro(regions.nsw, 1740, 15000,
                                  label='NSW1 pumped-hydro')
    return [hydro1, hydro2, hydro3, psh1, psh2]


def replacement(context):
    """The current NEM fleet, more or less.

    >>> class C: pass
    >>> c = C()
    >>> replacement(c)
    >>> len(c.generators)
    7
    """
    coal = generators.Black_Coal(regions.nsw, 0)
    ocgt = generators.OCGT(regions.nsw, 0)
    context.generators = [coal] + _hydro() + [ocgt]


def _one_ccgt(context):
    """One CCGT only.

    >>> class C: pass
    >>> c = C()
    >>> _one_ccgt(c)
    >>> len(c.generators)
    1
    """
    context.generators = [generators.CCGT(regions.nsw, 0)]


def ccgt(context):
    """All gas scenario.

    >>> class C: pass
    >>> c = C()
    >>> ccgt(c)
    >>> len(c.generators)
    7
    """
    # pylint: disable=redefined-outer-name
    ccgt = generators.CCGT(regions.nsw, 0)
    ocgt = generators.OCGT(regions.nsw, 0)
    context.generators = [ccgt] + _hydro() + [ocgt]


def ccgt_ccs(context):
    """CCGT CCS scenario.

    >>> class C: pass
    >>> c = C()
    >>> ccgt_ccs(c)
    >>> len(c.generators)
    7
    """
    # pylint: disable=redefined-outer-name
    ccgt = generators.CCGT_CCS(regions.nsw, 0)
    ocgt = generators.OCGT(regions.nsw, 0)
    context.generators = [ccgt] + _hydro() + [ocgt]


def coal_ccs(context):
    """Coal CCS scenario.

    >>> class C: pass
    >>> c = C()
    >>> coal_ccs(c)
    >>> len(c.generators)
    7
    """
    coal = generators.Coal_CCS(regions.nsw, 0)
    ocgt = generators.OCGT(regions.nsw, 0)
    context.generators = [coal] + _hydro() + [ocgt]


def re100(context):
    # pylint: disable=unused-argument
    """100% renewable electricity.

    >>> class C: pass
    >>> c = C()
    >>> re100(c)
    >>> len(c.generators)
    22
    """
    from generators import CentralReceiver, Wind, PV1Axis, Hydro, PumpedHydro, Biofuel

    capfactor = {CentralReceiver: 0.60, Wind: 0.40, PV1Axis: 0.33, Hydro: None, PumpedHydro: None, Biofuel: None}
    energy_fraction = {CentralReceiver: 0.40, Wind: 0.30, PV1Axis: 0.10, Hydro: None, PumpedHydro: None, Biofuel: None}

    result = []
    # The following list is in merit order.
    for g in [PV1Axis, Wind, CentralReceiver, Hydro, PumpedHydro, Biofuel]:
        if capfactor[g] is not None:
            capacity = 204.4 * consts.twh * energy_fraction[g] / (capfactor[g] * 8760)
        if g == PumpedHydro:
            # QLD: Wivenhoe (http://www.csenergy.com.au/content-%28168%29-wivenhoe.htm)
            result.append(PumpedHydro(regions.qld, 500, 5000, label='QLD1 pumped-hydro'))
            # NSW: Tumut 3 (6x250), Bendeela (2x80) and Kangaroo Valley (2x40)
            result.append(PumpedHydro(regions.nsw, 1740, 15000, label='NSW1 pumped-hydro'))
        elif g == Hydro:
            # Ignore the one small hydro plant in SA.
            result.append(Hydro(regions.tas, 2740, label=regions.tas.id + ' hydro'))
            result.append(Hydro(regions.nsw, 1160, label=regions.nsw.id + ' hydro'))
            result.append(Hydro(regions.vic, 960, label=regions.vic.id + ' hydro'))
        elif g == Biofuel:
            # 24 GW biofuelled gas turbines (fixed)
            # distribute 24GW of biofuelled turbines across chosen regions
            # the region list is in order of approximate demand
            rgns = [regions.nsw, regions.qld, regions.sa, regions.tas, regions.vic]
            for r in rgns:
                result.append(Biofuel(r, 24000 / len(rgns), label=r.id + ' GT'))
        elif g == PV1Axis:
            # Hand chosen polygons with high capacity factors
            for poly in [14, 21, 13, 37]:
                rgn = polygons.region_table[poly]
                # Put 25% PV capacity in each region.
                result.append(g(rgn, capacity * 0.25,
                                configfile.get('generation', 'pv1axis-trace'),
                                poly - 1,
                                build_limit=polygons.pv_limit[poly],
                                label=rgn.id + ' 1-axis PV'))
        elif g == CentralReceiver:
            polys = [14, 20, 21]
            capacity /= len(polys)
            for poly in polys:
                rgn = polygons.region_table[poly]
                result.append(g(rgn, capacity, 2, 6,
                                configfile.get('generation', 'cst-trace'),
                                poly - 1,
                                build_limit=polygons.cst_limit[poly],
                                label=rgn.id + ' CST'))
        elif g == Wind:
            # Hand chosen polygons with high capacity factors
            for poly in [1, 20, 24, 39, 43]:
                rgn = polygons.region_table[poly]
                # Put 20% wind capacity in each region.
                result.append(g(rgn, capacity * 0.2,
                                configfile.get('generation', 'wind-trace'),
                                poly - 1,
                                delimiter=',',
                                build_limit=polygons.wind_limit[poly],
                                label=rgn.id + ' wind'))
        else:  # pragma: no cover
            raise(ValueError)

    context.generators = result


def re100_batteries(context):
    """Use lots of renewables plus battery storage.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> re100_batteries(c)
    >>> len(c.generators)
    23
    """
    re100(context)
    nsw_battery = generators.Battery(regions.nsw, 0, 0)
    g = context.generators
    context.generators = g[0:9] + [nsw_battery] + g[9:]


def re_plus_ccs(context):
    """Mostly renewables with fossil and CCS augmentation.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> re_plus_ccs(c)
    >>> len(c.generators)
    23
    """
    re100(context)
    coal = generators.Black_Coal(regions.nsw, 0)
    # pylint: disable=redefined-outer-name
    coal_ccs = generators.Coal_CCS(regions.nsw, 0)
    # pylint: disable=redefined-outer-name
    ccgt = generators.CCGT(regions.nsw, 0)
    ccgt_ccs = generators.CCGT_CCS(regions.nsw, 0)
    ocgt = generators.OCGT(regions.nsw, 0)
    g = context.generators
    context.generators = [coal, coal_ccs, ccgt, ccgt_ccs] + g[:-4] + [ocgt]


def re_plus_fossil(context):
    """Mostly renewables with some fossil augmentation.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> re_plus_fossil(c)
    >>> len(c.generators)
    21
    """
    re100(context)
    # pylint: disable=redefined-outer-name
    coal = generators.Black_Coal(regions.nsw, 0)
    ccgt = generators.CCGT(regions.nsw, 0)
    ocgt = generators.OCGT(regions.nsw, 0)
    g = context.generators
    context.generators = [coal, ccgt] + g[:-4] + [ocgt]


def re100_dsp(context):
    """Mostly renewables with demand side participation.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> re100_dsp(c)
    >>> len(c.generators)
    25
    >>> isinstance(c.generators[-1], generators.DemandResponse)
    True
    """
    re100(context)
    g = context.generators
    context.generators = g + _demand_response()


def re100_geothermal_egs(context):
    """100% renewables plus EGS geothermal.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> re100_geothermal_egs(c)
    >>> isinstance(c.generators[0], generators.Geothermal)
    True
    """
    re100(context)
    g = context.generators
    geo = generators.Geothermal_EGS(regions.qld, 0,
                                    configfile.get('generation', 'egs-geothermal-trace'),
                                    14,  # (polygon 14)
                                    'EGS geothermal')
    context.generators = [geo] + g


def re100_geothermal_hsa(context):
    """100% renewables plus HSA geothermal.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> re100_geothermal_hsa(c)
    >>> isinstance(c.generators[0], generators.Geothermal_HSA)
    True
    """
    re100(context)
    g = context.generators
    geo = generators.Geothermal_HSA(regions.vic, 0,
                                    configfile.get('generation', 'hsa-geothermal-trace'),
                                    38,  # (polygon 38)
                                    'HSA geothermal')
    context.generators = [geo] + g


def re100_geothermal_both(context):
    """100% renewables plus both HSA and EGS geothermal.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> re100_geothermal_both(c)
    >>> isinstance(c.generators[0], generators.Geothermal_HSA)
    True
    >>> isinstance(c.generators[1], generators.Geothermal_EGS)
    True
    """
    # Grab the HSA generator.
    re100_geothermal_hsa(context)
    hsa = context.generators[0]

    # Prepend it to the EGS geothermal scenario.
    re100_geothermal_egs(context)
    context.generators = [hsa] + context.generators


def re100_geothermal_both_nocst(context):
    """100% renewables plus geothermal, but no CST.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> re100_geothermal_both_nocst(c)
    >>> isinstance(c.generators[0], generators.Geothermal_HSA)
    True
    >>> isinstance(c.generators[1], generators.Geothermal_EGS)
    True
    >>> for g in c.generators: assert not isinstance(g, generators.CST)
    """
    re100_geothermal_both(context)
    newlist = [g for g in context.generators if not isinstance(g, generators.CST)]
    context.generators = newlist


def re100_nocst(context):
    """100% renewables, but no CST.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> re100_nocst(c)
    >>> for g in c.generators: assert not isinstance(g, generators.CST)
    """
    re100(context)
    newlist = [g for g in context.generators if not isinstance(g, generators.CST)]
    context.generators = newlist


def theworks(context):
    """All technologies.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> theworks(c)
    >>> len(c.generators)
    26
    """
    re100(context)
    # pylint: disable=redefined-outer-name
    # use polygon 38
    geo = generators.Geothermal_HSA(regions.nsw, 0,
                                    configfile.get('generation', 'hsa-geothermal-trace'), 38)
    coal = generators.Black_Coal(regions.nsw, 0)
    coal_ccs = generators.Coal_CCS(regions.nsw, 0)
    ccgt = generators.CCGT(regions.nsw, 0)
    ccgt_ccs = generators.CCGT_CCS(regions.nsw, 0)
    ocgt = generators.OCGT(regions.nsw, 0)
    batt = generators.Battery(regions.nsw, 0, 0)
    dem = generators.DemandResponse(regions.nsw, 0, 300)
    g = context.generators
    context.generators = [geo, coal, coal_ccs, ccgt, ccgt_ccs] + g[:-4] + \
                         [ocgt, batt, dem]

supply_scenarios = {'re100': re100,
                    'ccgt': ccgt,
                    'ccgt-ccs': ccgt_ccs,
                    'coal-ccs': coal_ccs,
                    're100+batteries': re100_batteries,
                    'replacement': replacement,
                    're100+dsp': re100_dsp,
                    're100+egs': re100_geothermal_egs,
                    're100+hsa': re100_geothermal_hsa,
                    're100+geo': re100_geothermal_both,
                    're100-nocst': re100_nocst,
                    're100+geo-nocst': re100_geothermal_both_nocst,
                    're+fossil': re_plus_fossil,
                    're+ccs': re_plus_ccs,
                    'theworks': theworks,
                    '__one_ccgt__': _one_ccgt  # for testing only
                    }


### Demand modifiers

def demand_switch(label):
    """Return a callback function to modify the demand.

    >>> demand_switch('unchanged')	  # doctest: +ELLIPSIS
    <function unchanged at ...>
    >>> demand_switch('roll:10')      # doctest: +ELLIPSIS
    <function <lambda> at ...>
    >>> demand_switch('scale:5')    # doctest: +ELLIPSIS
    <function <lambda> at ...>
    >>> demand_switch('shift:100:10:12') # doctest: +ELLIPSIS
    <function <lambda> at ...>
    >>> demand_switch('shift:100:-2:12')
    Traceback (most recent call last):
      ...
    ValueError: invalid scenario: shift:100:-2:12
    >>> demand_switch('peaks:10:34000') # doctest: +ELLIPSIS
    <function <lambda> at ...>
    >>> demand_switch('npeaks:10:5') # doctest: +ELLIPSIS
    <function <lambda> at ...>
    >>> demand_switch('foo')
    Traceback (most recent call last):
      ...
    ValueError: invalid scenario: foo
    """
    try:
        if label == 'unchanged':
            return unchanged

        elif label.startswith('roll:'):
            # label form: "roll:X" rolls the load by X timesteps
            _, posns = label.split(':')
            posns = int(posns)
            return lambda context: roll_demand(context, posns)

        elif label.startswith('scale:'):
            # label form: "scale:X" scales the load by X%
            _, factor = label.split(':')
            factor = 1 + int(factor) / 100.
            return lambda context: scale_demand(context, factor)

        elif label.startswith('shift:'):
            # label form: "shift:N:H1:H2" load shifts N MW every day
            _, demand, h1, h2 = label.split(':')
            demand = int(demand)
            fromHour = int(h1)
            toHour = int(h2)
            if fromHour < 0 or fromHour >= 24 or toHour < 0 or toHour >= 24:
                raise ValueError
            return lambda context: shift_demand(context, demand, fromHour, toHour)

        elif label.startswith('peaks:'):
            # label form: "peaks:N:X" adjust demand peaks over N megawatts
            # by X%
            _, power, factor = label.split(':')
            power = int(power)
            factor = 1 + int(factor) / 100.
            return lambda context: scale_peaks(context, power, factor)

        elif label.startswith('npeaks:'):
            # label form: "npeaks:N:X" adjust top N demand peaks by X%
            _, topn, factor = label.split(':')
            topn = int(topn)
            factor = 1 + int(factor) / 100.
            return lambda context: scale_npeaks(context, topn, factor)
        else:
            raise ValueError

    except ValueError:
        raise ValueError('invalid scenario: %s' % label)


def unchanged(context):
    """No demand modification.

    >>> class C: pass
    >>> c = C()
    >>> unchanged(c)
    """
    # pylint: disable=unused-argument
    pass


def roll_demand(context, posns):
    """
    Roll demand by posns timesteps.

    >>> class C: pass
    >>> c = C()
    >>> c.demand = np.arange(3)
    >>> roll_demand(c, 1)
    >>> print c.demand
    [2 0 1]
    """
    context.demand = np.roll(context.demand, posns)


def scale_demand(context, factor):
    """
    Scale demand by factor%.

    >>> class C: pass
    >>> c = C()
    >>> c.demand = np.arange(3)
    >>> scale_demand(c, 1.2)
    >>> print c.demand   # doctest: +NORMALIZE_WHITESPACE
    [ 0. 1.2 2.4]
    """
    context.demand = context.demand * factor


def shift_demand(context, demand, fromHour, toHour):
    """Move N MW of demand from fromHour to toHour.

    >>> class C: pass
    >>> c = C()
    >>> c.demand = np.zeros ((5,10))
    >>> c.demand[::,3] = 5000
    >>> shift_demand(c, 2500, 3, 4)
    >>> c.demand[::,3]
    array([ 4500.,  4500.,  4500.,  4500.,  4500.])
    >>> c.demand[::,4]
    array([ 500.,  500.,  500.,  500.,  500.])
    """
    # Shed equally in each region for simplicity
    demand /= 5
    context.demand[::, fromHour::24] -= demand
    context.demand[::, toHour::24] += demand
    # Ensure load never goes negative
    context.demand = np.where(context.demand < 0, 0, context.demand)


def scale_peaks(context, power, factor):
    """Adjust demand peaks over N megawatts by factor%.

    >>> class C: pass
    >>> c = C()
    >>> c.demand = np.zeros ((5,10))
    >>> c.demand[::,3] = 5000
    >>> scale_peaks(c, 3000, 0.5)
    >>> c.demand[::,3]
    array([ 2500.,  2500.,  2500.,  2500.,  2500.])
    """
    agg_demand = context.demand.sum(axis=0)
    where = np.where(agg_demand > power)
    context.demand[::, where] *= factor


def scale_npeaks(context, topn, factor):
    """Adjust top N demand peaks by X%.

    >>> class C: pass
    >>> c = C()
    >>> c.demand = np.zeros ((5,10))
    >>> c.demand[::,3] = 5000
    >>> c.demand[::,4] = 3000
    >>> scale_npeaks(c, 1, 0.5)
    >>> c.demand[::,4]
    array([ 3000.,  3000.,  3000.,  3000.,  3000.])
    >>> c.demand[::,3]
    array([ 2500.,  2500.,  2500.,  2500.,  2500.])
    """
    agg_demand = context.demand.sum(axis=0)
    top_demands = heapq.nlargest(topn, agg_demand)
    # A trick from:
    # http://docs.scipy.org/doc/numpy/reference/generated/
    #   numpy.where.html#numpy.where
    ix = np.in1d(agg_demand.ravel(), top_demands).reshape(agg_demand.shape)
    where = np.where(ix)
    context.demand[::, where] *= factor
