# Some convenience variables.
#
# -*- Python -*-
# Copyright (C) 2010, 2011 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

from latlong import LatLong

melbourne = LatLong ((-37.8333, 144.9833))
sydney = LatLong ((-33.52, 151.13))
canberra = LatLong ((-35.3, 149.19))
perth = LatLong ((-31.933, 115.833))
darwin = LatLong ((-12.4, 130.8))
brisbane = LatLong ((-27.4833, 153.0333))
hobart = LatLong ((-42.8389, 147.4992))
adelaide = LatLong ((-34.9167, 138.6167))

cobar = LatLong ((-31.5, 145.8))
nyngan = LatLong ((-31.584129, 147.197099))
broken_hill = LatLong ((-32.0028, 141.4681))
alice_springs = LatLong ((-23.7951, 133.889))
marble_bar = LatLong ((-21.1756, 119.7497))
darlington_point = LatLong ((-34.5147, 145.7807))
dubbo = LatLong ((-32.2133, 148.5706))
moree = LatLong ((-29.5, 149.9))
tamworth = LatLong ((-31.0867, 150.8467))
prairie = LatLong ((-20.8708, 144.6))
longreach = LatLong ((-23.45, 144.25))
charleville = LatLong ((-26.4167, 146.2167))
roma = LatLong ((-26.5719, 148.7897))
bourke = LatLong ((-30.0917, 145.9358))
port_augusta = LatLong ((-32.5, 137.7667))
mildura = LatLong ((-34.1833, 142.2))
kalgoorlie = LatLong ((-30.75, 121.4667))
carnarvon = LatLong ((-24.9, 113.65))
liverpool = LatLong ((-33.9167, 150.9333))
murtho  = LatLong ((-34.054, 140.854))
eden = LatLong ((-37.07, 149.9))

sitenames = {}
sitenames[melbourne] = 'Melbourne'
sitenames[sydney] = 'Sydney'
sitenames[darwin] = 'Darwin'
sitenames[brisbane] = 'Brisbane'
sitenames[adelaide] = 'Adelaide'
sitenames[canberra] = 'Canberra'
sitenames[hobart] = 'Hobart'
sitenames[perth] = 'Perth'

sitenames[nyngan] = 'Nyngan'
sitenames[broken_hill] = 'Broken Hill'
sitenames[alice_springs] = 'Alice Springs'
sitenames[marble_bar] = 'Marble Bar'
sitenames[darlington_point] = 'Darlington Point'
sitenames[dubbo] = 'Dubbo'
sitenames[moree] = 'Moree'
sitenames[tamworth] = 'Tamworth'
sitenames[prairie] = 'Prairie'
sitenames[longreach] = 'Longreach'
sitenames[charleville] = 'Charleville'
sitenames[roma] = 'Roma'
sitenames[bourke] = 'Bourke'
sitenames[port_augusta] = 'Port Augusta'
sitenames[mildura] = 'Mildura'
sitenames[kalgoorlie] = 'Kalgoorlie'
sitenames[carnarvon] = 'Carnarvon'

bze = [prairie, longreach, charleville, roma, moree, bourke, dubbo, mildura, \
           broken_hill, port_augusta, kalgoorlie, carnarvon]
capitals = [canberra, sydney, melbourne, perth, adelaide, darwin, brisbane, hobart]
sites = bze + capitals + [nyngan, broken_hill, alice_springs, marble_bar]

sa_wa_nt   = surveyor_general = LatLong ((-26.0,129.0))
sa_nt_qld  = poeppel = LatLong ((-26.0,138.0))
sa_qld     = haddon = LatLong ((-26.0,141.0))
sa_qld_nsw = cameron = LatLong ((-29.0,141.0))
wilsons_prom = LatLong ((-39.1274, 146.4114))

years = range (1998,2002) + range (2003,2011)

nodata = -999
cellsize = 0.05
xllcorner = 112.025
yllcorner = -43.925

ghi = None
dni = None
demand = None
