.PHONY: help clean clean-pyc clean-build list test  docs release sdist
setup_version := `python src/organilab/__init__.py`

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "run_celery - run celery for development mode"
	@echo "messages - extract messages for translations"
	@echo "trans - compile messages of translations"
	@echo "build_docker - build docker images"
	@echo "release - package and upload a release"
	@echo "dist - print current version of organilab"

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
	cd src && python manage.py test  --no-input

docs:
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	pip install 'sphinx<7' sphinx-rtd-theme==1.2.2
	sphinx-build -b linkcheck ./docs/source ./docs/build/
	sphinx-build -b html ./docs/source ./docs/build/

run_celery:
	./run_celery.sh

messages:
	cd src && django-admin makemessages --all --no-location --no-obsolete && django-admin makemessages -d djangojs -l es  --ignore *.min.js --no-location --no-obsolete

trans:
	cd src && django-admin compilemessages --locale es

build_docker:
	docker build  -t organilab:$(setup_version)  .

release: clean trans builddocker

dist:
	echo $(setup_version)

