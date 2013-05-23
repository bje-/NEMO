#! /bin/bash

PYTHON=python26
EVOLVE=~/code/evolve.py
EVOPTS="-m 0.2 -p 10 -g 500"

# mmm, bash associative arrays

# no change to demand (baseline)
scenario[0]=""

# scale up demand
scenario[1]="-d scale:+10"
scenario[2]="-d scale:+20"
scenario[3]="-d scale:+30"
scenario[4]="-d scale:+40"
scenario[5]="-d scale:+50"

# scale down demand
scenario[6]="-d scale:-2"
scenario[7]="-d scale:-4"
scenario[8]="-d scale:-6"
scenario[9]="-d scale:-8"
scenario[10]="-d scale:-10"

# move 2GW of morning and evening peaks to noon
scenario[11]="-d shift:2000:8:12 -d shift:2000:18:12"

# scenario 11, plus 5% shaved off top 10 peaks
scenario[12]="${scenario[11]} -d npeaks:10:-5"

# scenario 11, plus 10% shaved off top 10 peaks
scenario[13]="${scenario[11]} -d npeaks:10:-10"

# scenario 11, plus 15% shaved off top 10 peaks
scenario[14]="${scenario[11]} -d npeaks:10:-15"

# scenario 11, plus 20% shaved off top 10 peaks
scenario[15]="${scenario[11]} -d npeaks:10:-20"

# scenario 11, plus 5% shaved off top 50 peaks
scenario[16]="${scenario[11]} -d npeaks:50:-5"

# scenario 11, plus 5% shaved off top 100 peaks
scenario[17]="${scenario[11]} -d npeaks:100:-5"

# scenario 11, plus a 5% demand reduction
scenario[18]="${scenario[11]} -d scale:-5"

# move morning and evening peaks around noon (3GW in each hour)
scenario[19]="-d shift:3000:7:10 shift:3000:8:12 shift:3000:9:11 shift:3000:17:12 shift:3000:18:13 shift:3000:19:14" 

for n in `seq 0 19` ; do
    echo "demand scenario $n"
    $PYTHON $EVOLVE $EVOPTS -s re100 ${scenario[$n]}
done
