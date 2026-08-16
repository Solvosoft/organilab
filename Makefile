.PHONY: help clean clean-pyc clean-build list test test-parallel test-selenium test-selenium-4 test-selenium-xvfb docs release sdist

# Variables
setup_version := `python3 src/organilab/__init__.py`
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

test-requirements: ## - install all test dependencies
	pip install -r test_requirements.txt

create-profile: ## - create user and user profile
	cd src && python manage.py createsuperuser && \
	python manage.py shell -c "\
	from auth_and_perms.models import Profile; \
	from django.contrib.auth.models import User; \
	user = User.objects.last(); \
	Profile.objects.get_or_create(user=user)"

check-move-organization-data: ## Validate organization migration (Example: make check-move-organization-data FROM=5 TO=9)
	@echo "Validating organization data migration..."
	@echo "FROM=$(FROM) → TO=$(TO)"
	cd src && python manage.py move_organization_data --from-org $(FROM) --to-org $(TO) --dry-run


move-organization-data: ## Execute organization migration (Example: make move-move-organization-data FROM=5 TO=9)
	@echo "You are about to move data from one organization to another"
	@echo "FROM=$(FROM) → TO=$(TO)"
	@read -p "Do you want to continue? [y/N]: " confirm; \
	if [ "$$confirm" = "y" ]; then \
		cd src && python manage.py move_organization_data --from-org $(FROM) --to-org $(TO); \
	else \
		echo "Operation cancelled"; \
	fi

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
	$(MAKE) clean-build && $(MAKE)  clean-pyc

test: ##  - run tests quickly with the default Python
	cd src && python manage.py test  --no-input --exclude-tag=selenium

test-parallel: ## - run tests in parallel (auto-detect workers)
	cd src && python manage.py test --no-input --exclude-tag=selenium --parallel -v 2

single-test: ## Run Django tests (optional: TEST=path.to.test, example: make single-test TEST=laboratory.tests.test_provider.ProviderViewTest)
	cd src && python manage.py test $(TEST) --no-input --exclude-tag=selenium

test-selenium: ## Run Selenium tests (optional: TEST=path.to.test, example: make test-selenium TEST=laboratory.tests.selenium_tests)
	cd src && python manage.py test $(or $(TEST),) --tag=selenium --no-input --parallel -v 2

test-selenium-parallel: ## Run Selenium tests with 4 workers (optional: TEST=path.to.test)
	cd src && python manage.py test $(or $(TEST),) --tag=selenium --no-input --parallel 20 -v 2

test-selenium-xvfb: ## Run Selenium tests with virtual display via xvfb-run (optional: TEST=path.to.test)
	xvfb-run --auto-servernum --server-args="-screen 0 1280x720x24" sh -c "cd src && python manage.py test $(or $(TEST),) --tag=selenium --no-input --parallel 12 -v 2"

test-selenium-fast: ## Run Selenium tests without GIF generation (fast mode, optional: TEST=path.to.test)
	cd src && GENERATE_SCREENSHOTS=False python manage.py test $(or $(TEST),) --tag=selenium --no-input --parallel -v 2

test-selenium-single-fast: ## Run a single Selenium test without GIF generation (TEST=path.to.test)
	cd src && GENERATE_SCREENSHOTS=False python manage.py test $(TEST) --tag=selenium --no-input -v 2

test-selenium-dev: ## Run Selenium tests fast, headless and reusing the DB (optional: TEST=path.to.test)
	xvfb-run --auto-servernum --server-args="-screen 0 1280x720x24" \
		sh -c "cd src && GENERATE_SCREENSHOTS=False python manage.py test $(or $(TEST),) --tag=selenium --no-input --keepdb --parallel -v 2"


docs: clean ##  - generate Sphinx HTML documentation, including API docs
	pip install 'sphinx==8.2.3' sphinx-rtd-theme==3.0.2 sphinxcontrib-video==0.4.2
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	sphinx-build -b linkcheck ./docs/source ./docs/build/
	sphinx-build -b html ./docs/source ./docs/build/
	python docs/fix_capacitacion_images.py

docs_full: ##  - generate full docs, Sphinx HTML documentation, including API docs
	xvfb-run --auto-servernum --server-args="-screen 0 1280x720x24" sh -c "cd src && python manage.py test  --no-input --tag=selenium --parallel 12"
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	pip install 'sphinx==8.2.3' sphinx-rtd-theme==3.0.2 sphinxcontrib-video==0.4.2
	sphinx-build -b linkcheck ./docs/source ./docs/build/
	sphinx-build -b html ./docs/source ./docs/build/
	python docs/fix_capacitacion_images.py

messages: ##  - extract messages for translations
	cd src && django-admin makemessages --all --no-location --no-obsolete && django-admin makemessages -d djangojs -l es  --ignore *.min.js --no-location --no-obsolete

trans: ##  - compile messages of translations
	cd src && django-admin compilemessages --locale es
	cd src && django-admin compilemessages --locale en

release: ##  - package and upload a release
	$(MAKE) clean && $(MAKE) trans && builddocker

dist: ##  - print current version of organilab
	#echo $(setup_version)
	git tag -a "v$(setup_version)" -m "Bump version $(setup_version)"
	git push origin "refs/tags/v$(setup_version)"

build_docker: ##  - build docker images
	$(MAKE) docs
	docker pull python:3.13-trixie
	docker pull python:3.13-slim-trixie
	docker build --no-cache  -t organilab:$(setup_version) -t organilab:latest .

build_docker_selenium: ##  - build docker images with selenium
	docker build -f docker/Dockerfile.selenium -t organilabselenium:$(setup_version)  .

load-perms: ## - load permissions
	$(MAKE) trans  && cd src  && python manage.py load_urlname_permissions

##--------------------------------------------------------
## Project utils
##--------------------------------------------------------
lint: ## - check style with flake8
	pycodestyle --exclude=*/migrations/*  --max-line-length=200 src

update_sds: ## - update SDS files in batches
	cd src && python manage.py update_sds --batch-size 10 --batch-delay 30 --delay 2

clean_orphan_media: ## - elimina archivos en MEDIA_ROOT no referenciados en la BD
	cd src && python manage.py clean_orphan_media
