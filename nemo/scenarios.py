# Copyright (C) 2012, 2013, 2014 Ben Elliston
# Copyright (C) 2014, 2015, 2016 The University of New South Wales
# Copyright (C) 2016 IT Power (Australia)
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Supply side scenarios."""

from nemo import configfile, regions
from nemo.generators import (Battery, Biofuel, Black_Coal,
                             CentralReceiver, CCGT, CCGT_CCS,
                             Coal_CCS, CST, DemandResponse, Hydro,
                             OCGT, PV1Axis, PumpedHydro, Wind)

from nemo.polygons import WILDCARD, wind_limit, pv_limit, cst_limit


def _demand_response():
    """
    Return a list of DR 'generators'.

    >>> dr = _demand_response()
    >>> len(dr)
    3
    """
    dr1 = DemandResponse(WILDCARD, 1000, 100, "DR100")
    dr2 = DemandResponse(WILDCARD, 1000, 500, "DR500")
    dr3 = DemandResponse(WILDCARD, 1000, 1000, "DR1000")
    return [dr1, dr2, dr3]


def _hydro():
    """
    Return a list of existing hydroelectric generators.

    >>> h = _hydro()
    >>> len(h)
    12
    """
    hydro24 = Hydro(24, 42.5, label='poly 24 hydro')
    hydro31 = Hydro(31, 43, label='poly 31 hydro')
    hydro35 = Hydro(35, 71, label='poly 35 hydro')
    hydro36 = Hydro(36, 2513.9, label='poly 36 hydro')
    hydro38 = Hydro(38, 450, label='poly 38 hydro')
    hydro39 = Hydro(39, 13.8, label='poly 39 hydro')
    hydro40 = Hydro(40, 586.6, label='poly 40 hydro')
    hydro41 = Hydro(41, 280, label='poly 41 hydro')
    hydro42 = Hydro(42, 590.4, label='poly 42 hydro')
    hydro43 = Hydro(43, 462.5, label='poly 43 hydro')

    # Pumped hydro
    # QLD: Wivenhoe (http://www.csenergy.com.au/content-%28168%29-wivenhoe.htm)
    psh17 = PumpedHydro(17, 500, 5000, label='poly 17 pumped-hydro')
    # NSW: Tumut 3 (6x250), Bendeela (2x80) and Kangaroo Valley (2x40)
    psh36 = PumpedHydro(36, 1740, 15000, label='poly 36 pumped-hydro')
    return [psh17, psh36] + \
        [hydro24, hydro31, hydro35, hydro36, hydro38, hydro39] + \
        [hydro40, hydro41, hydro42, hydro43]


def replacement(context):
    """
    Replace the current NEM fleet, more or less.

    >>> c = type('context', (), {})
    >>> replacement(c)
    >>> len(c.generators)
    14
    """
    context.generators = \
        [Black_Coal(WILDCARD, 0)] + _hydro() + [OCGT(WILDCARD, 0)]


def _one_ccgt(context):
    """
    One CCGT only.

    >>> c = type('context', (), {})
    >>> _one_ccgt(c)
    >>> len(c.generators)
    1
    """
    context.generators = [CCGT(WILDCARD, 0)]


def ccgt(context):
    """
    All gas scenario.

    >>> c = type('context', (), {})
    >>> ccgt(c)
    >>> len(c.generators)
    14
    """
    context.generators = [CCGT(WILDCARD, 0)] + _hydro() + [OCGT(WILDCARD, 0)]


def ccgt_ccs(context):
    """
    CCGT CCS scenario.

    >>> c = type('context', (), {})
    >>> ccgt_ccs(c)
    >>> len(c.generators)
    14
    """
    # pylint: disable=redefined-outer-name
    ccgt = CCGT_CCS(WILDCARD, 0)
    ocgt = OCGT(WILDCARD, 0)
    context.generators = [ccgt] + _hydro() + [ocgt]


def coal_ccs(context):
    """
    Coal CCS scenario.

    >>> c = type('context', (), {})
    >>> coal_ccs(c)
    >>> len(c.generators)
    14
    """
    coal = Coal_CCS(WILDCARD, 0)
    ocgt = OCGT(WILDCARD, 0)
    context.generators = [coal] + _hydro() + [ocgt]


def re100(context):
    """
    100% renewable electricity.

    >>> c = type('context', (), {})
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
            result += [h for h in _hydro() if not isinstance(h, PumpedHydro)]
        elif g in [Biofuel, PV1Axis, CentralReceiver, Wind]:
            for poly in range(1, 44):
                if g == Biofuel:
                    result.append(g(poly, 0, label='polygon %d GT' % poly))
                elif g == PV1Axis:
                    cfg = configfile.get('generation', 'pv1axis-trace')
                    result.append(g(poly, 0, cfg, poly - 1,
                                    build_limit=pv_limit[poly],
                                    label='polygon %d PV' % poly))
                elif g == CentralReceiver:
                    cfg = configfile.get('generation', 'cst-trace')
                    result.append(g(poly, 0, 2, 6, cfg, poly - 1,
                                    build_limit=cst_limit[poly],
                                    label='polygon %d CST' % poly))
                elif g == Wind:
                    cfg = configfile.get('generation', 'wind-trace')
                    result.append(g(poly, 0, cfg, poly - 1,
                                    build_limit=wind_limit[poly],
                                    label='polygon %d wind' % poly))
    context.generators = result


