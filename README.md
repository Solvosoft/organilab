# organilab
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
	$ virtualenv -p python3 ~/entornos/organilab
	$ source ~/entornos/organilab/bin/activate
    
Install requirements 
    
    $ cat apt_requirements.txt | xargs sudo apt install -y
	$ pip install -r requirements.txt
	
	
# Run in development

Check your database configuration and sync your models

	$ python manage.py migrate

Create a superuser for admin views

	$ python manage.py createsuperuser

Run your development server

	$ python manage.py runserver

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

## happy hacking	

	
