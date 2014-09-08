# Copyright (C) 2014 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Custom mutator(s)."""

from pyevolve import Consts
from pyevolve import Util
from random import randint, gauss


def gaussian_mutator(genome, **arguments):
    """My own allele mutator based on G1DListMutatorRealGaussian.

    Accepts the parameter *gauss_mu* and the *gauss_sigma* which
    respectively represents the mean and the std. dev. of the random
    distribution.
    """
    if arguments["pmut"] <= 0.0:
        return 0
    listSize = len(genome)
    mutations = arguments["pmut"] * listSize

    mu = genome.getParam("gauss_mu")
    sigma = genome.getParam("gauss_sigma")
    if mu is None:
        mu = Consts.CDefG1DListMutRealMU
    if sigma is None:
        sigma = Consts.CDefG1DListMutRealSIGMA

    allele = genome.getParam("allele", None)
    if allele is None:
        Util.raiseException("to use this mutator, you must specify the 'allele' parameter", TypeError)

    if mutations < 1.0:
        mutations = 0
        for it in xrange(listSize):
            if Util.randomFlipCoin(arguments["pmut"]):
                final_value = genome[it] + gauss(mu, sigma)
                assert len(allele[it].beginEnd) == 1, "only single ranges are supported"
                rangemin, rangemax = allele[it].beginEnd[0]
                final_value = min(final_value, rangemax)
                final_value = max(final_value, rangemin)
                genome[it] = final_value
                mutations += 1
    else:
        for it in xrange(int(round(mutations))):
            which_gene = randint(0, listSize - 1)
            final_value = genome[which_gene] + gauss(mu, sigma)
            assert len(allele[which_gene].beginEnd) == 1, "only single ranges are supported"
            rangemin, rangemax = allele[which_gene].beginEnd[0]
            final_value = min(final_value, rangemax)
            final_value = max(final_value, rangemin)
            genome[which_gene] = final_value
    return int(mutations)
