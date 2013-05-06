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
  def __init__ (self, (arg1,arg2)):
    if type (arg1) == type (1.) and type (arg2) == type (1.):
      # Pair of floats
      self._lat = arg1
      self._lon = arg2
    elif type (arg1) == type (1) and type (arg2) == type (1):
      # Pair of ints
      self._lat = yllcorner + cellsize * (maxrows - arg1)
      self._lon = xllcorner + cellsize * arg2
    else:
      raise TypeError

  def xy (self):
    col = int ((self._lon - xllcorner) / cellsize)
    assert col < maxcols
    row = int (maxrows - ((self._lat - yllcorner) / cellsize)) - 1
    assert row >= 0
    return row, col

  def distance (self, another):
    "Compute the distance between this lat/long and another."
    # Code adapted from Chris Veness
    R = 6371 # km
    dlat = math.radians (another._lat - self._lat)
    dlon = math.radians (another._lon - self._lon)
    lat1 = math.radians (self._lat)
    lat2 = math.radians (another._lat)
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.sin(dlon/2) * math.sin(dlon/2) * math.cos(lat1) * math.cos(lat2)
    c = 2 * math.atan2 (math.sqrt (a), math.sqrt(1-a))
    return R * c

  def __repr__ (self):
    return self.__str__ ()

  def __str__ (self):
    return '(' + str (self._lat) + ', ' + str (self._lon) + ')'

class BoundingBox:
  def __init__ (self, (ll, ur)):
    self._lowleft = ll
    self._upright = ur
    assert self._lowleft._lon <= self._upright._lon
    assert self._lowleft._lat <= self._upright._lat

  def contains_p (self, coord):
    return (coord._lat >= self._lowleft._lat and \
              coord._lat <= self._upright._lat) and \
              (coord._lon >= self._lowleft._lon and \
                 coord._lon <= self._upright._lon)

  def slice (self):
    ll = _lowleft.xy ()
    ur = _upright.xy ()
    s1 = slice (ur[0], ll[0])
    s2 = slice (ll[1], ur[1])
    return s1, s2

  def __repr__ (self):
    return self.__str__ ()

  def __str__ (self):
    return '(' + str (self._lowleft) + ', ' + str (self._upright) + ')'    
