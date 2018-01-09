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

docs:
	rm -f docs/pewpew.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ pewpew
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

install: clean
	python setup.py install

uninstall:
	pip uninstall pewpew

docserver:
	cd docs/_build/html && python -m SimpleHTTPServer 9000

venv:
	python3 -m venv .pewpew

workon:
	source ./.pewpew/bin/activate
