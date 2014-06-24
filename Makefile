check:
	python tests.py -v

flake8:
	flake8 --ignore=E501 *.py

lint:
	pylint *.py

clean:
	rm *.pyc
