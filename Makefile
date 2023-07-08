.PHONY: help clean clean-pyc clean-build list test  docs release sdist

djversion = $(python setup.py -V)
setupversion = $(awk -F "'" '{print $2}' src/organilab/__init__.py)

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package and upload a release"
	@echo "sdist - package"

clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

lint:
	pycodestyle --max-line-length=88 src

test:
	cd src && python manage.py test

docs:
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	pip install 'sphinx<7' sphinx-rtd-theme==1.2.2
	sphinx-build -b linkcheck ./docs/source _build/
	sphinx-build -b html ./docs/source _build/

makemessage:
	cd src && django-admin makemessages --all --no-location --no-obsolete && django-admin makemessages -d djangojs -l es  --ignore *.min.js

trans:
	cd src && django-admin compilemessages --locale es

release: sdist
	git tag -a "v`python setup.py --version`" -m "Bump version `python setup.py --version`"
	git push origin "v`python setup.py --version`"
	twine upload -s dist/*

sdist: clean
	cd src && python manage.py makemigrations && django-admin compilemessages -l es
	python3 -m build
	ls -l dist

