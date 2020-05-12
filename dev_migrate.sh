#!/bin/bash

cd src/
python manage.py migrate
python manage.py loaddata catalog
python manage.py loaddata zonetype
python manage.py createsuperuser

