# Copyright (C) 2012, 2013, 2014 Ben Elliston
# Copyright (C) 2014, 2015, 2016 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Supply and demand side scenarios."""
import heapq
import numpy as np

import configfile
import generators
import polygons
import regions


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
    dr1 = generators.DemandResponse(polygons.wildcard, 1000, 100, "DR100")
    dr2 = generators.DemandResponse(polygons.wildcard, 1000, 500, "DR500")
    dr3 = generators.DemandResponse(polygons.wildcard, 1000, 1000, "DR1000")
    return [dr1, dr2, dr3]


def _hydro():
    """
    Return a list of existing hydroelectric generators.

    >>> h = _hydro()
    >>> len(h)
    5
    """
    nswpoly = min(regions.nsw.polygons)
    taspoly = min(regions.tas.polygons)
    vicpoly = min(regions.vic.polygons)

    hydro1 = generators.Hydro(taspoly, 2255,
                              label=regions.tas.id + ' hydro')
    hydro2 = generators.Hydro(nswpoly, 910,
                              label=regions.nsw.id + ' hydro')
    hydro3 = generators.Hydro(vicpoly, 2237,
                              label=regions.vic.id + ' hydro')
    # QLD: Wivenhoe (http://www.csenergy.com.au/content-%28168%29-wivenhoe.htm)
    # (polygon 17)
    psh1 = generators.PumpedHydro(17, 500, 5000,
                                  label='QLD1 pumped-hydro')
    # NSW: Tumut 3 (6x250), Bendeela (2x80) and Kangaroo Valley (2x40)
    psh2 = generators.PumpedHydro(36, 1740, 15000,
                                  label='NSW1 pumped-hydro')
    return [psh1, psh2, hydro1, hydro2, hydro3]


def replacement(context):
    """The current NEM fleet, more or less.

    >>> class C: pass
    >>> c = C()
    >>> replacement(c)
    >>> len(c.generators)
    7
    """
    coal = generators.Black_Coal(polygons.wildcard, 0)
    ocgt = generators.OCGT(polygons.wildcard, 0)
    context.generators = [coal] + _hydro() + [ocgt]


def _one_ccgt(context):
    """One CCGT only.

    >>> class C: pass
    >>> c = C()
    >>> _one_ccgt(c)
    >>> len(c.generators)
    1
    """
    context.generators = [generators.CCGT(polygons.wildcard, 0)]


def ccgt(context):
    """All gas scenario.

    >>> class C: pass
    >>> c = C()
    >>> ccgt(c)
    >>> len(c.generators)
    7
    """
    # pylint: disable=redefined-outer-name
    ccgt = generators.CCGT(polygons.wildcard, 0)
    ocgt = generators.OCGT(polygons.wildcard, 0)
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
    ccgt = generators.CCGT_CCS(polygons.wildcard, 0)
    ocgt = generators.OCGT(polygons.wildcard, 0)
    context.generators = [ccgt] + _hydro() + [ocgt]


def coal_ccs(context):
    """Coal CCS scenario.

    >>> class C: pass
    >>> c = C()
    >>> coal_ccs(c)
    >>> len(c.generators)
    7
    """
    coal = generators.Coal_CCS(polygons.wildcard, 0)
    ocgt = generators.OCGT(polygons.wildcard, 0)
    context.generators = [coal] + _hydro() + [ocgt]


def re100(context):
    """100% renewable electricity.

    >>> class C: pass
    >>> c = C()
    >>> re100(c)
    >>> len(c.generators)
    22
    """
    from generators import CentralReceiver, Wind, PV1Axis, Hydro, PumpedHydro, Biofuel

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
                                delimiter=',',
                                build_limit=polygons.wind_limit[poly],
                                label='polygon %d wind' % poly))
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
    # discharge between 6pm and 6am daily
    hrs = range(0, 7) + range(18, 24)
    battery = generators.Battery(polygons.wildcard, 0, 0, dischargeHours=hrs)
    g = context.generators
    context.generators = [battery] + g


