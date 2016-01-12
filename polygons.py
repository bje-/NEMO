# Copyright (C) 2014, 2015, 2016 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Support code for the 43 polygons of the AEMO study."""

import dijkstra
from latlong import LatLong
import regions
import numpy as np

regions.nsw.polygons = {n: 0 for n in range(21, 25) + range(28, 32) + range(33, 37)}
regions.qld.polygons = {n: 0 for n in range(1, 12) + range(14, 18)}
regions.sa.polygons = {n: 0 for n in [12, 13, 18, 19, 20, 25, 26, 27, 32]}
regions.snowy.polygons = {}
regions.tas.polygons = {n: 0 for n in [40, 41, 42, 43]}
regions.vic.polygons = {n: 0 for n in [37, 38, 39]}

# indicate where the loads are
regions.qld.polygons[17] = 1.0
regions.nsw.polygons[31] = 1.0
regions.sa.polygons[32] = 1.0
regions.tas.polygons[43] = 1.0
regions.vic.polygons[39] = 1.0

# Ensure all weights sum to one.
for r in regions.All:
    if len(r.polygons) > 0:
        assert sum(r.polygons.values()) == 1

# Useful for testing
wildcard = 31

# Vertices of the closed polygons (nb. must be closed)
_polygons = {
    1: ((144.602, -13.838), (145.602, -13.838), (148.447, -18.282), (146.646, -19.041), (145.107, -18.792), (143.459, -18.480), (144.602, -13.838)),
    2: ((140.949, -18.099), (143.459, -18.480), (143.701, -20.715), (140.949, -20.612), (140.949, -18.099)),
    3: ((143.459, -18.480), (145.107, -18.792), (146.646, -20.797), (143.701, -20.715), (143.459, -18.480)),
    4: ((148.447, -18.282), (150.754, -21.545), (147.810, -22.513), (146.646, -20.797), (145.107, -18.792), (146.646, -19.041), (148.447, -18.282)),
    5: ((140.949, -20.612), (143.701, -20.715), (143.987, -23.665), (140.949, -23.665), (140.949, -20.612)),
    6: ((143.701, -20.715), (146.646, -20.797), (147.810, -22.513), (148.887, -23.665), (146.382, -23.665), (143.987, -23.665), (143.701, -20.715)),
    7: ((150.754, -21.545), (152.974, -24.137), (149.639, -24.817), (148.887, -23.665), (147.810, -22.513), (150.754, -21.545)),
    8: ((140.949, -23.665), (143.987, -23.665), (144.141, -25.958), (140.999, -25.996), (140.949, -23.665)),
    9: ((143.987, -23.665), (146.382, -23.665), (147.458, -25.958), (144.141, -25.958), (143.987, -23.665)),
    10: ((146.382, -23.665), (148.887, -23.665), (149.639, -24.817), (150.529, -25.958), (147.458, -25.958), (146.382, -23.665)),
    11: ((152.974, -24.137), (154.457, -25.958), (150.529, -25.958), (149.639, -24.817), (152.974, -24.137)),
    12: ((135.183, -25.999), (137.933, -25.997), (137.933, -29.075), (135.187, -29.075), (135.183, -25.999)),
    13: ((137.933, -25.997), (140.999, -25.996), (140.999, -28.999), (137.933, -29.075), (137.933, -25.997)),
    14: ((140.999, -25.996), (144.141, -25.958), (144.232, -28.999), (141.001, -28.999), (140.999, -25.996)),
    15: ((144.141, -25.958), (147.458, -25.958), (147.550, -28.999), (144.232, -28.999), (144.141, -25.958)),
    16: ((147.458, -25.958), (150.529, -25.958), (150.688, -28.999), (147.550, -28.999), (147.458, -25.958)),
    17: ((154.457, -25.958), (154.852, -29.075), (150.688, -28.999), (150.529, -25.958), (154.457, -25.958)),
    18: ((131.199, -29.075), (135.187, -29.075), (135.187, -31.325), (131.199, -31.325), (131.199, -29.075)),
    19: ((135.187, -29.075), (137.933, -29.075), (137.933, -31.325), (135.187, -31.325), (135.187, -29.075)),
    20: ((137.933, -29.075), (140.999, -28.999), (141.001, -30.999), (141.001, -31.354), (137.933, -31.325), (137.933, -29.075)),
    21: ((141.001, -28.999), (144.232, -28.999), (144.141, -31.109), (141.001, -30.998), (141.001, -28.999)),
    22: ((144.232, -28.999), (147.550, -28.999), (146.843, -31.840), (144.141, -31.766), (144.141, -31.109), (144.232, -28.999)),
    23: ((147.550, -28.999), (150.688, -28.999), (149.359, -31.878), (146.843, -31.840), (147.550, -28.999)),
    24: ((154.852, -29.075), (153.798, -32.639), (149.359, -31.878), (150.688, -28.999), (154.852, -29.075)),
    25: ((131.199, -31.325), (135.187, -31.325), (133.638, -34.053), (131.199, -32.658), (131.199, -31.325)),
    26: ((135.187, -31.325), (137.933, -31.325), (137.900, -33.852), (137.856, -36.985), (135.700, -36), (133.638, -34.053), (135.187, -31.325)),
    27: ((137.933, -31.326), (141.001, -31.354), (141.002, -33.311), (141.003, -33.982), (140.964, -33.981), (137.900, -33.852), (137.933, -31.326)),
    28: ((141.001, -30.998), (144.141, -31.109), (144.141, -31.766), (143.954, -33.303), (141.002, -33.311), (141.001, -31.354), (141.001, -30.998)),
    29: ((144.141, -31.766), (146.843, -31.840), (146.250, -34.053), (143.943, -34.016), (143.954, -33.303), (144.141, -31.766)),
    30: ((146.843, -31.840), (149.359, -31.878), (148.315, -34.107), (146.250, -34.053), (146.843, -31.840)),
    31: ((153.798, -32.639), (152.260, -34.724), (148.315, -34.107), (149.359, -31.878), (153.798, -32.639)),
    32: ((137.900, -33.852), (140.964, -33.981), (140.964, -33.990), (140.963, -33.990), (140.962, -34.110), (140.966, -35.237), (140.966, -35.389), (140.964, -35.749), (140.974, -37.359), (140.971, -37.791), (140.966, -38.056), (140.966, -38.568), (137.856, -36.985), (137.900, -33.852)),
    33: ((141.002, -33.311), (143.954, -33.303), (143.943, -34.016), (143.811, -35.299), (140.966, -35.237), (140.962, -34.108), (140.963, -33.990), (140.964, -33.990), (140.964, -33.981), (141.003, -33.982), (141.002, -33.311)),
    34: ((143.943, -34.016), (146.250, -34.053), (145.698, -35.989), (143.811, -35.299), (143.943, -34.016)),
    35: ((146.250, -34.053), (148.315, -34.107), (147.118, -36.510), (145.698, -35.989), (146.250, -34.053)),
    36: ((152.260, -34.724), (150.590, -37.831), (147.118, -36.510), (148.315, -34.107), (152.260, -34.724)),
    37: ((140.966, -35.237), (143.811, -35.299), (143.483, -39.249), (140.968, -38.568), (140.966, -38.056), (140.971, -37.791), (140.975, -37.359), (140.963, -35.742), (140.966, -35.389), (140.966, -35.237)),
    38: ((146.426, -40.581), (145.698, -35.989), (147.118, -36.510), (150.590, -37.831), (146.426, -40.581)),
    39: ((143.483, -39.249), (146.426, -40.581), (146.426, -42.033), (144.097, -42.033), (143.483, -39.249)),
    40: ((146.426, -40.581), (149.052, -38.849), (149.052, -42.033), (146.426, -42.033), (146.426, -40.581)),
    41: ((144.097, -42.033), (146.426, -42.033), (146.426, -44), (144.097, -43.747), (144.097, -42.033)),
    42: ((146.426, -42.033), (149.052, -42.033), (149.052, -43.747), (146.426, -44), (146.426, -42.033)),
    43: ((145.698, -35.989), (146.426, -40.581), (143.481, -39.249), (143.811, -35.299), (145.698, -35.989)),
}

