Installation
**************

Clone this repository

.. code-block:: bash

	$ git clone git@github.com:solvo/organilab.git
	$ cd organilab

Create a virtualenv

.. code-block:: bash

	$ mkdir -p ~/entornos/
	$ virtualenv -p python3 ~/entornos/organilab
	$ source ~/entornos/organilab/bin/activate

Install requirements

.. code-block:: bash

	$ pip install -r requirements.txt

Run in development
======================

Check your database configuration and sync your models

.. code-block:: bash

	$ python manage.py migrate

Create a superuser for admin views

.. code-block:: bash

	$ python manage.py createsuperuser

Run your development server

.. code-block:: bash

	$ python manage.py runserver

**happy hacking**

