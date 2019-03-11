# Copyright (C) 2010, 2011, 2014 Ben Elliston
#
# Latitude/longitude spherical geodesy formulae and scripts are
# (C) Chris Veness 2002-2011
# (www.movable-type.co.uk/scripts/latlong.html)
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Latitude and longitude support for the BoM solar irradiance grids."""
import math


cellsize = 0.05
xllcorner = 112.025
yllcorner = -43.925
maxcols = 839
maxrows = 679


class LatLong():

    """A point of latitude and logitude."""

    def __init__(self, arg1, arg2, is_xy=False):
        """Initialise a lat/long object.

        >>> obj = LatLong(-35, 149)
        >>> obj = LatLong(1, 10, True)
        >>> obj = LatLong(1, 2, True)
        >>> obj = LatLong(679, 839, True)
        >>> obj = LatLong(839, 679, True)
        Traceback (most recent call last):
          ...
        ValueError
        >>> obj = LatLong (499, 739, True)
        >>> round(obj.lat, 3)  # round for test safety
        -34.925
        >>> round(obj.lon, 3)  # round for test safety
        148.975
        """
        if is_xy:
            if arg1 > maxrows or arg2 > maxcols:
                raise ValueError
            self.lat = yllcorner + cellsize * (maxrows - arg1)
            self.lon = xllcorner + cellsize * arg2
        else:
            self.lat = arg1
            self.lon = arg2

    def xy(self):
        """
        Return the Cartesian coordinate.

        >>> obj = LatLong(-35, 149)
        >>> obj.xy()
        (499, 739)
        >>> obj = LatLong(0, 0, True)
        >>> round(obj.lat, 3)  # round for test safety
        -9.975
        >>> round(obj.lon, 3)  # round for test safety
        112.025
        """
        col = int((self.lon - xllcorner) / cellsize)
        assert col < maxcols
        row = int(maxrows - ((self.lat - yllcorner) / cellsize)) - 1
        assert row >= 0
        return row, col

    def distance(self, another):
        """
        Compute the distance in kilometres between this position and another.

        >>> obj = LatLong (-35, 149)
        >>> obj2 = LatLong (-36, 150)
        >>> obj.distance (obj)
        0.0
        >>> print '%.1f' % obj.distance (obj2)
        143.4
        """
        # Code adapted from Chris Veness
        r = 6371  # km
        dlat = math.radians(another.lat - self.lat)
        dlon = math.radians(another.lon - self.lon)
        lat1 = math.radians(self.lat)
        lat2 = math.radians(another.lat)
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + \
            math.sin(dlon / 2) * math.sin(dlon / 2) * \
            math.cos(lat1) * math.cos(lat2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c

    def __repr__(self):
        """
        Print object representation.

        >>> obj = LatLong(-35, 149)
        >>> print obj
        (-35, 149)
        """
        return self.__str__()

    def __str__(self):
        """
        Return string representation of the object.

        >>> obj = LatLong(-35, 149)
        >>> str(obj)
        '(-35, 149)'
        """
        return '(' + str(self.lat) + ', ' + str(self.lon) + ')'
