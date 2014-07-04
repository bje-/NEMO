# Copyright (C) 2010, 2011, 2014 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Implementation of Hour class."""

import datetime
from datetime import datetime as date


class Hour:

    """
    In the BoM gridded solar data, hour 0 is Jan 1, 1998 (UTC 00h).

    >>> h = Hour (0)
    >>> print (h)
    1998-01-01--00
    >>> dt = date(1998,1,1)
    >>> h = Hour (dt)
    >>> h
    0
    >>> h = Hour('foo')
    Traceback (most recent call last):
    ...
    TypeError
    >>> dt = date(1998,1,1,1,1)
    >>> h = Hour (dt)
    Traceback (most recent call last):
    ...
    ValueError
    """

    def __init__(self, arg):
        """Polymorphic constructor that takes two argument types, integer and datetime."""
        origin = datetime.datetime(1998, 1, 1)
        if type(arg) == type(origin):
            # Datetime variant
            if arg.minute != 0 or arg.second != 0:
                raise ValueError
            delta = arg - origin
            self.value = int(delta.days * 24 + delta.seconds / 3600)
        elif isinstance(arg, int):
            # Int variant
            self.value = arg
        else:
            raise TypeError

    def datetime(self):
        """Return the hour as a Python datetime.

        >>> h = Hour(0)
        >>> h.datetime()
        datetime.datetime(1998, 1, 1, 0, 0)
        """
        delta = datetime.timedelta(hours=self.value)
        return datetime.datetime(1998, 1, 1) + delta

    def __repr__(self):
        """Return the ordinal hour number."""
        return str(int(self.value))

    def __str__(self):
        """Format the hour as YYYY-MM-DD--HH."""
        return str(self.datetime().strftime('%Y-%m-%d--%H'))

    def __cmp__(self, v):
        """Compare v with self.

        >>> h1 = Hour(0)
        >>> h2 = Hour(date(1998,1,1))
        >>> h1 == h2
        True
        """
        return cmp(self.value, v)

    def __add__(self, v):
        """Add v hours.

        >>> Hour(0) + 2
        2
        """
        return Hour(self.value + int(v))

    def __sub__(self, v):
        """Subtract v hours.

        >>> Hour(10) - 2
        8
        """
        return Hour(self.value - int(v))

    def __trunc__(self):
        """Return ordinal value."""
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
    """Return True if hour h is missing.

    Filter the most egregious sequences of 'nodata' hours that
    represent holes in the data sets, perhaps due to satellite
    transmission problems?

    >>> missing_p(0)
    False
    >>> missing_p([0,1,2,3])
    False
    >>> h1 = Hour(date(2009, 2, 17))
    >>> h2 = Hour(date(2009, 2, 17, 2))
    >>> missing_p(range(h1,h2))
    True
    >>> missing_p('foo')
    Traceback (most recent call last):
      ...
    TypeError
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

if __name__ == '__main__':
    import doctest
    doctest.testmod()
