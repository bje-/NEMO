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
    if not result:
        raise FileNotFoundError(f"config file {filename} not found")
    # Verify
    config.get('generation', 'cst-trace')
    config.get('generation', 'egs-geothermal-trace')
    config.get('generation', 'hsa-geothermal-trace')
    config.get('generation', 'wind-trace')
    config.get('generation', 'pv1axis-trace')
    config.get('demand', 'demand-trace')


def get(section, option):
    """
    Get an option value for the named section.

    This works the same as ConfigParser.get.
    """
    return config.get(section, option)


def has_option_p(section, option):
    """
    Check if this section has a given option.

    This works the same as ConfigParser.has_option.
    """
    return config.has_option(section, option)


config = configparser.ConfigParser()

# If $NEMORC is set, use that as the config filename.
if os.getenv('NEMORC') is not None:
    load(os.getenv('NEMORC'))
else:
    load('nemo.cfg')
