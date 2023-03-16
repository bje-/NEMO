all: venv

# define the name of the virtual environment directory
VENV=myenv

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	./$(VENV)/bin/pip install -r requirements.txt

# env is a shortcut target
venv: $(VENV)/bin/activate

COVRUN=coverage run -a --source=. --omit=setup.py

envset:
	test -n "$$VIRTUAL_ENV" || (echo "Python env is not activated" && false)

check:  envset flake8
	PYTHONOPTIMIZE=0 pytest --cov=awklite --cov nemo --doctest-modules

coverage: replay.json replay-noscenario.json replay-nocost.json
	$(COVRUN) evolve --list-scenarios > /dev/null
	#  these tests are needed because we need to control external
	#  environment variables
	NEMORC=nemo.cfg $(COVRUN) evolve -g1 -s __one_ccgt__ > /dev/null
	unset NEMORC && $(COVRUN) evolve -g1 -s __one_ccgt__ > /dev/null
	unset DISPLAY && $(COVRUN) evolve -g1 -s __one_ccgt__ > /dev/null
	if test -f trace.out; then rm trace.out; fi
	$(COVRUN) evolve -v --lambda 2 -g1 -s __one_ccgt__ \
		--trace-file=trace.out --emissions-limit=0 \
		--fossil-limit=0.1 --reserves=1000 \
		--reliability-std=0.002 --min-regional-generation=0.5 \
		-d scale:10 -d scaletwh:100 -d scalex:0:6:10 > /dev/null
	test -f trace.out && rm trace.out
	$(COVRUN) replay -f replay.json -v -v > /dev/null
	$(COVRUN) replay -f replay-noscenario.json -v > /dev/null || true
	$(COVRUN) replay -f replay-nocost.json -v > /dev/null || true
	$(COVRUN) evolve -g1 -s __one_ccgt__ -p > /dev/null
	$(COVRUN) replay -p -f replay.json > /dev/null
	rm results.json
	rm replay.json replay-noscenario.json replay-nocost.json
	make html

.PHONY: html

html:
	coverage html

replay.json:
	printf "# %s\n%s\n\n" "comment line" "malformed line" >> $@
	printf '{"options": {"carbon_price": 0, "ccs_storage_costs": 27, "gas_price": 11,' >> $@
	printf ' "coal_price": 2, "costs": "Null", "discount_rate": 0.05, "supply_scenario": "__one_ccgt__",' >> $@
	printf ' "nsp_limit": 0.75, "demand_modifier": ["unchanged"]}, "parameters": [1]}\n' >> $@

replay-noscenario.json: replay.json
	sed 's/__one_ccgt__/noexist/' < $< > $@

replay-nocost.json: replay.json
	sed 's/Null/noexist/' < $< > $@

stub.py:
	printf 'import nemo\n' > $@
	printf 'c = nemo.Context()\n' >> $@
	printf 'nemo.run(c)\n' >> $@

nemo.prof: stub.py
	python3 -m cProfile -o $@ $<

prof: nemo.prof
	snakeviz $<

lineprof: stub.py
	kernprof -v -l stub.py

flake8: envset
	flake8 evolve replay summary awklite nemo tests --ignore=N801

LINTSRC=evolve replay summary $(wildcard *.py awklite/*.py nemo/*.py tests/*.py)

pylint:
	pylint --enable=useless-suppression $(LINTSRC)

lint:	envset flake8 pylint
	codespell -d -L fom,hsa,trough $(LINTSRC) || true
	isort --check $(LINTSRC)
	pylama $(LINTSRC)
	-vulture --min-confidence=70 $(LINTSRC)
	bandit -qq -s B101 $(LINTSRC)
	pydocstyle $(LINTSRC)

coveralls:
	coveralls

dist:
	python3 setup.py sdist bdist_wheel

upload: dist
	twine upload dist/*

pdoc:
	pdoc3 --force --html nemo

clean:
	-rm -r dist build *.egg-info
	-rm -r .coverage htmlcov
	-rm replay.json replay-noscenario.json replay-nocost.json
	-rm *.pyc tests/*.pyc nemo.prof stub.py stub.py.lprof
