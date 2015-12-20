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
arr = np.genfromtxt('exchanges.csv', delimiter=',')

# Step 1, write the file back out in JSON
f = open('exchanges.json', 'w')
json.dump(arr.tolist(), f)
f.close()

for i in range(1, arr.shape[0]):
    for j in range(1, arr.shape[1]):
        flow = arr[i, j]
        if int(flow) > 0:
            print '  %s -> %s [label="%d" penwidth=%.2f]' % \
                (labels[i], labels[j], flow, width(flow))
print '}'