def re100_batteries(context):
    """
    Use lots of renewables plus battery storage.

    >>> c = type('context', (), {})
    >>> c.generators = []
    >>> re100_batteries(c)
    >>> len(c.generators)
    185
    """
    re100(context)
    # discharge between 6pm and 6am daily
    hrs = list(range(0, 7)) + list(range(18, 24))
    battery = Battery(WILDCARD, 0, 0, discharge_hours=hrs)
    context.generators.insert(0, battery)


def _one_per_poly(region):
    """
    Return three lists of wind, PV and CST generators, one per polygon.

    >>> from nemo import regions
    >>> wind, pv, cst = _one_per_poly(regions.tas)
    >>> len(wind), len(pv), len(cst)
    (4, 4, 4)
    """
    pv = []
    wind = []
    cst = []

    wind_cfg = configfile.get('generation', 'wind-trace')
    pv_cfg = configfile.get('generation', 'pv1axis-trace')
    cst_cfg = configfile.get('generation', 'cst-trace')

    for poly in region.polygons:
        wind.append(Wind(poly, 0, wind_cfg,
                         poly - 1,
                         build_limit=wind_limit[poly],
                         label='poly %d wind' % poly))
        pv.append(PV1Axis(poly, 0, pv_cfg,
                          poly - 1,
                          build_limit=pv_limit[poly],
                          label='poly %d PV' % poly))
        cst.append(CentralReceiver(poly, 0, 2.5, 8, cst_cfg,
                                   poly - 1,
                                   build_limit=cst_limit[poly],
                                   label='poly %d CST' % poly))
    return wind, pv, cst


def re100_one_region(context, region):
    """
    100% renewables in one region only.

    >>> from nemo import regions
    >>> c = type('context', (), {})
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
                isinstance(g, Hydro) and g.region() is region]
    newlist += cst
    newlist += [g for g in context.generators if
                isinstance(g, Biofuel) and g.region() is region]
    context.generators = newlist


def re_plus_ccs(context):
    """
    Mostly renewables with fossil and CCS augmentation.

    >>> c = type('context', (), {})
    >>> c.generators = []
    >>> re_plus_ccs(c)
    >>> len(c.generators)
    185
    """
    re100(context)
    coal = Black_Coal(WILDCARD, 0)
    # pylint: disable=redefined-outer-name
    coal_ccs = Coal_CCS(WILDCARD, 0)
    # pylint: disable=redefined-outer-name
    ccgt = CCGT(WILDCARD, 0)
    ccgt_ccs = CCGT_CCS(WILDCARD, 0)
    ocgt = OCGT(WILDCARD, 0)
    context.generators = [coal, coal_ccs, ccgt, ccgt_ccs] + \
        context.generators[:-4] + [ocgt]


def re_plus_fossil(context):
    """
    Mostly renewables with some fossil augmentation.

    >>> c = type('context', (), {})
    >>> c.generators = []
    >>> re_plus_fossil(c)
    >>> len(c.generators)
    183
    """
    re100(context)
    context.generators = \
        [Black_Coal(WILDCARD, 0), CCGT(WILDCARD, 0)] + \
        context.generators[:-4] + [OCGT(WILDCARD, 0)]


def re100_dsp(context):
    """
    Mostly renewables with demand side participation.

    >>> c = type('context', (), {})
    >>> c.generators = []
    >>> re100_dsp(c)
    >>> len(c.generators)
    187
    >>> isinstance(c.generators[-1], DemandResponse)
    True
    """
    re100(context)
    context.generators += _demand_response()


def re100_nocst(context):
    """
    100% renewables, but no CST.

    >>> c = type('context', (), {})
    >>> re100_nocst(c)
    >>> for g in c.generators: assert not isinstance(g, CST)
    """
    re100(context)
    newlist = [g for g in context.generators if not isinstance(g, CST)]
    context.generators = newlist


def re100_nsw(context):
    """
    100% renewables in New South Wales only.

    >>> c = type('context', (), {})
    >>> c.generators = []
    >>> re100_nsw(c)
    >>> for g in c.generators: assert g.region() is regions.nsw
    """
    re100_one_region(context, regions.nsw)


def re100_qld(context):
    """
    100% renewables in Queensland only.

    >>> c = type('context', (), {})
    >>> c.generators = []
    >>> re100_qld(c)
    >>> for g in c.generators: assert g.region() is regions.qld
    """
    re100_one_region(context, regions.qld)


def re100_south_aus(context):
    """
    100% renewables in South Australia only.

    >>> c = type('context', (), {})
    >>> c.generators = []
    >>> re100_south_aus(c)
    >>> for g in c.generators: assert g.region() is regions.sa
    """
    re100_one_region(context, regions.sa)


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
                    'replacement': replacement}
