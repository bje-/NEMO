def changes (dataset, start, end):
  max = ma.zeros (dims)
  min = ma.zeros (dims)
  # Produce a grid that gives the maximum 1-h delta between the hours
  # of start and end.
  for h in range (Hour (start), Hour (end)):
    g1 = grid (dataset, h)
    g2 = grid (dataset, h+1)
    if not np.any (g1) or not np.any (g2):
      continue
    g = (g2-g1).filled (0)
    max = np.maximum (max, g)
    min = np.minimum (min, g)

  result = np.where (abs(min) > abs(max), min, max)
  result.mask = ozmask
  return result

