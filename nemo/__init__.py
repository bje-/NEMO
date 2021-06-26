# Copyright (C) 2017 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""The National Electricity Market Optimiser (NEMO)."""

import nemo.nem  # noqa: F401
from nemo.context import Context
from nemo.sim import run
from nemo.utils import plot

__all__ = ['Context', 'run', 'plot']
