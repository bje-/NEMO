# Copyright (C) 2014 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Configuration file processing (eg, filenames)."""

import configparser
import os


def load(filename):
    """Load a configuration file (or files)."""
    result = config.read(filename)
    assert result != [], "config file %s not found" % filename
    # Verify
    config.get('generation', 'cst-trace')
    config.get('generation', 'egs-geothermal-trace')
    config.get('generation', 'hsa-geothermal-trace')
    config.get('generation', 'wind-trace')
    config.get('generation', 'pv1axis-trace')
    config.get('demand', 'demand-trace')


def get(section, option):
    """Get an option value for the named section, just like
    ConfigParser.get."""
    return config.get(section, option)


config = configparser.ConfigParser()

# If $NEMORC is set, use that as the config filename.
if os.getenv('NEMORC') is not None:
    load(os.getenv('NEMORC'))
else:
    load('nemo.cfg')
