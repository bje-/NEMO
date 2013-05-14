#!/bin/sh

PYTHON=python26
EVOLVE=~/code/evolve.py
EVOPTS="-g 10 -q"

# scale: scenario
for s in `seq -10 -10 -90`; do
    $PYTHON $EVOLVE $EVOPTS -d scale:$s
done

# shift: scenario
for s in `seq 100 100 1000`; do
    $PYTHON $EVOLVE $EVOPTS -d shift:$n:18:12
done
