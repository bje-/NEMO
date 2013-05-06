# ts2swrf.awk: a TAPM time series to SWRF translator
#
# -*- AWK -*-
# Copyright (C) 2011 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# This script requires four VAR=VALUE arguments to be passed to
# the awk script: year, lat and long.  Usage example:
# awk -f ts2swrf.awk lat=-35 long=149 year=2010

# Emit the header.
/DATE/ { print "Created " strftime ("%Y-%m-%d %H:%M:%S") " by ts2swrf.awk for year " year
  print "Requested latitude = " lat
  print "Requested longitude = " long
  print "Latitude of data = " lat
  print "Longitude of data = " long
  print "Approximate distance from requested point = 0.0 km"
  print "Elevation = 0 m"
  print ""
  print ""
  print "Date/Time (GMT)	Surface Pressure (mb)	Speed 200m (m/s)	Speed 100m (m/s)	Speed 50m (m/s)	Speed 20m (m/s)	Speed 10m (m/s)	Direction 200m (d)	Direction 100m (d)	Direction 50m (d)	Direction 20m (d)	Direction 10m (d)	Temperature 200m (K)	Temperature 100m (K)	Temperature 50m (K)	Temperature 20m (K)	Temperature 10m (K)"
}

# Emit each record. Hours in the TAPM time series are in local time
# and numbered from 1-24. Subtract one to put them in the range 0-23.

# eg. 20100101  1  3.9  32.0  23.1
/2010/ {
  OFS="\t"
  date = $1 " " sprintf ("%02d00", $2-1)
  print date, "1.0", 0, $3, 0, 0, 0, 0, $4, 0, 0, 0, 0, $5, 0, 0, 0
}
