.PHONY: clean	clean-build clean-pyc docs help

clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

test:
	pytest --flake8

travis_test:
	flake8 pewpew
	pytest .

docs:
	rm -f docs/pewpew.rst
	rm -f docs/modules.rst
	pip install -r requirements_doc.txt
	sphinx-apidoc -o docs/ pewpew
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

install: clean
	pip install -r requirements.txt
	python setup.py install

uninstall:
	pip uninstall pewpew

dev_install: install
	pip install -r requirements_dev.txt

docserver:
	cd docs/_build/html && python -m http.server 9000

venv:
	python3 -m venv .pewpew

workon:
	source ./.pewpew/bin/activate
