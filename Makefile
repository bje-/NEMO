all:

COVRUN=coverage run -a --source=. --omit=priodict.py,dijkstra.py

check:  replay.data
	nosetests -I '(evolve|replay).py' --with-doctest --with-coverage --cover-package=.
	$(COVRUN) evolve.py --list-scenarios > /dev/null
	$(COVRUN) evolve.py --lambda 2 -g1 -s theworks -d scale:10 -d scaletwh:100 -d scalex:0:6:10 > /dev/null
	NEMORC=default.cfg $(COVRUN) evolve.py -g1 -s __one_ccgt__ > /dev/null
	$(COVRUN) evolve.py --lambda 2 -g1 -s __one_ccgt__ --fossil-limit=0 > /dev/null
	$(COVRUN) evolve.py --lambda 2 -g1 -s ccgt --emissions-limit=0 --fossil-limit=0.1 --reserves=1000 --costs=PGTR2030 > /dev/null
	if test -f trace.out; then rm trace.out; fi
	$(COVRUN) evolve.py --lambda 2 -g1 --reliability-std=0.002 --min-regional-generation=0.5 --seed 0 --trace-file=trace.out --bioenergy-limit=0 -t --costs=AETA2013-in2030-high -d unchanged -v > /dev/null
	$(COVRUN) replay.py -t -d unchanged -f replay.data -v > /dev/null
	rm replay.data
	coverage html

replay.data:
	echo "# comment line" >> $@
	echo "malformed line" >> $@
	echo >> $@
	echo "__one_ccgt__: [1]" >> $@

nem.prof:
	python -m cProfile -o $@ profile.py

prof: nem.prof
	python /usr/lib/python2.7/dist-packages/runsnakerun/runsnake.py $<

lineprof:
	kernprof.py -v -l profile.py

flake8:
	python -m flake8 --ignore=E266,E501,N801,N803,N806 --exclude=priodict.py,dijkstra.py *.py tests/*.py

lint:	flake8
	pylint $(filter-out priodict.py dijkstra.py, $(wildcard *.py))

coverage:
	coveralls

docker:
	 docker build -t nemo .

clean:
	rm -rf .coverage htmlcov replay.data
	rm *.pyc tests/*.pyc nem.prof profile.py.lprof
