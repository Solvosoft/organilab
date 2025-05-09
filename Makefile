.PHONY: help clean clean-pyc clean-build list test  docs release sdist
setup_version := `python src/organilab/__init__.py`
current_path := `pwd`
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
	cd src && python manage.py test  --no-input --exclude-tag=selenium

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

build_docker: clean trans
	docker build  -t organilab:$(setup_version)  .

release: clean trans builddocker

dist:
	#echo $(setup_version)
	git tag -a "v$(setup_version)" -m "Bump version $(setup_version)"
	git push origin "refs/tags/v$(setup_version)"

start:
	cd src && python manage.py migrate
	python manage.py init_checks
	python manage.py load_urlname_permissions



docs_full:
	cd src && python manage.py test  --no-input --tag=selenium && cd ..
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	pip install 'sphinx<7' sphinx-rtd-theme==1.2.2
	sphinx-build -b linkcheck ./docs/source ./docs/build/
	sphinx-build -b html ./docs/source ./docs/build/

build_docker_selenium:
	docker build -f docker/Dockerfile.selenium -t organilabselenium:$(setup_version)  .

run_docker_selenium:
	 docker run --network="host"  -v $(current_path)/src:/organilab/src  -v $(current_path)/fixtures:/organilab/fixtures -v $(current_path)/docs:/organilab/docs  -ti organilabselenium:$(setup_version) $(run)


database_config:
	cd src && python manage.py migrate && python manage.py init_checks && python manage.py load_urlname_permissions
