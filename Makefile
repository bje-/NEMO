all:

OMIT=nemo/priodict.py,nemo/dijkstra.py
COVRUN=coverage run -a --source=. --omit=$(OMIT)

check:  replay.json flake8
	nosetests -I '(evolve|replay|setup).py' --with-doctest --with-coverage --cover-package=.

coverage: replay.json
	$(COVRUN) evolve.py --list-scenarios > /dev/null
	$(COVRUN) evolve.py --lambda 2 -g1 -s theworks --costs=Null -d scale:10 -d scaletwh:100 -d scalex:0:6:10 > /dev/null
	NEMORC=nemo.cfg $(COVRUN) evolve.py -g1 -s __one_ccgt__ > /dev/null
	$(COVRUN) evolve.py --lambda 2 -g1 -s __one_ccgt__ --fossil-limit=0 > /dev/null
	$(COVRUN) evolve.py --lambda 2 -g1 -s ccgt --emissions-limit=0 --fossil-limit=0.1 --reserves=1000 --costs=PGTR2030 > /dev/null
	if test -f trace.out; then rm trace.out; fi
	$(COVRUN) evolve.py --lambda 2 -g1 --reliability-std=0.002 --min-regional-generation=0.5 --seed 0 --trace-file=trace.out --bioenergy-limit=0 -t --costs=AETA2013-in2030-high -v > /dev/null
	$(COVRUN) replay.py -t -f replay.json -v > /dev/null
	rm trace.out results.json replay.json
	coverage html --omit=$(OMIT)

replay.json:
	echo "# comment line" >> $@
	echo "malformed line" >> $@
	echo >> $@
	echo -n '{"options": {"carbon_price": 0, "ccs_storage_costs": 27, "gas_price": 11,' >> $@
	echo -n ' "coal_price": 2, "costs": "Null", "discount_rate": 0.05, "supply_scenario": "__one_ccgt__",' >> $@
	echo    ' "nsp_limit": 0.75, "demand_modifier": ["unchanged"]}, "parameters": [1]}' >> $@

nem.prof:
	python -m cProfile -o $@ profile.py

prof: nem.prof
	python /usr/lib/python2.7/dist-packages/runsnakerun/runsnake.py $<

lineprof:
	kernprof -v -l profile.py

flake8:
	python -m flake8 --ignore=E501,N *.py */*.py

lint:
	pylint $(filter-out nemo/priodict.py nemo/dijkstra.py, $(wildcard *.py nemo/*.py))

coveralls:
	coveralls

docker:
	 docker build -t nemo .

pypi:
	python setup.py sdist upload -r pypi

clean:
	-rm -rf .coverage htmlcov replay.json exchanges.json
	-rm *.pyc tests/*.pyc nem.prof profile.py.lprof
