.PHONY: help clean clean-pyc clean-build list test  docs release sdist

# Variables
setup_version := `python src/organilab/__init__.py`
current_path := `pwd`


##--------------------------------------------------------
## Help
##--------------------------------------------------------

help: ## Mostrar esta ayuda
	@echo
	@echo "Usage: make [target]"
	@echo
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo


##--------------------------------------------------------
## Project setup & server
##--------------------------------------------------------

start: ##  - run project local
	cd src && python manage.py migrate \
	&& python manage.py init_checks \
	&& python manage.py load_urlname_permissions

run_celery: ##  - run celery for development mode
	./run_celery.sh

database_config: ##  - init config data base
	cd src && python manage.py migrate && python manage.py init_checks && python manage.py load_urlname_permissions

run_docker_selenium: ##  - run project in docker with selenium
	 docker run --network="host"  -v $(current_path)/src:/organilab/src  -v $(current_path)/fixtures:/organilab/fixtures -v $(current_path)/docs:/organilab/docs  -ti organilabselenium:$(setup_version) $(run)

migrate: ## - makemigrations && migrate
	cd src && python manage.py makemigrations && \
	python manage.py migrate

requirements: ## - install all dependencies
	pip install -r requirements.txt

##--------------------------------------------------------
## Project build
##--------------------------------------------------------

clean-build: ##  - remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc: #  - remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

clean: ##  - remove build artifacts and remove Python file artifacts
	clean-build && clean-pyc

test: ##  - run tests quickly with the default Python
	cd src && python manage.py test  --no-input --exclude-tag=selenium

docs: ##  - generate Sphinx HTML documentation, including API docs
	pip install 'sphinx==8.2.3' sphinx-rtd-theme==3.0.2
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	sphinx-build -b linkcheck ./docs/source ./docs/build/
	sphinx-build -b html ./docs/source ./docs/build/

docs_full: ##  - generate full docs, Sphinx HTML documentation, including API docs
	cd src && python manage.py test  --no-input --tag=selenium && cd ..
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	pip install 'sphinx==8.2.3' sphinx-rtd-theme==3.0.2
	sphinx-build -b linkcheck ./docs/source ./docs/build/
	sphinx-build -b html ./docs/source ./docs/build/

messages: ##  - extract messages for translations
	cd src && django-admin makemessages --all --no-location --no-obsolete && django-admin makemessages -d djangojs -l es  --ignore *.min.js --no-location --no-obsolete

trans: ##  - compile messages of translations
	cd src && django-admin compilemessages --locale es

release: ##  - package and upload a release
	clean && trans && builddocker

dist: ##  - print current version of organilab
	#echo $(setup_version)
	git tag -a "v$(setup_version)" -m "Bump version $(setup_version)"
	git push origin "refs/tags/v$(setup_version)"

build_docker: ##  - build docker images
	clean trans && /
	docker pull python:3.13-trixie && /
	docker build  -t organilab:$(setup_version)  .

build_docker_selenium: ##  - build docker images with selenium
	docker build -f docker/Dockerfile.selenium -t organilabselenium:$(setup_version)  .

##--------------------------------------------------------
## Project utils
##--------------------------------------------------------
lint: ## - check style with flake8
	pycodestyle --exclude=*/migrations/*  --max-line-length=200 src
