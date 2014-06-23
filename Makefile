check:
	python tests.py -v

pep8:
	pep8 --ignore=E501 *.py

lint:
	pylint *.py

clean:
	rm *.pyc
