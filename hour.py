# -*- Python -*-
# Copyright (C) 2010, 2011 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import datetime
from datetime import datetime as date


class Hour:
  def __init__(self, arg):
    origin = datetime.datetime(1998, 1, 1)
    if type(arg) == type(origin):
      # Datetime variant
      if arg.minute != 0 and arg.second != 0:
        raise ValueError
      delta = arg - origin
      self.value = int(delta.days * 24 + delta.seconds / 3600)
    elif isinstance(arg, int):
      # Int variant
      self.value = arg
    else:
      raise TypeError

  def datetime(self):
    delta = datetime.timedelta(hours=self.value)
    return datetime.datetime(1998, 1, 1) + delta

  def __repr__(self):
    return str(int(self.value))

  def __str__(self):
    return str(self.datetime().strftime('%Y-%m-%d--%H'))

  def __cmp__(self, v):
    return cmp(self.value, v)

  def __add__(self, v):
    return Hour(self.value + int(v))

  def __sub__(self, v):
    return Hour(self.value - int(v))

  def __trunc__(self):
    return self.value

# Module initialisation.
hours = []
h1 = Hour(date(2001, 7, 1))
h2 = Hour(date(2003, 6, 30, 23))
hours += range(h1, h2)

h1 = Hour(date(2003, 10, 16, 2))
h2 = Hour(date(2003, 10, 16, 19))
hours += range(h1, h2)

h1 = Hour(date(2006, 4, 16, 7))
h2 = Hour(date(2006, 4, 17, 20))
hours += range(h1, h2)

h1 = Hour(date(2006, 5, 2, 5))
h2 = Hour(date(2006, 5, 2, 21))
hours += range(h1, h2)

h1 = Hour(date(2007, 7, 22, 4))
h2 = Hour(date(2007, 7, 22, 20))
hours += range(h1, h2)

h1 = Hour(date(2009, 11, 11, 8))
h2 = Hour(date(2009, 11, 12, 18))
hours += range(h1, h2)

h1 = Hour(date(2008, 3, 13, 7))
h2 = Hour(date(2008, 3, 17, 20))
hours += range(h1, h2)

h1 = Hour(date(2008, 4, 9, 7))
h2 = Hour(date(2008, 4, 13, 21))
hours += range(h1, h2)

h1 = Hour(date(2009, 11, 15, 8))
h2 = Hour(date(2009, 11, 27, 18))
hours += range(h1, h2)

h1 = Hour(date(2009, 2, 16, 7))
h2 = Hour(date(2009, 2, 18, 20))
hours += range(h1, h2)


def missing_p(h):
  """
  Filter the most egregious sequences of 'nodata' hours that
  represent holes in the data sets, perhaps due to satellite
  transmission problems?
  """
  if isinstance(h, int):
    # scalar variant
    return h in hours
  elif isinstance(h, list):
    # list variant
    s1 = set(h)
    s2 = set(hours)
    return s1.issubset(s2)
  else:
    raise TypeError
