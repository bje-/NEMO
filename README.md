# National Electricity Market Optimiser (NEMO)

![Build status
badge](https://github.com/bje-/NEMO/actions/workflows/buildtest.yml/badge.svg)
[![Coverage
Status](https://coveralls.io/repos/github/bje-/NEMO/badge.svg?branch=master)](https://coveralls.io/github/bje-/NEMO?branch=master)
[![CodeFactor](https://www.codefactor.io/repository/github/bje-/nemo/badge)](https://www.codefactor.io/repository/github/bje-/nemo)
[![Bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

NEMO is a chronological production-cost and capacity expansion model
for testing and optimising different portfolios of renewable and
fossil electricity generation technologies. It has been developed and
improved over the past decade and has a growing number of users.

![NEMO dispatch results](http://nemo.ozlabs.org/theworks.png)

It requires no proprietary software to run, making it particularly
accessible to the governments of developing countries, academic
researchers and students. The model is available for others to inspect
and, importantly, to validate the results.

## Installation

```bash
pip install nemopt
```

## Features

For a set of given (or default) generation or demand traces, users can:

  1. Specify & simulate a custom resource mix, or;
  2. "Evolve" a resource mix using pre-configured scenarios, or
     configure their own scenario

### Evolution strategy

The benefit of an evolutionary approach is that NEMO in searching for
the least-cost solution, NEMO can also explore "near-optimal" resource
mixes.

NEMO no longer uses genetic algorithms, but has adopted the better
performing [CMA-ES](https://en.wikipedia.org/wiki/CMA-ES) method.

### Resource models

NEMO has models for the following resources: wind (including
offshore), photovoltaics, concentrating solar power (CSP), hydropower,
pumped storage hydro, biomass, black coal, open cycle gas turbines
(OCGTs), combined cycle gas turbines (CCGTs), diesel generators, coal
with carbon capture and storage (CCS), CCGT with CCS, geothermal,
demand response, batteries, electrolysers, hydrogen fuelled gas
turbines, and more.

## Documentation

Documentation is progressively being added to a [User's
Guide](https://nbviewer.org/urls/nemo.ozlabs.org/guide.ipynb?flush_cache=1)
in the form of a Jupyter notebook.

[API documentation](http://nemo.ozlabs.org/pdoc/index.html) exists for
the `nemo` module. This is useful when building new tools that use the
simulation framework.

The model is described in an Energy Policy paper titled [Least cost
100% renewable electricity scenarios in the Australian National
Electricity
Market](http://ceem.unsw.edu.au/sites/default/files/documents/LeastCostElectricityScenariosInPress2013.pdf)
by Elliston, MacGill and Diesendorf (2013).

## System requirements

NEMO should run on any operating system where Python 3 is available
(eg, Windows, Mac OS X, Linux). It utilises some add-on packages:

- [DEAP](https://deap.readthedocs.io/en/master/),
- [Gooey](https://pypi.org/project/Gooey/),
- [Matplotlib](http://matplotlib.org/),
  [Numpy](http://www.numpy.org/), [Pandas](http://pandas.pydata.org/)
  and
- [Pint](https://pint.readthedocs.io).

### Scaling up

For simple simulations or scripted sensitivity analyses, a laptop or
desktop PC will be adequate. However, for optimising larger systems, a
cluster of compute nodes is desirable. The model is scalable and you
can devote as many locally available CPU cores to the model as you
wish.

> #### Note
>
> Due to a lack of active development, support for
> [SCOOP](https://pypi.python.org/pypi/scoop) has been removed. It
> will be soon replaced with something like [Ray](https://ray.io/).

## Citation

If you use NEMO, please cite the following paper:

> Ben Elliston, Mark Diesendorf, Iain MacGill, [Simulations of
> scenarios with 100% renewable electricity in the Australian National
> Electricity
> Market](https://www.sciencedirect.com/science/article/pii/S0301421512002169?via=ihub#s0010),
> Energy Policy, Volume 45, 2012, Pages 606-613, ISSN 0301-4215,
> <https://doi.org/10.1016/j.enpol.2012.03.011>

## Community

The [nemo-devel](https://lists.ozlabs.org/listinfo/nemo-devel) mailing
list is where users and developers can correspond.

## Contributing

Enhancements and bug fixes are very welcome. Please report bugs in the
[issue tracker](https://github.com/bje-/NEMO/issues). Authors retain
copyright over their work.

## License

NEMO was first developed by [Dr Ben
Elliston](https://www.ceem.unsw.edu.au/staff/ben-elliston) in 2011 at
the [Collaboration for Energy and Environmental Markets, UNSW
Sydney](https://www.ceem.unsw.edu.au/).

NEMO is free software and the source code is licensed under the [GPL version 3 license](COPYING).

## Useful references

Australian cost data are taken from the [Australian Energy Technology
Assessments](https://www.industry.gov.au/Office-of-the-Chief-Economist/Publications/Pages/Australian-energy-technology-assessments.aspx)
(2012, 2013), the [Australian Power Generation Technology
Report](http://www.co2crc.com.au/publication-category/reports/) (2015)
and the CSIRO [GenCost
reports](https://data.csiro.au/collections/collection/CIcsiro:44228)
(2021, 2022). The GenCost reports provide the basis of the input cost
assumptions for the AEMO [Integrated System
Plan](https://aemo.com.au/en/energy-systems/major-publications/integrated-system-plan-isp).
Costs for other countries may be added in time.

Renewable energy trace data covering the Australian National
Electricity Market territory are taken from the AEMO 100% Renewables
Study. An accompanying
[report](http://content.webarchive.nla.gov.au/gov/wayback/20140211194248/http://www.climatechange.gov.au/sites/climatechange/files/files/reducing-carbon/APPENDIX3-ROAM-report-wind-solar-modelling.pdf)
describes the method of generating the traces.

## Acknowledgements

Early development of NEMO was financially supported by the [Australian
Renewable Energy Agency](http://www.arena.gov.au/) (ARENA). Thanks to
undergraduate and postgraduate student users at UNSW who have provided
valuable feedback on how to improve (and document!) the model.
