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

check:  envset flake8 ruff test

test:	envset
	PYTHONPATH=. pytest --mpl --cov=nemo --doctest-modules

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
		--reliability-std=0.002 --min-regional-generation=0.5 > /dev/null
	test -f trace.out && rm trace.out
	$(COVRUN) replay -f replay.json -v -v > /dev/null
	$(COVRUN) replay -f replay-noscenario.json -v > /dev/null || true
	$(COVRUN) replay -f replay-nocost.json -v > /dev/null || true
	$(COVRUN) evolve -g1 -s __one_ccgt__ -p > /dev/null
	$(COVRUN) evolve -g1 -s __one_ccgt__ > output.txt
	$(COVRUN) summary < output.txt
	$(COVRUN) replay -p -f replay.json > /dev/null
	rm results.json output.txt
	rm replay.json replay-noscenario.json replay-nocost.json
	make html

.PHONY: html

html:
	coverage html

replay.json:
	printf "# %s\n%s\n\n" "comment line" "malformed line" >> $@
	printf '{"options": {"carbon_price": 0, "ccs_storage_costs": 27, "gas_price": 11,' >> $@
	printf ' "coal_price": 2, "costs": "Null", "discount_rate": 0.05, "supply_scenario": "__one_ccgt__",' >> $@
	printf ' "nsp_limit": 0.75, "parameters": [1]}\n' >> $@

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

LINTSRC=evolve replay summary $(wildcard *.py awklite/*.py nemo/*.py tests/*.py)

flake8: envset
	flake8 $(LINTSRC) --ignore=N801

ruff:	envset
	ruff check --select ALL --ignore=Q000,ARG002,T201,ANN,N801,SLF,PLR,PT,INP \
		--output-format=concise $(LINTSRC)

pylint:
	pylint --enable=useless-suppression $(LINTSRC)

lint:	envset flake8 ruff pylint
	codespell -d -L assertin,fom,hsa,trough,harge $(LINTSRC) || true
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
