import regions

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
