check:
	python tests.py -v

lint:
	pep8 --ignore=E111,E501 *.py

clean:
	rm *.pyc