numpolygons = len(_polygons)

# Table mapping polygon number to region.
_region_table = [None] * (numpolygons + 1)
for rgn in [regions.nsw, regions.qld, regions.sa, regions.tas, regions.vic]:
    for poly in rgn.polygons:
        _region_table[poly] = rgn


def region(poly):
    """Return the region a polygon resides in.

    >>> region(1)
    QLD1
    >>> region(40)
    TAS1
    """
    return _region_table[poly]


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


def _centroid(vertices):
    """Find the centroid of a polygon."""

    # Ensure the polygon is closed
    assert vertices[0] == vertices[-1]
    sum = 0
    vsum = (0, 0)
    for i in range(len(vertices) - 1):
        v1 = vertices[i]
        v2 = vertices[i + 1]
        cross = v1[0] * v2[1] - v1[1] * v2[0]
        sum += cross
        vsum = (((v1[0] + v2[0]) * cross) + vsum[0], ((v1[1] + v2[1]) * cross) + vsum[1])
        z = 1. / (3. * sum)
    return (vsum[0] * z, vsum[1] * z)

centroids = {}
for i, vertices in zip(_polygons.keys(), _polygons.values()):
    a, b = _centroid(vertices)
    centroids[i] = LatLong(b, a)


def path(poly1, poly2):
    """
    Return a path from polygon 1 to polygon 2.

    >>> path(1, 30)
    [(1, 4), (4, 10), (10, 16), (16, 23), (23, 30)]
    >>> path(23, 43)
    [(23, 30), (30, 35), (35, 38), (38, 41), (41, 43)]
    """
    return connections[(poly1, poly2)]


