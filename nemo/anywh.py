# Copyright (C) 2017 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Self-scaling units."""


class anyWh():
    """
    >>> for i in range(8): print(anyWh(pow(10.23, i)))
    1 MWh
    10.23 MWh
    104.65 MWh
    1.0706 GWh
    10.952 GWh
    112.04 GWh
    1.1462 TWh
    11.725 TWh
    >>> a = anyWh(500)
    >>> int(a)
    500
    >>> float(a)
    500.0
    """
    def __init__(self, n, units='Wh'):
        self._val = float(n)
        if self._val >= pow(10, 6):
            self.units = 'T' + units
        elif self._val >= pow(10, 3):
            self.units = 'G' + units
        elif self._val >= 1:
            self.units = 'M' + units
        else:
            self.units = 'k' + units

    def _scale(self):
        if self._val >= pow(10, 6):
            return self._val / pow(10, 6)
        if self._val >= pow(10, 3):
            return self._val / pow(10, 3)
        if self._val >= 1:
            return self._val
        return self._val * pow(10, 3)

    def __int__(self):
        return int(self._val)

    def __float__(self):
        return float(self._val)

    def __str__(self):
        return '%.5g %s' % (self._scale(), self.units)