def _one_per_poly(region):
    """Return three lists of wind, PV and CST generators, one per polygon.

    >>> import regions
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
                                    delimiter=',',
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

    >>> import regions
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
    newlist += [g for g in context.generators if isinstance(g, generators.Hydro) and g.region() is region]
    newlist += cst
    newlist += [g for g in context.generators if isinstance(g, generators.Biofuel) and g.region() is region]
    context.generators = newlist


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
    coal = generators.Black_Coal(polygons.wildcard, 0)
    # pylint: disable=redefined-outer-name
    coal_ccs = generators.Coal_CCS(polygons.wildcard, 0)
    # pylint: disable=redefined-outer-name
    ccgt = generators.CCGT(polygons.wildcard, 0)
    ccgt_ccs = generators.CCGT_CCS(polygons.wildcard, 0)
    ocgt = generators.OCGT(polygons.wildcard, 0)
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
    coal = generators.Black_Coal(polygons.wildcard, 0)
    ccgt = generators.CCGT(polygons.wildcard, 0)
    ocgt = generators.OCGT(polygons.wildcard, 0)
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
    >>> re100_geothermal_egs(c)
    >>> isinstance(c.generators[0], generators.Geothermal)
    True
    """
    re100(context)
    g = context.generators
    poly = 14
    geo = generators.Geothermal_EGS(poly, 0,
                                    configfile.get('generation',
                                                   'egs-geothermal-trace'), poly,
                                    'EGS geothermal')
    context.generators = [geo] + g


def re100_geothermal_hsa(context):
    """100% renewables plus HSA geothermal.

    >>> class C: pass
    >>> c = C()
    >>> re100_geothermal_hsa(c)
    >>> isinstance(c.generators[0], generators.Geothermal_HSA)
    True
    """
    re100(context)
    g = context.generators
    poly = 38
    geo = generators.Geothermal_HSA(poly, 0,
                                    configfile.get('generation',
                                                   'hsa-geothermal-trace'), poly,
                                    'HSA geothermal')
    context.generators = [geo] + g


def re100_geothermal_both(context):
    """100% renewables plus both HSA and EGS geothermal.

    >>> class C: pass
    >>> c = C()
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
    >>> re100_geothermal_both_nocst(c)
    >>> for g in c.generators: assert not isinstance(g, generators.CST)
    """
    re100_geothermal_both(context)
    newlist = [g for g in context.generators if not isinstance(g, generators.CST)]
    context.generators = newlist


def re100_geothermal_both_nopv(context):
    """100% renewables plus geothermal, but no CST.

    >>> class C: pass
    >>> c = C()
    >>> re100_geothermal_both_nopv(c)
    >>> for g in c.generators: assert not isinstance(g, generators.PV)
    """
    re100_geothermal_both(context)
    newlist = [g for g in context.generators if not isinstance(g, generators.PV)]
    context.generators = newlist


def re100_geothermal_both_nowind(context):
    """100% renewables plus geothermal, but no CST.

    >>> class C: pass
    >>> c = C()
    >>> re100_geothermal_both_nowind(c)
    >>> for g in c.generators: assert not isinstance(g, generators.Wind)
    """
    re100_geothermal_both(context)
    newlist = [g for g in context.generators if not isinstance(g, generators.Wind)]
    context.generators = newlist


def re100_geothermal_both_novre(context):
    """100% renewables plus geothermal, but no variable renewable energy (VRE).

    >>> class C: pass
    >>> c = C()
    >>> re100_geothermal_both_novre(c)
    >>> for g in c.generators: assert not isinstance(g, generators.Wind) and not isinstance(g, generators.PV)
    """
    re100_geothermal_both(context)
    newlist = [g for g in context.generators if not isinstance(g, generators.Wind) and not isinstance(g, generators.PV)]
    context.generators = newlist


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


def re100_egs_nocst(context):
    """100% renewables with EGS geothermal but no CST.

    >>> class C: pass
    >>> c = C()
    >>> re100_egs_nocst(c)
    >>> for g in c.generators: assert not isinstance(g, generators.CST)
    """
    re100_geothermal_egs(context)
    newlist = [g for g in context.generators if not isinstance(g, generators.CST)]
    context.generators = newlist


