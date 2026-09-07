.PHONY: help clean clean-pyc clean-build list setup check-env venv-info url-inventory url-inventory-check test-urls test test-parallel test-selenium test-selenium-4 test-selenium-single test-selenium-xvfb test-selenium-bitacora docs release sdist

# Variables
ROOT_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
VENV ?= $(ROOT_DIR)/.venv
# Si el entorno virtual existe se usa siempre, sin necesidad de activarlo; si no,
# se cae al python del PATH para no romper quien ya trabaje dentro de otro venv.
PYTHON ?= $(shell test -x $(VENV)/bin/python && echo $(VENV)/bin/python || command -v python || command -v python3)
SYSTEM_PYTHON ?= python3

setup_version := `$(PYTHON) src/organilab/__init__.py`
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
## Entorno virtual
##--------------------------------------------------------

setup: ##  - crea .venv (si no existe) e instala runtime + dependencias de prueba
	@test -x $(VENV)/bin/python || $(SYSTEM_PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install -r requirements.txt
	$(VENV)/bin/python -m pip install -r test_requirements.txt
	@$(MAKE) --no-print-directory check-env

check-env: ##  - verifica dependencias, chromedriver y conexión a PostgreSQL
	@$(PYTHON) scripts/check_env.py

venv-info: ##  - muestra qué intérprete usarán los targets
	@echo "VENV   = $(VENV)"
	@echo "PYTHON = $(PYTHON)"

##--------------------------------------------------------
## Project setup & server
##--------------------------------------------------------

start: ##  - run project local
	cd src && $(PYTHON) manage.py migrate \
	&& $(PYTHON) manage.py init_checks \
	&& $(PYTHON) manage.py load_urlname_permissions

run_celery: ##  - run celery for development mode
	./run_celery.sh

database_config: ##  - init config data base
	cd src && $(PYTHON) manage.py migrate && $(PYTHON) manage.py init_checks && $(PYTHON) manage.py load_urlname_permissions

run_docker_selenium: ##  - run project in docker with selenium
	 docker run --network="host"  -v $(current_path)/src:/organilab/src  -v $(current_path)/fixtures:/organilab/fixtures -v $(current_path)/docs:/organilab/docs  -ti organilabselenium:$(setup_version) $(run)

migrate: ## - makemigrations && migrate
	cd src && $(PYTHON) manage.py makemigrations && \
	$(PYTHON) manage.py migrate

requirements: ## - install all dependencies
	$(PYTHON) -m pip install -r requirements.txt

test-requirements: ## - install all test dependencies
	$(PYTHON) -m pip install -r test_requirements.txt

create-profile: ## - create user and user profile
	cd src && $(PYTHON) manage.py createsuperuser && \
	$(PYTHON) manage.py shell -c "\
	from auth_and_perms.models import Profile; \
	from django.contrib.auth.models import User; \
	user = User.objects.last(); \
	Profile.objects.get_or_create(user=user)"

check-move-organization-data: ## Validate organization migration (Example: make check-move-organization-data FROM=5 TO=9)
	@echo "Validating organization data migration..."
	@echo "FROM=$(FROM) → TO=$(TO)"
	cd src && $(PYTHON) manage.py move_organization_data --from-org $(FROM) --to-org $(TO) --dry-run


move-organization-data: ## Execute organization migration (Example: make move-move-organization-data FROM=5 TO=9)
	@echo "You are about to move data from one organization to another"
	@echo "FROM=$(FROM) → TO=$(TO)"
	@read -p "Do you want to continue? [y/N]: " confirm; \
	if [ "$$confirm" = "y" ]; then \
		cd src && $(PYTHON) manage.py move_organization_data --from-org $(FROM) --to-org $(TO); \
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
	cd src && $(PYTHON) manage.py test  --no-input --exclude-tag=selenium

test-parallel: ## - run tests in parallel (auto-detect workers)
	cd src && $(PYTHON) manage.py test --no-input --exclude-tag=selenium --parallel -v 2

single-test: ## Run Django tests (optional: TEST=path.to.test, example: make single-test TEST=laboratory.tests.test_provider.ProviderViewTest)
	cd src && $(PYTHON) manage.py test $(TEST) --no-input --exclude-tag=selenium

test-selenium: ## Run Selenium tests, workers auto (optional: TEST=path.to.test, example: make test-selenium TEST=laboratory.tests.selenium_tests) [OJO: usa TU pantalla, abre Chrome encima de tu sesion]
	cd src && $(PYTHON) manage.py test $(or $(TEST),) --tag=selenium --no-input --parallel -v 2

test-selenium-parallel: ## Run Selenium tests with a fixed worker count (WORKERS=12 by default, optional: TEST=path.to.test) [OJO: usa TU pantalla, abre Chrome encima de tu sesion]
	cd src && $(PYTHON) manage.py test $(or $(TEST),) --tag=selenium --no-input --parallel $(or $(WORKERS),12) -v 2

test-selenium-xvfb: ## Run Selenium tests headless via xvfb-run, workers auto (optional: TEST=path.to.test)
	xvfb-run --auto-servernum --server-args="-screen 0 1280x720x24" sh -c "cd src && $(PYTHON) manage.py test $(or $(TEST),) --tag=selenium --no-input --parallel -v 2"

test-selenium-fast: ## Run Selenium tests without GIF generation, workers auto (optional: TEST=path.to.test) [OJO: usa TU pantalla, abre Chrome encima de tu sesion]
	cd src && GENERATE_SCREENSHOTS=False $(PYTHON) manage.py test $(or $(TEST),) --tag=selenium --no-input --parallel -v 2

test-selenium-single-fast: ## Run a single Selenium test without GIF generation, serial (TEST=path.to.test) [OJO: usa TU pantalla, abre Chrome encima de tu sesion]
	cd src && GENERATE_SCREENSHOTS=False $(PYTHON) manage.py test $(TEST) --tag=selenium --no-input -v 2

test-selenium-single: ## Corre UN test Selenium en serie y en su PROPIA pantalla virtual (TEST=ruta.al.test; GIF=1 para generar el GIF)
	@test -n "$(TEST)" || { echo "Falta TEST=ruta.al.test (este target corre un solo test a proposito)"; exit 2; }
	xvfb-run --auto-servernum --server-args="-screen 0 1280x720x24" \
		sh -c "cd src && $(if $(GIF),,GENERATE_SCREENSHOTS=False )$(PYTHON) manage.py test $(TEST) --tag=selenium --no-input -v 2"

test-selenium-dev: ## Run Selenium tests fast, headless, reusing the DB (optional: TEST=...). OJO --keepdb: si la BD reciclada queda sin permisos, loaddata revienta en setUpClass; borrar test_organilab y relanzar
	xvfb-run --auto-servernum --server-args="-screen 0 1280x720x24" \
		sh -c "cd src && GENERATE_SCREENSHOTS=False $(PYTHON) manage.py test $(or $(TEST),) --tag=selenium --no-input --keepdb --parallel -v 2"


##--------------------------------------------------------
## Bitácora de Selenium
##--------------------------------------------------------

BITACORA_DIR ?= $(ROOT_DIR)/selenium-results
BITACORA ?= $(BITACORA_DIR)/bitacora_$(shell date +%Y%m%d_%H%M%S).log

test-selenium-bitacora: ## Corre Selenium headless sin GIF y deja el log completo en selenium-results/ (optional: TEST=..., WORKERS=N, BITACORA=ruta.log)
	@mkdir -p $(BITACORA_DIR)
	@echo "Bitácora: $(BITACORA)"
	-@xvfb-run --auto-servernum --server-args="-screen 0 1280x720x24" \
		sh -c "cd src && GENERATE_SCREENSHOTS=False $(PYTHON) manage.py test $(or $(TEST),) --tag=selenium --no-input --parallel $(or $(WORKERS),) -v 2" \
		> $(BITACORA) 2>&1
	@echo
	@echo "----- resumen -----"
	@grep -E '^(FAIL|ERROR): |^Ran |^OK|^FAILED|^SKIP: ' $(BITACORA) || echo "sin fallos registrados"
	@echo "-------------------"
	@echo "Log completo: $(BITACORA)"

docs: clean ##  - generate Sphinx HTML documentation, including API docs
	$(PYTHON) -m pip install 'sphinx==8.2.3' sphinx-rtd-theme==3.0.2 sphinxcontrib-video==0.4.2
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	sphinx-build -b linkcheck ./docs/source ./docs/build/
	sphinx-build -b html ./docs/source ./docs/build/
	$(PYTHON) docs/fix_capacitacion_images.py

docs_full: ##  - generate full docs, Sphinx HTML documentation, including API docs
	xvfb-run --auto-servernum --server-args="-screen 0 1280x720x24" sh -c "cd src && $(PYTHON) manage.py test  --no-input --tag=selenium --parallel"
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(PYTHON) -m pip install 'sphinx==8.2.3' sphinx-rtd-theme==3.0.2 sphinxcontrib-video==0.4.2
	sphinx-build -b linkcheck ./docs/source ./docs/build/
	sphinx-build -b html ./docs/source ./docs/build/
	$(PYTHON) docs/fix_capacitacion_images.py

messages: ##  - extract messages for translations
	cd src && $(PYTHON) -m django makemessages --all --no-location --no-obsolete && $(PYTHON) -m django makemessages -d djangojs -l es  --ignore *.min.js --no-location --no-obsolete

trans: ##  - compile messages of translations
	cd src && $(PYTHON) -m django compilemessages --locale es
	cd src && $(PYTHON) -m django compilemessages --locale en

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
	$(MAKE) trans  && cd src  && $(PYTHON) manage.py load_urlname_permissions

##--------------------------------------------------------
## Inventario de rutas
##--------------------------------------------------------

# Se genera con test_settings y DEBUG=False a propósito: es el urlconf que ve el
# guardián de presentation/tests/test_url_inventory.py (Django fuerza DEBUG=False
# al correr pruebas), y `organilab/urls.py:106` monta rutas distintas según DEBUG.
# Sin fijarlo, el fichero commiteado dependería del entorno de quien lo regenere.
url-inventory: ## - regenera roadmap/INVENTARIO_URLS.md y el CSV con la clasificación de rutas
	cd src && DEBUG=False $(PYTHON) manage.py url_inventory --settings=organilab.test_settings --format md -o $(ROOT_DIR)/roadmap/INVENTARIO_URLS.md
	cd src && DEBUG=False $(PYTHON) manage.py url_inventory --settings=organilab.test_settings --format csv -o $(ROOT_DIR)/roadmap/inventario_urls.csv
	cd src && DEBUG=False $(PYTHON) manage.py url_inventory --settings=organilab.test_settings

url-inventory-check: ## - falla si el inventario commiteado quedó desactualizado
	cd src && DEBUG=False $(PYTHON) manage.py url_inventory --settings=organilab.test_settings --check $(ROOT_DIR)/roadmap/INVENTARIO_URLS.md

test-urls: ## - smoke de las vistas navegables, sin navegador
	cd src && $(PYTHON) manage.py test organilab_test.tests.test_url_smoke --no-input -v 2

##--------------------------------------------------------
## Project utils
##--------------------------------------------------------
lint: ## - check style with flake8
	pycodestyle --exclude=*/migrations/*  --max-line-length=200 src

update_sds: ## - update SDS files in batches
	cd src && $(PYTHON) manage.py update_sds --batch-size 10 --batch-delay 30 --delay 2

clean_orphan_media: ## - elimina archivos en MEDIA_ROOT no referenciados en la BD
	cd src && $(PYTHON) manage.py clean_orphan_media
