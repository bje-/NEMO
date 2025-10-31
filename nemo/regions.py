# Copyright (C) 2011, 2014 Ben Elliston
# Copyright (C) 2014, 2015 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Market regions consisting of one or more polygons."""


class Region:
    """Each region is described by a Region object."""

    def __init__(self, ordinal, regionid, descr):
        """Construct a Region given an ordinal, region ID and description.

        >>> r = Region(0, 'cbr', 'Capital region')
        """
        self.id = regionid
        self.descr = descr
        self.num = ordinal
        self.polygons = None

    def __repr__(self):
        """Return region code."""
        return self.id

    def __index__(self):
        """Return region number."""
        return self.num

    def __copy__(self):
        """Prevent copying."""
        return self

    def __deepcopy__(self, _):
        """Prevent deepcopying."""
        return self


NSW = Region(0, 'NSW1', 'New South Wales')
QLD = Region(1, 'QLD1', 'Queensland')
SA = Region(2, 'SA1', 'South Australia')
SNOWY = Region(3, 'SNOWY1', 'Snowy Mountains')
TAS = Region(4, 'TAS1', 'Tasmania')
VIC = Region(5, 'VIC1', 'Victoria')
ALL = [NSW, QLD, SA, SNOWY, TAS, VIC]
NUMREGIONS = len(ALL)