def subset(path, polysuperset):
    """
    Are all polygons in path present in superset?

    >>> subset([(1,2), (2,3)], [1,2,3])
    True
    >>> subset([(1,4), (4,3)], [1,2,3])
    False
    """
    # Flatten the list of pairs into one long list.
    polylist = [i for sub in path for i in sub]
    # Now for a simple set operation.
    return set(polylist) <= set(polysuperset)


def direct_p(poly1, poly2):
    """
    Return True if region A and B are directly connected.

    >>> direct_p(1, 2)
    True
    >>> direct_p(1, 40)
    False
    """
    return len(path(poly1, poly2)) <= 1


def dist(i, j):
    """Return the distance between two polygon centroids.

    >>> dist(1,1)
    0
    >>> dist(1,43)
    2347
    >>> dist(1,43) == distances[1,43]
    True
    """
    return int(centroids[i].distance(centroids[j]))


# A proposed transmission network.

net = {1: {2: dist(1, 2), 3: dist(1, 3), 4: dist(1, 4)},
       2: {1: dist(2, 1), 3: dist(2, 3), 5: dist(2, 5)},
       3: {1: dist(3, 1), 2: dist(3, 2), 4: dist(3, 4), 6: dist(3, 6)},
       4: {1: dist(4, 1), 3: dist(4, 3), 6: dist(4, 6), 7: dist(4, 7), 10: dist(4, 10)},
       5: {2: dist(5, 2), 6: dist(5, 6), 8: dist(5, 8)},
       6: {3: dist(6, 3), 4: dist(6, 4), 5: dist(6, 5), 9: dist(6, 9)},
       7: {4: dist(7, 4), 10: dist(7, 10), 11: dist(7, 11)},
       8: {5: dist(8, 5), 9: dist(8, 9), 14: dist(8, 14)},
       9: {6: dist(9, 6), 8: dist(9, 8), 10: dist(9, 10), 15: dist(9, 15)},
       10: {4: dist(10, 4), 7: dist(10, 7), 9: dist(10, 9), 16: dist(10, 16)},
       11: {7: dist(7, 11), 16: dist(16, 11), 17: dist(11, 17)},
       12: {13: dist(12, 13), 19: dist(12, 19)},
       13: {12: dist(13, 12), 14: dist(13, 14), 20: dist(13, 20)},
       14: {8: dist(14, 8), 13: dist(14, 13), 15: dist(14, 15), 21: dist(14, 21)},
       15: {9: dist(15, 9), 14: dist(15, 14), 16: dist(15, 16), 22: dist(15, 22)},
       16: {10: dist(16, 10), 11: dist(16, 11), 15: dist(16, 15), 17: dist(16, 17), 23: dist(16, 23)},
       17: {11: dist(17, 11), 16: dist(17, 16), 24: dist(17, 24)},
       18: {19: dist(18, 19), 25: dist(18, 25)},
       19: {12: dist(19, 12), 18: dist(19, 18), 20: dist(19, 20), 26: dist(19, 26)},
       20: {13: dist(20, 13), 19: dist(20, 19), 21: dist(20, 21), 27: dist(20, 27)},
       21: {14: dist(21, 14), 20: dist(21, 20), 22: dist(21, 22), 29: dist(21, 29)},
       22: {15: dist(22, 15), 21: dist(22, 21), 23: dist(22, 23), 29: dist(22, 29)},
       23: {16: dist(23, 16), 22: dist(23, 22), 24: dist(23, 24), 30: dist(23, 30)},
       24: {17: dist(24, 17), 23: dist(24, 23), 31: dist(23, 31)},
       25: {18: dist(25, 18), 26: dist(25, 26)},
       26: {19: dist(26, 19), 25: dist(26, 25), 27: dist(26, 27)},
       27: {20: dist(27, 20), 26: dist(27, 26), 28: dist(27, 28), 32: dist(27, 32), 33: dist(27, 33)},
       28: {21: dist(28, 21), 27: dist(28, 27), 29: dist(28, 29), 33: dist(28, 33)},
       29: {22: dist(29, 22), 28: dist(29, 28), 30: dist(29, 30), 34: dist(29, 34)},
       30: {23: dist(30, 23), 29: dist(30, 29), 31: dist(30, 31), 35: dist(30, 35)},
       31: {24: dist(31, 24), 30: dist(31, 30), 36: dist(31, 36)},
       32: {27: dist(32, 27), 37: dist(32, 37)},
       33: {27: dist(33, 27), 28: dist(33, 28), 34: dist(33, 34), 37: dist(33, 37)},
       34: {29: dist(34, 29), 33: dist(34, 33), 35: dist(34, 35), 39: dist(34, 39)},
       35: {30: dist(35, 30), 34: dist(35, 34), 36: dist(35, 36), 38: dist(35, 38), 39: dist(35, 39)},
       36: {31: dist(36, 31), 35: dist(36, 35), 38: dist(36, 38)},
       37: {32: dist(37, 32), 33: dist(37, 33), 39: dist(37, 39)},
       38: {35: dist(38, 35), 36: dist(38, 36), 39: dist(38, 39), 41: dist(38, 41)},
       39: {34: dist(39, 34), 35: dist(39, 35), 37: dist(39, 37), 38: dist(39, 38), 40: dist(39, 40)},
       40: {39: dist(40, 39), 41: dist(40, 41), 42: dist(40, 42)},
       41: {38: dist(41, 38), 40: dist(41, 40), 43: dist(41, 43)},
       42: {40: dist(42, 40), 43: dist(42, 43)},
       43: {41: dist(43, 41), 42: dist(43, 42)}}

