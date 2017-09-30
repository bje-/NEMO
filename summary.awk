# Copyright (C) 2013, 2014, 2017 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

BEGIN {
    PROCINFO["sorted_in"] = "@ind_num_asc"
    # merit order
    split("battery HSA EGS PV wind CST Coal Coal-CCS CCGT CCGT-CCS hydro PSH GT OCGT diesel DR", merit)
    # assume 8760 timesteps unless specified in the input
    timesteps = 8760
}

/battery.*GW.?$/	{ caps["battery"] += $(NF-1); last="battery" }
/HSA.*GW.?$/		{ caps["HSA"] += $(NF-1); last="HSA" }
/EGS.*GW.?$/		{ caps["EGS"] += $(NF-1); last="EGS" }
/PV.*GW.?$/		{ caps["PV"] += $(NF-1); last="PV" }
/wind.*GW.?$/		{ caps["wind"] += $(NF-1); last="wind" }
/ S?CST.*GW.?$/		{ caps["CST"] += $(NF-1); last="CST" }
/ hydro.*GW.?$/		{ caps["hydro"] += $(NF-1); last="hydro" }
/pumped-hydro.*GW.?$/	{ caps["PSH"] += $(NF-1); last="PSH" }
/PSH.*GW.?$/		{ caps["PSH"] += $(NF-1); last="PSH" }
/ GT.*GW.?$/		{ caps["GT"] += $(NF-1); last="GT" }
/CCGT-CCS.*GW.?$/	{ caps["CCGT-CCS"] += $(NF-1); last="CCGT-CCS" }
/CCGT .*GW.?$/		{ caps["CCGT"] += $(NF-1); last="CCGT" }
/coal.*GW.?$/		{ caps["Coal"] += $(NF-1); last="Coal" }
/Coal-CCS.*GW.?$/	{ caps["Coal-CCS"] += $(NF-1); last="Coal-CCS" }
/OCGT.*GW.?$/		{ caps["OCGT"] += $(NF-1); last="OCGT" }
/diesel.*GW.?$/		{ caps["diesel"] += $(NF-1); last="diesel" }
/(DR|demand).*GW.?$/	{ caps["DR"] += $(NF-1); last="DR" }

/supplied.*TWh/		{ energy[last] += $2 }

/spilled.*TWh/		{ surplus += $5 }	# may be "spilled" in old log files
/surplus.*TWh/		{ surplus += $7 }	# now it's "surplus"
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
		    energy[c], energy[c] / total_demand, \
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
