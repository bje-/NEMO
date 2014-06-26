check:
	python tests.py -v

flake8:
	flake8 --ignore=E501 *.py

nem.prof:
	python -m cProfile -o $@ profile.py

prof: nem.prof
	python /usr/lib/python2.7/dist-packages/runsnakerun/runsnake.py $<

lineprof:
	kernprof.py -v -l profile.py

lint:
	pylint *.py

clean:
	rm *.pyc nem.prof profile.py.lprof
