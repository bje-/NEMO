# Copyright (C) 2011, 2014 Ben Elliston
# Copyright (C) 2014, 2015 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Regions and their interconnections."""
import string

import numpy as np

from latlong import LatLong


class Region:

    """Each region is described by a Region object."""

    def __init__(self, count, regionid, descr, (centreLat, centreLon)):
        """
        Construct a Region given a count, region ID, description and lat/long of the region's centre.

        >>> r = Region(0, 'cbr', 'Capital region', ((-35, 149)))
        """
        self.id = regionid
        self.descr = descr
        self.centre = LatLong(centreLat, centreLon)
        self.num = count

    def __repr__(self):
        """
        Return region code.

        >>> r = Region(1, 'QLD1', 'Queensland', ((-22, 144)))
        >>> r
        QLD1
        """
        return self.id

    def __index__(self):
        """
        Return region number.

        >>> r = Region(1, 'QLD1', 'Queensland', ((-22, 144)))
        >>> x = [0,1,2,3,4]
        >>> x[r]
        1
        """
        return self.num

# Centres taken from:
# http://www.ga.gov.au/education/geoscience-basics/dimensions/
nsw = Region(0, 'NSW1', 'New South Wales', (-32.1633, 147.0166))
qld = Region(1, 'QLD1', 'Queensland', (-22.4869, 144.4316))
sa = Region(2, 'SA1', 'South Australia', (-30.0583, 135.7633))
snowy = Region(3, 'SNOWY1', 'Snowy Mountains', (-36.2200, 148.1269))
tas = Region(4, 'TAS1', 'Tasmania', (-42.0213, 146.5933))
vic = Region(5, 'VIC1', 'Victoria', (-36.8541, 144.2811))
All = [nsw, qld, sa, snowy, tas, vic]
numregions = len(All)


def find(s):
    """
    Return the first region object matching the substring s.

    >>> find('NS')
    NSW1
    >>> find('QP')
    Traceback (most recent call last):
      ...
    ValueError
    """
    for r in All:
        if string.find(r.id, s) == 0:
            return r
    raise ValueError

# Node connectivity is expressed using a 2-D list.
connections = {}
for src in All:
    for dest in All:
        if src is dest:
            # An empty list is used for the path from a region to
            # itself (so that the path length is 0).
            connections[(src, dest)] = []
        else:
            # Some of these (eg. QLD -> SA) are overwritten using the
            # exceptional cases below.
            connections[(src, dest)] = [(src, dest)]

# Enumerate the indirect cases by hand. There's not too many of them.
connections[(qld, sa)] = [(qld, nsw), (nsw, vic), (vic, sa)]
connections[(qld, vic)] = [(qld, nsw), (nsw, vic)]
connections[(qld, tas)] = [(qld, nsw), (nsw, vic), (vic, tas)]
connections[(sa, nsw)] = [(sa, vic), (vic, nsw)]
connections[(sa, tas)] = [(sa, vic), (vic, tas)]
connections[(tas, nsw)] = [(tas, vic), (vic, nsw)]
connections[(qld, sa)] = [(qld, sa)]
connections[(sa, nsw)] = [(sa, nsw)]

# And the reverse direction.
for (src, dest) in [(qld, sa), (qld, vic), (qld, tas), (sa, nsw),
                    (sa, tas), (tas, nsw)]:
    connections[dest, src] = []
    for (a, b) in connections[(src, dest)][::-1]:
        connections[dest, src].append((b, a))

# Distances between regions.
# For this, we use the centre of each region as an approximation.
# This strikes a balance between likely renewable sites and loads.

distances = np.empty((numregions, numregions))
for rgn1 in All:
    for rgn2 in All:
        distances[rgn1.num, rgn2.num] = rgn1.centre.distance(rgn2.centre)


def path(regiona, regionb):
    """
    Return a path from region A to region B.

    >>> path(nsw,qld)
    [(NSW1, QLD1)]
    >>> path(sa,tas)
    [(SA1, VIC1), (VIC1, TAS1)]
    """
    return connections[(regiona, regionb)]


def direct_p(regiona, regionb):
    """
    Return True if region A and B are directly connected.

    >>> direct_p(nsw,qld)
    True
    >>> direct_p(qld,tas)
    False
    """
    return len(path(regiona, regionb)) <= 1


def in_regions_p(rpath, rgnset):
    """
    Ensure every region in rpath is in rgnset.

    >>> in_regions_p([(nsw, vic)], All)
    True
    >>> in_regions_p([(qld,nsw), (nsw,vic), (vic,tas)], [vic, nsw, sa])
    False
    """
    if len(rpath) > 0:
        for (source, destn) in rpath:
            if source not in rgnset or destn not in rgnset:
                return False
    return True
