# Copyright (C) 2023 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""
Storage classes.

Storage objects are usually shared between a load and a generator (for
example, a pumped hydro system having a pump, a turbine and a storage
system.
"""


class GenericStorage():
    """A simple electrical storage system.

    The storage has unity efficiency. It is up to the load and
    generator to handle the round trip efficiency of the relevant
    technologies.
    """

    def __init__(self, maxstorage, label=None):
        """Construct a storage object.

        The storage capacity (in MWh) is specified by maxstorage.
        """
        self.maxstorage = maxstorage
        self.storage = self.maxstorage / 2
        self.label = label

    def set_storage(self, maxstorage):
        """
        Change the storage capacity.

        >>> r = GenericStorage(1000)
        >>> r.set_storage(1200)
        >>> r.maxstorage
        1200
        >>> r.storage
        600.0
        """
        self.maxstorage = maxstorage
        self.storage = self.maxstorage / 2

    def soc(self):
        """Return the storage SOC (state of charge)."""
        return self.storage / self.maxstorage

    def empty_p(self):
        """Return True if the storage is empty."""
        return self.storage == 0

    def full_p(self):
        """Return True if the storage is full."""
        return self.maxstorage == self.storage

    def charge(self, amt):
        """
        Charge the storage by amt.

        >>> stg = GenericStorage(1000, 'test')
        >>> stg.charge(100)
        100
        >>> stg.charge(600)
        400.0
        >>> stg.storage == stg.maxstorage
        True
        """
        assert amt >= 0
        delta = min(self.maxstorage - self.storage, amt)
        self.storage = min(self.maxstorage, self.storage + amt)
        return delta

    def discharge(self, amt):
        """
        Discharge the storage by 'amt'.

        >>> stg = GenericStorage(1000, 'test')
        >>> stg.discharge(100)
        100
        >>> stg.discharge(600)
        400.0
        """
        assert amt >= 0
        delta = min(self.storage, amt)
        self.storage = max(0, self.storage - amt)
        return delta


class HydrogenStorage(GenericStorage):
    """Hydrogen storage."""


class PumpedHydroStorage(GenericStorage):
    """A pair of reservoirs for pumped storage."""

    def __init__(self, maxstorage, label=None):
        """Construct a pumped hydro storage reservoir pair.

        The storage capacity (in MWh) is specified by maxstorage.
        """
        GenericStorage.__init__(self, maxstorage, label)

        # Communicate between pump and turbine here to prevent both
        # generators running in the same hour.
        self.last_gen = None
        self.last_pump = None
