# -*- Python -*-
# Copyright (C) 2012 Ben Elliston
#
# Adapted from SIMPLESYS, a solar thermal system model.
# http://www.powerfromthesun.net/simplesys.html
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# Notes:
# (1) Think of QA as "unmet load" rather than "auxiliary".

def _alert (message):
    print message
    
def _percent (x):
    return str (round (float (x)*100)) + '%'

class Context:
    def __init__ (self, ep=0, qf=0, sl=0, sm=0):
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

    def __repr__ (self):
        s = 'HR=%d ES=%d ZS=%d SU=%d ISTART=%d SHUT=%d QF=%d SL=%d SM=%d' % \
            (self.HR, self.ES, self.ZS, self.SU, self.ISTART, self.SHUT, self.QF, self.SL, self.SM)
        return s
    
    def reset (self):
	self.HR = 0
	self.ES = 0
        self.ZS = 0
        self.SU = 0

    def returnQL (self, QL):
	T = self.HR % 24
        x = QL
        if T < self.ISTART: x = 0
        if T >= self.SHUT: x = 0
        return x

    def collectorOutput (self):
        """Calculate collector field output"""
        x = self.COLLECTOR[self.HR] - self.QF
        if x < 0: x = 0
        self.QC = x

    def startupEnergy (self):
        if self.SU < self.EP:
            self.SU = self.SU+self.QC
            if self.SU < self.EP:
                self.QC = 0
            else:
                self.QC = self.SU-self.EP
    
    def storageLoss (self):
        if self.ES > 0:
            self.ES = self.ES-self.SL #Energy accumulated in storage. Not zeroed at end of day
            self.ZS = self.ZS-self.SL #Energy lost from storage over the day.  Zeroed at end of day

    def storageInput (self, heatRate):
        "Accept heat from an auxiliary source."
        self.ES = min (self.ES+heatRate, self.SM)
        if self.ES+heatRate > self.SM:
            return self.ES+heatRate-self.SM
        else:
            return 0
        
    def controlLogic (self, QL):
	self.QA = 0
	self.QS = 0
	self.QD = 0
	
	if self.QC > 0:
		if self.QC > QL:
			if self.ES > self.SM:
				self.QD = self.QC-QL
				self.MODE = 4
			else:
				self.QS = self.QC-QL
				self.MODE = 3
				if (self.ES+self.QS) > self.SM:
					self.QD = self.ES+self.QS-self.SM
					self.QS = self.QS-self.QD
					self.MODE = 3.4
		else:
			if self.ES > 0:
				self.QS = self.QC-QL
				self.MODE = 5
				if (self.ES+self.QS) <= 0:
					self.QS = -self.ES
					self.QA = QL+self.QS-self.QC
					self.MODE = 5.1
			else:
				self.QA = QL-self.QC
				self.MODE = 2
	else:
		if self.ES > 0:
			self.QS = -QL
			self.MODE = 6
			if (self.ES+self.QS) <= 0:
				self.QS = -self.ES
				self.QA = QL+self.QS-self.QC
				self.MODE = 6.1
		else:
			self.QA = QL
			self.MODE = 1
	if QL <= 0: self.MODE = 0

    def validate (self):
        """Call to validate the object state."""
        # Validate entries
        if self.EP < 0: _alert("Energy to heat-up piping must be positive!")
        if self.QF < 0: _alert("Field piping heat loss must be positive!")
        if self.SM < 0: _alert("Maximum storage capacity must be positive!")
        if self.ES < 0: _alert("Energy in storage must be positive!")
        if self.SL < 0: _alert("Storage heat loss must be positive!")
        if self.ISTART < 0 or self.ISTART > 23: _alert("Start time must be between 0 and 23!")
        if self.SHUT < 0 or self.SHUT > 24: _alert("Shutdown time must be between 0 and 24!")
        if self.SHUT < self.ISTART: _alert("Shutdown time must be greater than Start time")

    def nexthour (self, load):
        D = self.HR / 24
        T = self.HR % 24

        if T == 0:
            # New day, reset.
            self.ZS = 0
            self.SU = 0

        rQL = self.returnQL (load)
        self.collectorOutput ()
        self.startupEnergy ()
        self.storageLoss ()
        self.controlLogic (rQL)

        self.ES += self.QS
        self.ZS += self.QS
        self.HR += 1

        return {'T': T, 'QC': round(self.QC,3), 'QA': round(self.QA,3), 'QS': round(self.QS,3), 'ES': round(self.ES,3),
                'QD': round(self.QD,3), 'QL': round(rQL,3), 'MODE': self.MODE}
