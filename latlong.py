# latlong.py: latitude and longitude support
# Copyright (C) 2010, 2011 Ben Elliston
#
# Latitude/longitude spherical geodesy formulae & scripts (C) Chris Veness 2002-2011
# (www.movable-type.co.uk/scripts/latlong.html)
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

cellsize = 0.05
xllcorner = 112.025
yllcorner = -43.925
maxcols = 839
maxrows = 679

import math


class LatLong:
    def __init__(self, (arg1, arg2)):
        if isinstance(arg1, float) and isinstance(arg2, float):
            # Pair of floats
            self.lat = arg1
            self.lon = arg2
        elif isinstance(arg1, int) and isinstance(arg2, int):
            # Pair of ints
            self.lat = yllcorner + cellsize * (maxrows - arg1)
            self.lon = xllcorner + cellsize * arg2
        else:
            raise TypeError

    def xy(self):
        col = int((self.lon - xllcorner) / cellsize)
        assert col < maxcols
        row = int(maxrows - ((self.lat - yllcorner) / cellsize)) - 1
        assert row >= 0
        return row, col

    def distance(self, another):
        "Compute the distance between this lat/long and another."
        # Code adapted from Chris Veness
        R = 6371  # km
        dlat = math.radians(another.lat - self.lat)
        dlon = math.radians(another.lon - self.lon)
        lat1 = math.radians(self.lat)
        lat2 = math.radians(another.lat)
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + \
            math.sin(dlon / 2) * math.sin(dlon / 2) * math.cos(lat1) * math.cos(lat2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '(' + str(self.lat) + ', ' + str(self.lon) + ')'


class BoundingBox:
    def __init__(self, (ll, ur)):
        self._lowleft = ll
        self._upright = ur
        assert self._lowleft.lon <= self._upright.lon
        assert self._lowleft.lat <= self._upright.lat

    def contains_p(self, coord):
        return (coord.lat >= self._lowleft.lat and
                coord.lat <= self._upright.lat) and \
            (coord.lon >= self._lowleft.lon and
             coord.lon <= self._upright.lon)

    def slice(self):
        ll = _lowleft.xy()
        ur = _upright.xy()
        s1 = slice(ur[0], ll[0])
        s2 = slice(ll[1], ur[1])
        return s1, s2

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '(' + str(self._lowleft) + ', ' + str(self._upright) + ')'
