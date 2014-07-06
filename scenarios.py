# Copyright (C) 2012, 2013, 2014 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Supply and demand side scenarios."""

import heapq
import numpy as np

import generators
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
    hydros = [hydro1, hydro2, hydro3, psh1, psh2]
    for h in hydros:
        h.setters = []
    return hydros


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
    >>> c.generators
    Traceback (most recent call last):
      ...
    AttributeError: C instance has no attribute 'generators'
    """
    pass


def re100_batteries(context):
    """Use lots of renewables plus battery storage.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = range(25)
    >>> re100_batteries(c)
    >>> len(c.generators)
    26
    """
    nsw_battery = generators.Battery(regions.nsw, 0, 0)
    g = context.generators
    context.generators = g[0:9] + [nsw_battery] + g[9:]


def re_plus_fossil(context):
    """Mostly renewables with some fossil augmentation.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = range(25)
    >>> re_plus_fossil(c)
    >>> len(c.generators)
    22
    """
    # pylint: disable=redefined-outer-name
    ccgt = generators.CCGT(regions.nsw, 0)
    ocgt = generators.OCGT(regions.nsw, 0)
    g = context.generators
    context.generators = [ccgt] + g[:-5] + [ocgt]


def re100_dsp(context):
    """Mostly renewables with demand side participation.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = range(10)
    >>> re100_dsp(c)
    >>> len(c.generators)
    13
    >>> isinstance(c.generators[-1], generators.DemandResponse)
    True
    """
    dr1 = generators.DemandResponse(regions.nsw, 2000, 300)
    dr2 = generators.DemandResponse(regions.nsw, 2000, 1000)
    dr3 = generators.DemandResponse(regions.nsw, 2000, 3000)
    g = context.generators
    context.generators = g + [dr1, dr2, dr3]


def re100_geothermal(context):
    """100% renewables plus geothermal.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = range(10)
    >>> re100_geothermal(c)
    >>> len(c.generators)
    7
    >>> isinstance(c.generators[0], generators.Geothermal)
    True
    """
    geo = generators.Geothermal(regions.sa, 0)
    g = context.generators
    context.generators = [geo] + g[:-4]


def theworks(context):
    """All technologies.

    >>> class C: pass
    >>> c = C()
    >>> c.generators = range(10)
    >>> theworks(c)
    >>> len(c.generators)
    14
    """
    # pylint: disable=redefined-outer-name
    geo = generators.Geothermal(regions.nsw, 0)
    coal = generators.Black_Coal(regions.nsw, 0)
    coal_ccs = generators.Coal_CCS(regions.nsw, 0)
    ccgt = generators.CCGT(regions.nsw, 0)
    ccgt_ccs = generators.CCGT_CCS(regions.nsw, 0)
    ocgt = generators.OCGT(regions.nsw, 0)
    batt = generators.Battery(regions.nsw, 0, 0)
    dem = generators.DemandResponse(regions.nsw, 0, 300)
    g = context.generators
    context.generators = [geo, coal, coal_ccs, ccgt, ccgt_ccs] + g[:-4] + [ocgt, batt, dem]

supply_scenarios = {'re100': re100,
                    'ccgt': ccgt,
                    'ccgt-ccs': ccgt_ccs,
                    'coal-ccs': coal_ccs,
                    're100+batteries': re100_batteries,
                    'replacement': replacement,
                    're100+dsp': re100_dsp,
                    're100+geoth': re100_geothermal,
                    're+fossil': re_plus_fossil,
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
            # label form: "roll:X" rolls the load by X hours
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
    Roll demand by posns hours.

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
