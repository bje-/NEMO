# Copyright (C) 2017 IT Power (Australia)
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

FROM ubuntu:latest
MAINTAINER bje@air.net.au
RUN apt-get update
RUN apt-get -y install python-pip python-numpy python-matplotlib git
RUN pip install --upgrade pip
RUN pip install scoop
RUN pip install deap
# Force Matplotlib to build the fontcache upfront.
RUN python -c 'import matplotlib.pyplot'
RUN git clone git://git.ozlabs.org/nemo.git /home/nemo
CMD cd /home/nemo && python -m scoop evolve.py
