# Copyright (C) 2014 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Support code for the 43 polygons of the AEMO study."""

import regions

# Table mapping polygon number to NEM region.
region_table = [None] * 44

for num in range(21, 25) + range(28, 32) + range(33, 37):
    region_table[num] = regions.vic

for num in range(1, 12) + range(14, 18):
    region_table[num] = regions.qld

for num in [12, 13, 18, 19, 20, 25, 26, 27, 32]:
    region_table[num] = regions.sa

for num in [40, 41, 42, 43]:
    region_table[num] = regions.tas

for num in [37, 38, 39]:
    region_table[num] = regions.vic

wind_limit = [80.3, 0, 36.9, 6.5, 15.6, 1.5, 6.9, 2.6, 0, 4.1, 1.5,
              2.1, 0.9, 30.3, 0, 0, 40.5, 0.2, 0, 49.1, 2.3, 0, 1.7,
              116.3, 3.3, 71.9, 128.3, 11.7, 0.5, 0.6, 52.5, 20.0, 0,
              0, 0.9, 101.0, 9.15, 10.2, 15.6, 11.4, 14.1, 0.5, 29.1]

pv_limit = [133, 1072, 217, 266, 1343, 1424, 287, 1020, 657, 175, 47,
            488, 749, 1338, 1497, 1093, 243, 558, 647, 639, 921, 1310, 1182, 125,
            81, 493, 689, 937, 736, 522, 31, 527, 535, 618, 339, 26, 670, 78, 347,
            13, 21, 0.21, 5]
