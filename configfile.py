# Copyright (C) 2014 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Configuration file processing (eg, filenames)."""

import ConfigParser


def load(filename):
    """Load a configuration file (or files)."""
    config.read(filename)
    # Verify
    config.get('generation', 'cst-trace')
    config.get('generation', 'wind-trace')
    config.get('generation', 'pv1axis-trace')
    config.get('demand', 'demand-trace')


def get(section, keyword):
    """A wrapper around ConfigParser.get."""
    return config.get(section, keyword)

config = ConfigParser.ConfigParser()
load('default.cfg')
