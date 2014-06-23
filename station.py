#!/usr/bin/env python
#
# -*- Python -*-
# Copyright (C) 2011 Marton Hidas
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
#
# station.py - information about power stations, as referred to in
# the AEMO data.
#
# The nonsched dict contains information on non-scheduled generation
# stations based on the following documents (and a bit of detective
# work matching some of the DUIDS with station names):
#   http://www.aemo.com.au/data/gendata_exist.shtml
#   http://www.nemweb.com.au/reports/current/cdeii/CO2EII_Available_Generators.csv
#   http://www.aemo.com.au/planning/2010ntndp_cd/downloads/NTNDPdatabase/related/List%20of%20Regional%20Boundaries%20and%20Marginal%20Loss%20Factors%202010-11.pdf
#   http://oz-energy-analysis.org/data/generation_wind_farms.php


nonsched = {'BUTLERSG': ('Butlers Gorge PS', 'TAS', 'hydro', 14),
            'CAPTL_WF': ('Capital WF', 'NSW', 'wind', 140),
            'CATHROCK': ('Cathedral Rocks WF', 'SA', 'wind', 66),
            'CHALLHWF': ('Challicum Hills WF', 'VIC', 'wind', 53),
            'CLOVER': ('Clover PS', 'VIC', 'hydro', 30),
            'CLUNY': ('Cluny PS', 'TAS', 'hydro', 17),
            'CNUNDAWF': ('Canunda WF', 'SA', 'wind', 46),
            'CULLRGWF': ('Cullerin Range WF', 'NSW', 'wind', 30),
            'GB01': ('Broken Hill GT 1', 'NSW', 'gas', 50),
            'GB02': ('Broken Hill GT 2', 'NSW', 'gas', 50),
            'INVICTA': ('Invicta Mill', 'QLD', 'th-bagasse', 39),
            'LKBONNY1': ('Lake Bonney Stage 1 WF', 'SA', 'wind', 81),
            'MTMILLAR': ('Mount Millar WF', 'SA', 'wind', 70),
            'PALOONA': ('Paloona PS', 'TAS', 'hydro', 28),
            'PIONEER': ('Pioneer Sugar Mill', 'QLD', 'bagasse', 68),
            'PORTWF': ('Portland (Bridgewater+Nelson) WF', 'VIC', 'wind', 102),
            'REPULSE': ('Repulse PS', 'TAS', 'hydro', 28),
            'ROWALLAN': ('Rowallan PS', 'TAS', 'hydro', 11),
            'RUBICON': ('Rubicon Mountain Streams PS', 'VIC', 'hydro', 14),
            'STARHLWF': ('Starfish Hill WF', 'SA', 'wind', 35),
            'WAUBRAWF': ('Waubra WF', 'VIC', 'wind', 192),
            'WG01': ('Warragamba PS', 'NSW', 'hydro', 50),
            'WOOLNTH1': ('Woolnorth (Bluff+Studland) WF', 'TAS', 'wind', 140),
            'WPWF': ('Wattle Point WF', 'SA', 'wind', 91),
            'YAMBUKWF': ('Portland (Yambuk) WF', 'VIC', 'wind', 30)}


def list(type=''):
    """
    Prints a table of information about non-scheduled power stations, and
    reports their total capacity. If type is given, only stations of that
    type are included.
    """
    form = "%-12s %-35s %-6s %-12s %7s"
    totcap = 0
    print form % ('DUID', 'Station name', 'Region', 'Type', 'Cap(MW)')
    for k, v in sorted(nonsched.items()):
        if not type or v[2] == type:
            print form % ((k,) + v)
            totcap += v[3]
    print form % ('--------', 'TOTAL CAPACITY', '', '', totcap)


def type(duid):
    """
    Given the DUID for a non-scheduled power station, return the type of
    generator (wind, hydro, etc...)
    """
    return nonsched[duid][2]


def capacity(duid):
    """
    Given the DUID for a non-scheduled power station, return its
    generation capacity in MW.
    """
    return nonsched[duid][3]


def windfarm_p(duid):
    """
    Predicate function that returns  True if the given duid is that of a
    wind farm, False otherwise.
    """
    return nonsched[duid][2] == 'wind'


def count_duids(table):
    """
    Given an AEMO non-scheduled generation table, return a dictionary
    where the keys are DUIDs and the values are the number of times
    each appears in the table.
    """
    dictionary = {}
    for row in table:
        id = row['duid']
        try:
            dictionary[id] += 1
        except:
            dictionary[id] = 1
    return dictionary
