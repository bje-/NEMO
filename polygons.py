# Copyright (C) 2014 The University of New South Wales
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
    region_table[num] = regions.nsw

for num in range(1, 12) + range(14, 18):
    region_table[num] = regions.qld

for num in [12, 13, 18, 19, 20, 25, 26, 27, 32]:
    region_table[num] = regions.sa

for num in [40, 41, 42, 43]:
    region_table[num] = regions.tas

for num in [37, 38, 39]:
    region_table[num] = regions.vic


def in_region(rgn):
    """
    Return all polygons in region R.

    >>> import regions
    >>> in_region(regions.tas)
    [40, 41, 42, 43]
    """
    return [i for i, r in enumerate(region_table) if r is rgn]


wind_limit = [None, 80.3, 0, 36.9, 6.5, 15.6, 1.5, 6.9, 2.6, 0, 4.1,
              1.5, 2.1, 0.9, 30.3, 0, 0, 40.5, 0.2, 0, 49.1, 2.3, 0,
              1.7, 116.3, 3.3, 71.9, 128.3, 11.7, 0.5, 0.6, 52.5,
              20.0, 0, 0, 0.9, 101.0, 9.15, 10.2, 15.6, 11.4, 14.1,
              0.5, 29.1]

pv_limit = [None, 133, 1072, 217, 266, 1343, 1424, 287, 1020, 657,
            175, 47, 488, 749, 1338, 1497, 1093, 243, 558, 647, 639,
            921, 1310, 1182, 125, 81, 493, 689, 937, 736, 522, 31,
            527, 535, 618, 339, 26, 670, 78, 347, 13, 21, 0.21, 5]

cst_limit = [None, 102, 822, 166, 204, 1030, 1092, 220, 782, 504, 134,
             36, 374, 574, 1026, 1148, 838, 186, 428, 496, 490, 706,
             1004, 906, 96, 62, 378, 528, 718, 564, 400, 24, 404, 410,
             474, 260, 20, 514, 60, 266, 10, 16, 0.16, 4]

# Centroids computed using:
# from shapely.wkt import loads as load_wkt
# for line in open('polygons.txt'):
#     poly = load_wkt(line)
#     print '(%.4f, %.4f), ' % (poly.centroid.x, poly.centroid.y)

centroid = [None, (145.6805, -16.8409), (142.2379, -19.4933),
            (144.7431, -19.8044), (148.0952, -20.3882), (142.3891, -22.1891),
            (145.8032, -22.3341), (150.3670, -23.2435), (142.5151, -24.8275),
            (145.5085, -24.8731), (148.3193, -24.8506), (152.0407, -25.2058),
            (136.5593, -27.5362), (139.4600, -27.5170), (142.5967, -27.4951),
            (145.8451, -27.4786), (149.0567, -27.4841), (152.6411, -27.5123),
            (133.1927, -30.2004), (136.5601, -30.2004), (139.4783, -30.1884),
            (142.6081, -30.0221), (145.6999, -30.3552), (148.6318, -30.3777),
            (152.2333, -30.6865), (133.0352, -32.3367), (136.2310, -33.8026),
            (139.4694, -32.6314), (142.5256, -32.1674), (145.2835, -32.8903),
            (147.7073, -32.9339), (150.9370, -33.3127), (139.5187, -35.8797),
            (142.4491, -34.2822), (145.0052, -34.8352), (146.8992, -35.1261),
            (149.6554, -35.8086), (142.3498, -37.0599), (147.5719, -38.1292),
            (144.9769, -40.9127), (147.9022, -40.8201), (145.2879, -42.9548),
            (147.7086, -42.9548), (144.8708, -37.9380)]
