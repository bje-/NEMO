# Copyright (C) 2013, 2014 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

BEGIN {
    PROCINFO["sorted_in"] = "@ind_num_asc"
    merit[0] = "HSA"
    merit[1] = "EGS"
    merit[2] = "PV"
    merit[3] = "wind"
    merit[4] = "CST"
    merit[5] = "Coal"
    merit[6] = "Coal-CCS"
    merit[7] = "CCGT"
    merit[8] = "CCGT-CCS"
    merit[9] = "hydro"
    merit[10] = "PSH"
    merit[11] = "GT"
    merit[12] = "OCGT"
    merit[13] = "DR"
    # assume 8760 timesteps unless specified in the simulation output
    timesteps = 8760
}

/HSA.*GW.?$/		{ caps["HSA"] += $(NF-1); last="HSA" }
/EGS.*GW.?$/		{ caps["EGS"] += $(NF-1); last="EGS" }
/PV.*GW.?$/		{ caps["PV"] += $(NF-1); last="PV" }
/wind.*GW.?$/		{ caps["wind"] += $(NF-1); last="wind" }
/ S?CST.*GW.?$/		{ caps["CST"] += $(NF-1); last="CST" }
/ hydro.*GW.?$/		{ caps["hydro"] += $(NF-1); last="hydro" }
/pumped-hydro.*GW.?$/	{ caps["PSH"] += $(NF-1); last="PSH" }
/ GT.*GW.?$/		{ caps["GT"] += $(NF-1); last="GT" }
/CCGT-CCS.*GW.?$/	{ caps["CCGT-CCS"] += $(NF-1); last="CCGT-CCS" }
/CCGT .*GW.?$/		{ caps["CCGT"] += $(NF-1); last="CCGT" }
/coal.*GW.?$/		{ caps["Coal"] += $(NF-1); last="Coal" }
/Coal-CCS.*GW.?$/	{ caps["Coal-CCS"] += $(NF-1); last="Coal-CCS" }
/OCGT.*GW.?$/		{ caps["OCGT"] += $(NF-1); last="OCGT" }
/(DR|demand).*GW.?$/	{ caps["DR"] += $(NF-1); last="DR" }
/supplied.*TWh/		{ energy[last] += $2 }
/spilled.*TWh/		{ surplus += $5 }
/Score:/		{ cost = $2 }
/Timesteps:/		{ timesteps = $2 }
/^{.*}/			{ params = $0 }

/Demand energy:/ {
    i++
    total_demand = $(NF-1)
    total_capacity = 0
    for (c in caps) {
    	total_capacity += caps[c]
    }
    printf ("# scenario %d\n", i)
    if (params != "")
       printf ("# options %s\n", params)
    printf ("# demand %.2f TWh\n", total_demand)
    printf ("# score %.2f $/MWh\n", cost)
    printf ("# tech\t  GW\tshare\t  TWh\tshare\tCF\n")
    for (m in merit) {
	c = merit[m]
	if (caps[c] != "")
	    printf ("%s\t%4.1f\t%.3f\t%5.1f\t%.3f\t%02.3f\n", c, \
		    caps[c], (float) caps[c] / total_capacity, \
		    energy[c], (float) energy[c] / total_demand, \
		    (caps[c] > 0) ? (float) (energy[c] * 1000) / (caps[c] * timesteps) : 0)
    }
    if (surplus > 0)
	printf ("surplus\t%5s\t%5s\t%5.1f\t%.3f\n", "N/A", "N/A", surplus, surplus / total_demand)

    surplus = 0
    params = null
    delete caps
    delete energy
    printf ("\n\n")
}
