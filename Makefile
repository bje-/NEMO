all:

COVRUN=python-coverage run -a --source .

check:  replay.data
	nosetests -I '(evolve|replay).py' --with-doctest --with-coverage --cover-package=.
	$(COVRUN) evolve.py --list-scenarios > /dev/null
	$(COVRUN) evolve.py -g1 -s __one_ccgt__ > /dev/null
	NEMORC=default.cfg $(COVRUN) evolve.py --lambda 2 -g1 -s __one_ccgt__ > /dev/null
	# Use lots of the miscellaneous options.
	$(COVRUN) evolve.py -v --lambda 2 -g1 --min-regional-generation=0.5 --seed 0 --trace-file=trace.out --emissions-limit=100 --fossil-limit=1.0 -t --costs=AETA2013-in2030-high --coal-ccs-costs=20 -d unchanged > /dev/null
	$(COVRUN) replay.py -f replay.data -v > /dev/null
	rm replay.data
	make html

nem.prof:
	python -m cProfile -o $@ profile.py

prof: nem.prof
	python /usr/lib/python2.7/dist-packages/runsnakerun/runsnake.py $<

lineprof:
	kernprof.py -v -l profile.py

flake8:
	flake8 --ignore=E501 *.py tests/*.py

lint:	flake8
	pylint *.py

html:
	python-coverage html

html-upload:
	rsync -az --delete htmlcov/ bilbo:~/public_html/nemo/coverage

replay.data:
	echo "# comment line" >> $@
	echo "malformed line" >> $@
	echo >> $@
	echo "List: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]" >> $@

clean:
	rm -rf .coverage htmlcov replay.data
	rm *.pyc nem.prof profile.py.lprof
