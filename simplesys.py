# -*- Python -*-
# Copyright (C) 2012, 2014 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# Notes:
# (1) Think of QA as "unmet load" rather than "auxiliary".

"""
A reimplementation of the SIMPLESYS solar thermal system model.

See http://www.powerfromthesun.net/simplesys.html
"""


def _alert(message):
    """
    Print a message on the console.

    >>> _alert('Hello')
    Hello
    """
    print message


class Context:

    """The SIMPLESYS model state is held in a Context object."""

    def __init__(self, ep=0, qf=0, sl=0, sm=0):
        """
        Construct a SIMPLESYS context containing system state.

        >>> c = Context()
        """
        self.EP = ep
        self.QF = qf
        self.SL = sl
        self.SM = sm

        # Start at hour zero.
        # Each call to calculate advances one hour.
        self.HR = 0

        # Initial storage energy
        self.ES = 0

        # When to start and stop (hour)
        self.ISTART = 0
        self.SHUT = 24

        self.SU = 0
        self.ZS = 0

        # Partially define here. As NoneType variables, if they are
        # used before being defined, an exception will be raised.
        self.MODE = None
        self.QS = None
        self.QA = None
        self.QC = None
        self.QD = None

    def __repr__(self):
        """A compact representation of the object state.

        >>> c = Context()
        >>> c
        HR=0 ES=0 ZS=0 SU=0 ISTART=0 SHUT=24 QF=0 SL=0 SM=0
        """
        s = 'HR=%d ES=%d ZS=%d SU=%d ISTART=%d SHUT=%d QF=%d SL=%d SM=%d' % \
            (self.HR, self.ES, self.ZS, self.SU, self.ISTART, self.SHUT, self.QF, self.SL, self.SM)
        return s

    def reset(self):
        """
        Reset the object state.

        >>> c = Context ()
        >>> c.reset()
        """
        self.HR = 0
        self.ES = 0
        self.ZS = 0
        self.SU = 0

    def collectorOutput(self):
        """Calculate collector field output."""
        x = self.COLLECTOR[self.HR] - self.QF
        self.QC = 0 if x < 0 else x

    def startupEnergy(self):
        """Absorb some collector output to start up."""
        if self.SU < self.EP:
            self.SU = self.SU + self.QC
            if self.SU < self.EP:
                self.QC = 0
            else:
                self.QC = self.SU - self.EP

    def storageLoss(self):
        """Account for storage heat loss."""
        if self.ES > 0:
            # Energy accumulated in storage. Not zeroed at end of day
            self.ES = self.ES - self.SL
            # Energy lost from storage over the day.  Zeroed at end of day
            self.ZS = self.ZS - self.SL

    def storageInput(self, heatRate):
        """Accept heat from an auxiliary source."""
        self.ES = min(self.ES + heatRate, self.SM)
        if self.ES + heatRate > self.SM:
            return self.ES + heatRate - self.SM
        else:
            return 0

    def controlLogic(self, QL):
        """The logic that controls system mode changes.

        This is described at:
        http://powerfromthesun.net/Book/chapter14/chapter14.html
        """
        self.QA = 0
        self.QS = 0
        self.QD = 0

        if self.QC > 0:
            if self.QC > QL:
                if self.ES > self.SM:
                    self.QD = self.QC - QL
                    self.MODE = 4
                else:
                    self.QS = self.QC - QL
                    self.MODE = 3
                    if (self.ES + self.QS) > self.SM:
                        self.QD = self.ES + self.QS - self.SM
                        self.QS = self.QS - self.QD
                        self.MODE = 3.4
            else:
                if self.ES > 0:
                    self.QS = self.QC - QL
                    self.MODE = 5
                    if (self.ES + self.QS) <= 0:
                        self.QS = -self.ES
                        self.QA = QL + self.QS - self.QC
                        self.MODE = 5.1
                else:
                    self.QA = QL - self.QC
                    self.MODE = 2
        else:
            if self.ES > 0:
                self.QS = -QL
                self.MODE = 6
                if (self.ES + self.QS) <= 0:
                    self.QS = -self.ES
                    self.QA = QL + self.QS - self.QC
                    self.MODE = 6.1
            else:
                self.QA = QL
                self.MODE = 1
        if QL <= 0:
            self.MODE = 0

    def validate(self):
        """
        Call to validate the object state.

        >>> obj = Context()
        >>> obj.validate()	# valid, no output
        >>> obj.EP = -1
        >>> obj.validate()
        Energy to heat-up piping must be positive!
        >>> obj = Context()
        >>> obj.ISTART = 12
        >>> obj.SHUT = 8
        >>> obj.validate()
        Shutdown time must be greater than Start time
        """
        if self.EP < 0:
            _alert("Energy to heat-up piping must be positive!")
        if self.QF < 0:
            _alert("Field piping heat loss must be positive!")
        if self.SM < 0:
            _alert("Maximum storage capacity must be positive!")
        if self.ES < 0:
            _alert("Energy in storage must be positive!")
        if self.SL < 0:
            _alert("Storage heat loss must be positive!")
        if self.ISTART < 0 or self.ISTART > 23:
            _alert("Start time must be between 0 and 23!")
        if self.SHUT < 0 or self.SHUT > 24:
            _alert("Shutdown time must be between 0 and 24!")
        if self.SHUT < self.ISTART:
            _alert("Shutdown time must be greater than Start time")

    def nexthour(self, load):
        """
        Advance the context by one hour.

        >>> import numpy
        >>> coll = numpy.zeros (10)
        >>> c = Context()
        >>> c.COLLECTOR = coll
        >>> c.nexthour(10)
        {'QA': 10, 'QC': 0.0, 'T': 0, 'MODE': 1, 'QL': 10, 'QS': 0, 'ES': 0, 'QD': 0}
        >>> c.nexthour(10)
        {'QA': 10, 'QC': 0.0, 'T': 1, 'MODE': 1, 'QL': 10, 'QS': 0, 'ES': 0, 'QD': 0}
        """
        T = self.HR % 24

        if T == 0:
            # New day, reset.
            self.ZS = 0
            self.SU = 0

        self.collectorOutput()
        self.startupEnergy()
        self.storageLoss()
        rQL = load if (T >= self.ISTART or T < self.SHUT) else 0
        self.controlLogic(rQL)

        self.ES += self.QS
        self.ZS += self.QS
        self.HR += 1

        return {'T': T, 'QC': self.QC, 'QA': self.QA, 'QS': self.QS,
                'ES': self.ES, 'QD': self.QD, 'QL': rQL, 'MODE':
                self.MODE}

if __name__ == '__main__':
    import doctest
    doctest.testmod()
