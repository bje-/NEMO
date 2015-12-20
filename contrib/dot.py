# Copyright (C) 2015 The University of New South Wales
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import numpy as np
import json

labels = {}
# skip index 0 to trigger KeyError
for i in range(1, 44):
    labels[i] = 'poly%d' % i
labels[17] = 'Brisbane'
labels[31] = 'Sydney'
labels[32] = 'Adelaide'
labels[43] = 'Hobart'
labels[39] = 'Melbourne'


def width(x):
    return int(x) / 1000.

print 'digraph {'
f = open('exchanges.json', 'r')
arr = json.load(f)

for i in range(1, len(arr)):
    for j in range(1, len(arr[i])):
        flow = arr[i][j]
        if int(flow) > 0:
            print '  %s -> %s [label="%d" penwidth=%.2f]' % \
                (labels[i], labels[j], flow, width(flow))
print '}'
