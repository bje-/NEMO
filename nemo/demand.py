# Copyright (C) 2021 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Demand side scenarios."""

import numpy as np
import pandas as pd


def roll(label):
    """roll:X rolls the load by X timesteps.

    >>> roll("roll:3")  # doctest: +ELLIPSIS
    <function roll.<locals>.<lambda> at ...>
    >>> roll("junk string")
    Traceback (most recent call last):
    AssertionError
    """
    assert label.startswith('roll:')

    # label form: "roll:X" rolls the load by X timesteps
    _, posns = label.split(':')
    posns = int(posns)
    return lambda context: _roll_demand(context, posns)


def scale(label):
    """scale:X scales all of the load uniformly by X%.

    >>> scale("scale:10")  # doctest: +ELLIPSIS
    <function scale.<locals>.<lambda> at ...>
    >>> scale("junkstring")
    Traceback (most recent call last):
    AssertionError
    """
    assert label.startswith('scale:')

    _, factor = label.split(':')
    factor = 1 + float(factor) / 100
    return lambda context: _scale_demand_by(context, factor)


def scalex(label):
    """scalex:H1:H2:X scales hours H1 to H2 by X%.

    >>> scalex("scalex:8:12:10")  # doctest: +ELLIPSIS
    <function scalex.<locals>.<lambda> at ...>
    >>> scalex("scalex:10:30:5")
    Traceback (most recent call last):
    ValueError: hour > 24
    >>> scalex("scalex:12:8:5")
    Traceback (most recent call last):
    ValueError: to_hour comes before from_hour
    >>> scalex("junkstring")
    Traceback (most recent call last):
    AssertionError
    """
    assert label.startswith('scalex:')

    _, hour1, hour2, factor = label.split(':')
    from_hour = int(hour1)
    to_hour = int(hour2)
    if from_hour < 0 or to_hour < 0:
        raise ValueError("hour < 0")
    if from_hour > 24 or to_hour > 24:
        raise ValueError("hour > 24")
    if to_hour <= from_hour:
        raise ValueError("to_hour comes before from_hour")
    factor = 1 + float(factor) / 100
    return lambda context: _scale_range_demand(context,
                                               from_hour, to_hour, factor)


def scaletwh(label):
    """scaletwh:N scales demand to N TWh.

    >>> scaletwh("scaletwh:100")  # doctest: +ELLIPSIS
    <function scaletwh.<locals>.<lambda> at ...>
    >>> scaletwh("junkstring")
    Traceback (most recent call last):
    AssertionError
    """
    assert label.startswith('scaletwh:')

    _, val = label.split(':')
    new_demand = float(val)
    return lambda context: _scale_demand_twh(context, new_demand)


def shift(label):
    """shift:N:H1:H2 shifts N MW of daily load from H1 to H2.

    >>> shift("shift:3:10:14")  # doctest: +ELLIPSIS
    <function shift.<locals>.<lambda> at ...>
    >>> shift("junkstring")
    Traceback (most recent call last):
    AssertionError
    """
    assert label.startswith('shift:')
    _, demand, hour1, hour2 = label.split(':')
    demand = int(demand)
    from_hour = int(hour1)
    to_hour = int(hour2)
    if from_hour < 0 or to_hour < 0:
        raise ValueError("hour < 0")
    if from_hour > 24 or to_hour > 24:
        raise ValueError("hour > 24")
    return lambda context: _shift_demand(context, demand, from_hour, to_hour)


def peaks(label):
    """peaks:N:X reduces demand peaks over N MW by X%.

    >>> peaks("peaks:5:10")  # doctest: +ELLIPSIS
    <function peaks.<locals>.<lambda> at ...>
    >>> peaks("junkstring")
    Traceback (most recent call last):
    AssertionError
    """
    assert label.startswith('peaks:')
    _, power, factor = label.split(':')
    power = int(power)
    factor = 1 + float(factor) / 100
    return lambda context: _scale_peaks(context, power, factor)


def npeaks(label):
    """npeaks:N:X adjusts top N demand peaks by X%.

    >>> npeaks("npeaks:5:10")  # doctest: +ELLIPSIS
    <function npeaks.<locals>.<lambda> at ...>
    >>> npeaks("junkstring")
    Traceback (most recent call last):
    AssertionError
    """
    assert label.startswith('npeaks:')
    _, topn, factor = label.split(':')
    topn = int(topn)
    factor = 1 + float(factor) / 100
    return lambda context: _scale_npeaks(context, topn, factor)


def unchanged(_):
    """No demand modification.

    >>> unchanged("any")  # doctest: +ELLIPSIS
    <function unchanged.<locals>.<lambda> at ...>
    """
    return lambda context: context


switch_table = [
    (lambda s: s == 'unchanged', unchanged),
    (lambda s: s.startswith('roll:'), roll),
    (lambda s: s.startswith('scale:'), scale),
    (lambda s: s.startswith('scalex:'), scalex),
    (lambda s: s.startswith('scaletwh:'), scaletwh),
    (lambda s: s.startswith('shift:'), shift),
    (lambda s: s.startswith('peaks:'), peaks),
    (lambda s: s.startswith('npeaks:'), npeaks),
]


