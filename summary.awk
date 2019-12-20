#!/usr/bin/gawk -f
#
# Copyright (C) 2013, 2014, 2017, 2019 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# This script processes the output of evolve into a summary
# table. Usage example:
#
# awk -f summary.awk < evolve-output.txt
#
# The script is capable of processing a file containing multiple runs.
# Multiple summary tables will be output.

BEGIN {
    PROCINFO["sorted_in"] = "@ind_num_asc"
    # merit order
    split("battery HSA EGS PV wind CST Coal Coal-CCS CCGT CCGT-CCS hydro PSH GT OCGT diesel DR", merit)
    # assume 8760 timesteps unless specified in the input
    timesteps = 8760

    # initialise some variables
    co2 = 0
    surplus = 0
}

# Convert any power unit to GW
function gw(amt, suffix)
{
    switch (suffix) {
	case "kW":
	    return amt / 10**6
	case "MW":
	    return amt / 10**3
	case "GW":
	    return amt
	default:
	    print("ERROR: unrecognised suffix ", suffix)
	    exit(1)
    }

}

# Convert any energy unit to TWh
function twh(amt, suffix)
{
    switch (suffix) {
	case "MWh":
	    return amt / 10**6
	case "GWh":
	    return amt / 10**3
	case "TWh":
	    return amt
	default:
	    print("ERROR: unrecognised suffix ", suffix)
	    exit(1)
    }
}


# add AMT to the capacity total for technology TECH
function addcap(tech)
{
    caps[tech] += gw($(NF-1), $(NF))
    last=tech
}

/[Bb]attery.*[kMG]W.?$/		{ addcap("battery") }
/HSA.*[kMG]W.?$/		{ addcap("HSA") }
/EGS.*[kMG]W.?$/		{ addcap("EGS") }
/PV.*[kMG]W.?$/			{ addcap("PV") }
/wind.*[kMG]W.?$/		{ addcap("wind") }
/ S?CST.*[kMG]W.?$/		{ addcap("CST") }
/ hydro.*[kMG]W.?$/		{ addcap("hydro") }
/pumped-hydro.*[kMG]W.?$/   	{ addcap("PSH") }
/PSH.*[kMG]W.?$/		{ addcap("PSH") }
/ GT.*[kMG]W.?$/		{ addcap("GT") }
/CCGT-CCS.*[kMG]W.?$/		{ addcap("CCGT-CCS") }
/CCGT .*[kMG]W.?$/		{ addcap("CCGT") }
/coal.*[kMG]W.?$/		{ addcap("Coal") }
/Coal-CCS.*[kMG]W.?$/		{ addcap("Coal-CCS") }
/OCGT.*[kMG]W.?$/		{ addcap("OCGT") }
/diesel.*[kMG]W.?$/		{ addcap("diesel") }
/(DR|demand).*[kMG]W.?$/	{ addcap("DR") }

/supplied [[:digit:]\.]+ [MGT]Wh/ {
    sub(/,/, "", $3)  # strip trailing comma
    energy[last] += twh($2, $3)
    total_generation += twh($2, $3)
}
/spilled [[:digit:]\.] TWh/	{ surplus += $5 }	# may be "spilled" in old log files
/surplus [[:digit:]\.]+ [MGT]Wh/ {			# now it's "surplus"
    sub(/,/, "", $8)  # strip trailing comma
    surplus += twh($7, $8)
}

/Mt CO2.?$/ 		{ co2 += $(NF-2) }
/Mt CO2,/		{ co2 += $(NF-5)-$(NF-2) }

/Unserved energy/	{ unserved = $3 }
/Score:/		{ cost = $2 }
/Penalty:/		{ penalty = $2 }
/Constraints violated/	{ sub("Constraints violated: ", ""); gsub(" ", ","); constraints = $0; }
/Timesteps:/		{ timesteps = $2 }
/^{.*}/			{ params = $0 }
/Demand energy:/	{ total_demand = $(NF-1) }

/^Done/ {
    scenario_num++
    total_capacity = 0
    for (c in caps) {
    	total_capacity += caps[c]
    }
    if (scenario_num > 1)
	print ""
    printf ("# scenario %d\n", scenario_num)
    if (params != "")
       printf ("# options %s\n", params)
    printf ("# demand %.2f TWh\n", total_demand)
    printf ("# emissions %.2f Mt\n", co2)
    printf ("# unserved %s\n", unserved)
    printf ("# score %.2f $/MWh\n", cost)
    if (penalty > 0)
    {
	printf ("# penalty %.2f $/MWh\n", penalty)
	printf ("# constraints <%s> violated\n", constraints)
    }
    printf ("# %10s\t  GW\tshare\t  TWh\tshare\tCF\n", "tech")
    for (m in merit) {
	c = merit[m]
	if (caps[c] != "")
	    printf ("%12s\t%4.1f\t%.3f\t%5.1f\t%.3f\t%02.3f\n", c, \
		    caps[c], caps[c] / total_capacity, \
		    energy[c], energy[c] / total_generation, \
		    (caps[c] > 0) ? (energy[c] * 1000) / (caps[c] * timesteps) : 0)
    }
    if (surplus > 0)
	printf ("%12s%8s\t%5s\t%5.1f\t%.3f\n", "surplus", "N/A", "N/A", surplus, surplus / total_demand)

    print ""
    co2 = 0
    surplus = 0
    params = ""
    constraints = ""
    delete caps
    delete energy
}