def re100_hsa_nocst(context):
    """100% renewables with HSA geothermal, but no CST.

    >>> class C: pass
    >>> c = C()
    >>> re100_hsa_nocst(c)
    >>> for g in c.generators: assert not isinstance(g, generators.CST)
    """
    re100_geothermal_hsa(context)
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
    """All technologies.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = []
    >>> theworks(c)
    >>> len(c.generators)
    28
    """
    re100(context)
    # pylint: disable=redefined-outer-name
    geo = generators.Geothermal_HSA(polygons.wildcard, 0,
                                    configfile.get('generation', 'hsa-geothermal-trace'), 38)
    pt = generators.ParabolicTrough(polygons.wildcard, 0, 2, 6,
                                    configfile.get('generation', 'cst-trace'), 12)
    coal = generators.Black_Coal(polygons.wildcard, 0)
    coal_ccs = generators.Coal_CCS(polygons.wildcard, 0)
    ccgt = generators.CCGT(polygons.wildcard, 0)
    ccgt_ccs = generators.CCGT_CCS(polygons.wildcard, 0)
    ocgt = generators.OCGT(polygons.wildcard, 0)
    batt = generators.Battery(polygons.wildcard, 0, 0)
    diesel = generators.Diesel(polygons.wildcard, 0)
    dem = generators.DemandResponse(polygons.wildcard, 0, 300)
    g = context.generators
    context.generators = [geo, pt, coal, coal_ccs, ccgt, ccgt_ccs] + \
        g[:-4] + [ocgt, diesel, batt, dem]

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
                    're100+egs': re100_geothermal_egs,
                    're100+egs-nocst': re100_egs_nocst,
                    're100+geo': re100_geothermal_both,
                    're100+geo-nocst': re100_geothermal_both_nocst,
                    're100+geo-nopv': re100_geothermal_both_nopv,
                    're100+geo-novre': re100_geothermal_both_novre,
                    're100+geo-nowind': re100_geothermal_both_nowind,
                    're100+hsa': re100_geothermal_hsa,
                    're100+hsa-nocst': re100_hsa_nocst,
                    're100-nocst': re100_nocst,
                    'replacement': replacement,
                    'theworks': theworks
                    }


# Demand modifiers

def demand_switch(label):
    """Return a callback function to modify the demand.

    >>> demand_switch('unchanged')	  # doctest: +ELLIPSIS
    <function unchanged at ...>
    >>> demand_switch('roll:10')      # doctest: +ELLIPSIS
    <function <lambda> at ...>
    >>> demand_switch('scale:5')    # doctest: +ELLIPSIS
    <function <lambda> at ...>
    >>> demand_switch('scalex:0:100:5')    # doctest: +ELLIPSIS
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
            # label form: "scale:X" scales all of the load by X%
            _, factor = label.split(':')
            factor = 1 + int(factor) / 100.
            return lambda context: scale_demand(context, factor)

        elif label.startswith('scalex:'):
            # label form: "scalex:H1:H2:X" scales hours H1 to H2 by X%
            _, h1, h2, factor = label.split(':')
            fromHour = int(h1)
            toHour = int(h2)
            factor = 1 + int(factor) / 100.
            return lambda context: scale_range_demand(context,
                                                      fromHour, toHour, factor)

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


def scale_range_demand(context, fromHour, toHour, factor):
    """
    Scale demand between fromHour and toHour by factor%.

    >>> class C: pass
    >>> c = C()
    >>> c.demand = np.zeros((1,10))
    >>> c.demand[:] = np.arange(10)
    >>> scale_range_demand(c, 0, 4, 1.2)
    >>> print c.demand   # doctest: +NORMALIZE_WHITESPACE
    [[ 0.  1.2  2.4  3.6  4.  5.  6.  7.  8.  9. ]]
    """
    context.demand[:, fromHour:toHour] *= factor


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