distances = np.zeros((numpolygons + 1, numpolygons + 1))
# mark row 0 and column 0 as unused (there is no polygon #0)
distances[0] = np.nan
distances[::, 0] = np.nan
for p1 in range(1, distances.shape[0]):
    for p2 in range(1, distances.shape[0]):
        distances[p1, p2] = dist(p1, p2)

existing_net = np.zeros((numpolygons + 1, numpolygons + 1))
# mark row 0 and column 0 as unused (there is no polygon #0)
existing_net[0] = np.nan
existing_net[::, 0] = np.nan
for (p1, p2, limit) in [(1, 4, 350), (4, 7, 1300), (7, 11, 1600),
                        (11, 17, 1600), (16, 17, 4500), (17, 24, 1250),
                        (24, 31, 1000), (31, 36, 500), (36, 38, 500),
                        (38, 39, 500), (39, 40, 500), (39, 37, 600),
                        (37, 32, 600), (32, 27, 200)]:
    assert p2 in net[p1].keys() and p1 in net[p2].keys()
    existing_net[p1, p2] = limit
    existing_net[p2, p1] = limit

# override with some asymmetric links
existing_net[24, 17] = 300
existing_net[17, 11] = 1100
existing_net[11, 7] = 1100

connections = {}
for dest in range(1, numpolygons + 1):
    for src in range(1, numpolygons + 1):
        shortest = [n for n in dijkstra.shortestPath(net, src, dest)]
        pairs = []
        for i in range(len(shortest) - 1):
            pairs.append((shortest[i], shortest[i + 1]))
        connections[(src, dest)] = pairs
