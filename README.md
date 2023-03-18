# organilab

[![Tests](https://github.com/Solvosoft/organilab/actions/workflows/tests.yml/badge.svg)](https://github.com/Solvosoft/organilab/actions/workflows/tests.yml)
[![Documentation](https://img.shields.io/readthedocs/organilab?label=Read%20the%20Docs&logo=read%20the%20docs&logoColor=white)](http://organilab.readthedocs.io/en/latest/?badge=latest)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django)

Simple laboratory organizer with multiples features:

- Laboratory builder and elegant presentation 
- Multi-laboratory management
- Reservation system
- Solution Calculator
- Procedures management
- Object limit notifications
- Internationalization

# Documentation

Documentation will be available in [read the docs](http://organilab.readthedocs.io/en/latest/)

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

Compile translations 

	$ django-admin makemessages --all
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


## Cómo compilar el editor.

1) Create in `assert` folder 2 links 
   - assets/svgcanvas   <- svgeditor/packages/svgcanvas
   - assets/svgedit  <- svgedit
2) Install dependencies usin `npm i`
3) Install svgcanvas dependencies using `npm i` in folder `assets/svgcanvas`
4) Build de project 
   - npm run svgcanvas
   - npm run editor
   - npm run build

Listo, la biblioteca ya está correctamente compilada y en las carpetas que debería


## happy hacking	


