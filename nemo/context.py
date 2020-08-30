# Copyright (C) 2011, 2012, 2014 Ben Elliston
# Copyright (C) 2014, 2015, 2016 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""
A simulation context encapsulates all simulation state ensuring that
there is never any residual state left behind after a simulation
run. It also allows multiple contexts to be compared after individual
simulation runs.
"""

import re

import json
import numpy as np
import pandas as pd
import pint

from nemo import configfile
from nemo import costs
from nemo import generators
from nemo import regions
from nemo import polygons

from nemo.nem import startdate
from nemo.nem import hourly_regional_demand
from nemo.nem import hourly_demand

ureg = pint.UnitRegistry()
ureg.default_format = '.2f~P'


class Context():

    """All simulation state is kept in a Context object."""

    def __init__(self):
        """Initialise a default context."""
        self.verbose = False
        self.track_exchanges = False
        self.regions = regions.All
        self.startdate = startdate
        # Number of timesteps is determined by the number of demand rows.
        self.hours = len(hourly_regional_demand)
        # Estimate the number of years from the number of simulation hours.
        if self.hours == 8760 or self.hours == 8784:
            self.years = 1
        else:
            self.years = self.hours / (365.25 * 24)

        self.relstd = 0.002  # 0.002% unserved energy
        self.generators = [generators.CCGT(polygons.wildcard, 20000),
                           generators.OCGT(polygons.wildcard, 20000)]
        self.demand = hourly_demand.copy()
        self.timesteps = len(self.demand)
        self.spill = pd.DataFrame()
        self.generation = pd.DataFrame()
        self.unserved = pd.DataFrame()
        # System non-synchronous penetration limit
        self.nsp_limit = float(configfile.get('limits', 'nonsync-penetration'))
        self.exchanges = np.zeros((self.hours, polygons.numpolygons, polygons.numpolygons))
        self.costs = costs.NullCosts()

    def total_demand(self):
        """Return the total demand from the data frame."""
        return self.demand.values.sum()

    def unserved_energy(self):
        """Return the total unserved energy."""
        return self.unserved.values.sum()

    def surplus_energy(self):
        """Return total surplus energy."""
        return self.spill.values.sum()

    def unserved_percent(self):
        """Return the total unserved energy as a percentage of total demand.

        >>> import pandas as pd
        >>> c = Context()
        >>> c.unserved_percent()
        0.0
        >>> c.demand = pd.DataFrame()
        >>> c.unserved_percent()
        nan
        """
        # We can't catch ZeroDivision because numpy emits a warning
        # (which we would rather not suppress).
        if self.total_demand() == 0:
            return np.nan
        return self.unserved_energy() / self.total_demand() * 100

    def add_exchange(self, hour, src, dest, transfer):
        """Record an energy transfer from src to dest in given hour."""
        self.exchanges[hour, src - 1, dest - 1] += transfer

    def set_capacities(self, caps):
        """Set generator capacities from a list."""
        n = 0
        for gen in self.generators:
            for (setter, min_cap, max_cap) in gen.setters:
                # keep parameters within bounds
                newval = max(min(caps[n], max_cap), min_cap)
                setter(newval)
                n += 1
        # Check every parameter has been set.
        assert n == len(caps), '%d != %d' % (n, len(caps))

    def __str__(self):
        """A human-readable representation of the context."""
        s = ""
        if self.regions != regions.All:
            s += 'Regions: ' + str(self.regions) + '\n'
        if self.verbose:
            s += 'Generators:' + '\n'
            for g in self.generators:
                s += '\t' + str(g)
                summary = g.summary(self)
                if summary is not None:
                    s += '\n\t   ' + summary + '\n'
                else:
                    s += '\n'
        s += 'Timesteps: %d h\n' % self.hours
        total_demand = (self.total_demand() * ureg.MWh).to_compact()
        s += 'Demand energy: {}\n'.format(total_demand)
        surplus_energy = (self.surplus_energy() * ureg.MWh).to_compact()
        s += 'Unused surplus energy: {}\n'.format(surplus_energy)
        if self.surplus_energy() > 0:
            spill_series = self.spill[self.spill.sum(axis=1) > 0]
            s += 'Timesteps with unused surplus energy: %d\n' % len(spill_series)

        if self.unserved.empty:
            s += 'No unserved energy'
        else:
            s += 'Unserved energy: %.3f%%' % self.unserved_percent() + '\n'
            if self.unserved_percent() > self.relstd * 1.001:
                s += 'WARNING: reliability standard exceeded\n'
            s += 'Unserved total hours: ' + str(len(self.unserved)) + '\n'

            # A subtle trick: generate a date range and then substract
            # it from the timestamps of unserved events.  This will
            # produce a run of time detlas (for each consecutive hour,
            # the time delta between this timestamp and the
            # corresponding row from the range will be
            # constant). Group by the deltas.
            rng = pd.date_range(self.unserved.index[0], periods=len(self.unserved.index), freq='H')
            unserved_events = [k for k, g in self.unserved.groupby(self.unserved.index - rng)]
            s += 'Number of unserved energy events: ' + str(len(unserved_events)) + '\n'
            if not self.unserved.empty:
                usmin = (self.unserved.min() * ureg.MW).to_compact()
                usmax = (self.unserved.max() * ureg.MW).to_compact()
                s += 'Shortfalls (min, max): ({}, {})'.format(usmin, usmax)
        return s

    class JSONEncoder(json.JSONEncoder):
        """A custom encoder for Context objects."""
        def default(self, o):
            if isinstance(o, Context):
                result = []
                for g in o.generators:
                    tech = re.sub(r"<class 'generators\.(.*)'>",
                                  r'\1', str(type(g)))
                    result += [{'label': g.label, 'polygon': g.polygon,
                                'capacity': g.capacity, 'technology': tech}]
                return result
            return None
