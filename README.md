# organilab

[![Tests](https://github.com/Solvosoft/organilab/actions/workflows/tests.yml/badge.svg)](https://github.com/Solvosoft/organilab/actions/workflows/tests.yml)
[![Documentation](https://img.shields.io/readthedocs/organilab?label=Read%20the%20Docs&logo=read%20the%20docs&logoColor=white)](http://organilab.readthedocs.io/en/latest/?badge=latest)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django)
![Coverage](https://solvosoft.github.io/organilab/coverage.svg)

Simple laboratory organizer with multiples features:

- Laboratory builder and elegant presentation
- Multi-laboratory management
- Reservation system
- Solution Calculator
- Procedures management
- Object limit notifications
- Internationalization

# Documentation

Documentation will be available in [read the docs](http://organilab.readthedocs.io/)

# Installation

Clone this repository

	$ git clone git@github.com:solvo/organilab.git
	$ cd organilab

Create a virtualenv

	$ mkdir -p ~/entornos/
	$ python -m venv ~/entornos/organilab
	$ source ~/entornos/organilab/bin/activate

Install requirements

	$ pip install -r requirements.txt

# Run in development

Check your database configuration and sync your models

	$ python manage.py migrate
	$ python manage.py createcachetable
    $ python manage.py load_urlname_permissions
    $ python manage.py loadgroup
    $ python manage.py load_sga
    $ python manage.py loaddata sga_components.json

Could be required to call python manage.py initial_data

Create a superuser for admin views

	$ python manage.py createsuperuser

Run your development server

	$ python manage.py runserver

Create translations

	$ django-admin makemessages --all --no-location --no-obsolete

Create javascript translations

    $ django-admin makemessages -d djangojs -l es  --ignore *.min.js

Compile translations

	$ django-admin compilemessages --locale es

## Run with composer in development environment

Create your image organilab
```bash
docker build -f docker/Dockerfile -t solvosoft/organilab
```

Run with **bind mount folder** to sync with changes without rebuild image:
```bash
docker run -it --name organilab -p 80:80 -p 8000:8000 \
    -v `pwd`/src/:/organilab --env DBHOST=YOUR_PG_HOST \
	solvosoft/organilab
```

Enter to the container:
```bash
docker run -it organilab python manage.py runserver 0.0.0.0:8000
```
And finally each change you make in your local files will restart the environment in order to apply them.

## Testing with selenium and docker

Run all selenium test is too slow, so you maybe want to generate a gif of your test.

First create a docker image:

```bash
make build_docker_selenium
```

Run your test, please note that quotes ("") are required on the command before run=.

```
make run_docker_selenium run="python manage.py test  --no-input --tag=selenium laboratory.tests.selenium_tests.manage_organizations.test_laboratory_tab"
```


## happy hacking