# Demand modifiers
def switch(label):
    """Return a callback function to modify the demand.

    >>> switch('unchanged')	  # doctest: +ELLIPSIS
    <function ...>

    >>> switch('roll:10')  # doctest: +ELLIPSIS
    <function ...>

    >>> switch('scale:5')  # doctest: +ELLIPSIS
    <function ...>

    >>> switch('scalex:0:10:5')  # doctest: +ELLIPSIS
    <function ...>

    >>> switch('shift:100:10:12')  # doctest: +ELLIPSIS
    <function ...>

    >>> switch('shift:100:-2:12')  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ValueError: hour < 0

    >>> switch('shift:100:12:25')  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ValueError: hour > 24

    >>> switch('scalex:-1:12:20')  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ValueError: hour < 0

    >>> switch('scalex:12:25:20')  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ValueError: hour > 24

    >>> switch('scalex:20:8:20')  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ValueError: to_hour comes before from_hour

    >>> switch('peaks:10:34000')  # doctest: +ELLIPSIS
    <function ...>

    >>> switch('npeaks:10:5')  # doctest: +ELLIPSIS
    <function ...>

    >>> switch('foo')
    Traceback (most recent call last):
    ValueError: invalid scenario: foo
    """
    for (predicate, callback) in switch_table:
        if predicate(label):
            return callback(label)

    raise ValueError(f'invalid scenario: {label}')


def _roll_demand(context, posns):
    """
    Roll demand by posns timesteps.

    >>> c = type('context', (), {})
    >>> c.demand = pd.DataFrame(list(range(10)))
    >>> _roll_demand(c, 1)
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


def _scale_range_demand(context, from_hour, to_hour, factor):
    """
    Scale demand between from_hour and to_hour by factor%.

    >>> c = type('context', (), {})
    >>> c.demand = pd.DataFrame(list(range(10)))
    >>> _scale_range_demand(c, 0, 4, 1.2)
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


def _scale_demand_twh(context, new_demand):
    """
    Scale demand to new_demand TWh.

    >>> c = type('context', (), {})
    >>> c.demand = pd.DataFrame([100]*10)
    >>> _scale_demand_twh(c, 0.0002)
    >>> print(c.demand.loc[0])
    0    20.0
    Name: 0, dtype: float64
    """
    total_demand = context.demand.values.sum()
    new_demand *= 10 ** 6
    context.demand *= new_demand / total_demand


def _scale_demand_by(context, factor):
    """
    Scale demand by factor%.

    >>> c = type('context', (), {})
    >>> c.demand = pd.DataFrame([0, 1, 2])
    >>> _scale_demand_by(c, 1.2)
    >>> print(c.demand)
         0
    0  0.0
    1  1.2
    2  2.4
    """
    context.demand *= factor


def _shift_demand(context, demand, from_hour, to_hour):
    """Move n MW of demand from from_hour to to_hour.

    >>> from nemo import context, regions
    >>> ctx = context.Context()
    >>> ctx.regions = [regions.sa]
    >>> ctx.demand = np.zeros((43, 24 * 7))
    >>> ctx.demand[26][0::24] = 100  # polygon 27
    >>> ctx.demand[31][0::24] = 100  # polygon 32
    >>> saved_sum = ctx.demand.sum()
    >>> _shift_demand(ctx, 50, 0, 12) # shift 50MW from midnight to noon
    >>> assert ctx.demand.sum() == saved_sum  # verify no change
    >>> ctx.demand[26][0], ctx.demand[26][12]  # 5MW -> noon
    (95.0, 5.0)
    >>> ctx.demand[31][0], ctx.demand[31][12]  # 45MW -> noon
    (55.0, 45.0)
    """
    # Shift demand within in each polygon
    for poly in range(43):
        for regn in context.regions:
            if poly + 1 in regn.polygons:
                weight = regn.polygons[poly + 1]
                if context.demand[poly].sum() > 0:
                    context.demand[poly, from_hour::24] -= demand * weight
                    context.demand[poly, to_hour::24] += demand * weight
    assert np.all(context.demand >= 0), \
        f"negative load in hour {from_hour}"


def _scale_peaks(context, power, factor):
    """
    Adjust demand peaks over N megawatts by factor%.

    >>> c = type('context', (), {})
    >>> c.demand = pd.DataFrame([[0.0]*5]*5)
    >>> c.demand.loc[3] = 5000
    >>> _scale_peaks(c, 3000, 0.5)
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


def _scale_npeaks(context, topn, factor):
    """
    Adjust top N demand peaks by X%.

    >>> c = type('context', (), {})
    >>> c.demand = pd.DataFrame([[0.0]*5]*5)
    >>> c.demand.loc[3] = 5000
    >>> c.demand.loc[4] = 3000
    >>> _scale_npeaks(c, 1, 0.5)
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
