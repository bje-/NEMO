all:

OMIT=nemo/priodict.py,nemo/dijkstra.py
COVRUN=coverage run -a --source=. --omit=$(OMIT)

check:  replay.json flake8
	python3 -m nose --with-doctest --with-coverage --cover-package=nemo

coverage: replay.json
	$(COVRUN) evolve --list-scenarios > /dev/null
	$(COVRUN) evolve --lambda 2 -g1 -s theworks --costs=Null -d scale:10 -d scaletwh:100 -d scalex:0:6:10 > /dev/null
	NEMORC=nemo.cfg $(COVRUN) evolve -g1 -s __one_ccgt__ > /dev/null
	$(COVRUN) evolve --lambda 2 -g1 -s __one_ccgt__ --fossil-limit=0 > /dev/null
	$(COVRUN) evolve --lambda 2 -g1 -s ccgt --emissions-limit=0 --fossil-limit=0.1 --reserves=1000 --costs=PGTR2030 > /dev/null
	if test -f trace.out; then rm trace.out; fi
	$(COVRUN) evolve --lambda 2 -g1 --reliability-std=0.002 --min-regional-generation=0.5 --seed 0 --trace-file=trace.out --bioenergy-limit=0 -t --costs=AETA2013-in2030-high -v > /dev/null
	$(COVRUN) replay -t -f replay.json -v > /dev/null
	rm trace.out results.json replay.json
	coverage html --omit=$(OMIT)

replay.json:
	printf "# %s\n%s\n\n" "comment line" "malformed line" >> $@
	printf '{"options": {"carbon_price": 0, "ccs_storage_costs": 27, "gas_price": 11,' >> $@
	printf ' "coal_price": 2, "costs": "Null", "discount_rate": 0.05, "supply_scenario": "__one_ccgt__",' >> $@
	printf ' "nsp_limit": 0.75, "demand_modifier": ["unchanged"]}, "parameters": [1]}\n' >> $@

nemo.prof:
	python3 -m cProfile -o $@ stub.py

prof: nemo.prof
	python3 -m snakeviz $<

lineprof:
	python3 -m kernprof -v -l stub.py

flake8:
	python3 -m flake8 nemo --max-line-length=127 --ignore=N801

lint:
	python3 -m pylint $(filter-out nemo/priodict.py nemo/dijkstra.py, $(wildcard *.py nemo/*.py))

coveralls:
	coveralls

docker:
	docker build -t nemo .

dist:
	python3 setup.py sdist bdist_wheel

clean:
	-rm -rf dist build *.egg-info
	-rm -rf .coverage htmlcov replay.json exchanges.json
	-rm *.pyc tests/*.pyc nemo.prof stub.py.lprof
