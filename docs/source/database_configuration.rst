Database configuration
######################

In order to configure the database connection of the Django project, you must create the database resource and a user with permissions granted to manage such resource.

Dependencies
============

* Install PostgreSQL: With a ``sudo`` session (or with any superuser privileges session) you must install the required packages to run the PostgreSQL DBMS.

.. code-block:: bash

    $ sudo apt-get install postgresql-9.4 postgresql-client-9.4

* Configure the database to use hashed passwords instead of trusted authentication:  Edit the file ``/etc/postgresql/9.4/main/pg_hba.conf`` and change the entrie with this content:

.. code-block:: bash

    # "local" is for Unix domain socket connections only
    local   all             all                                     peer

Change it for this:

.. code-block:: bash

    # "local" is for Unix domain socket connections only
    local   all             all                                     peer

Create the database
===================

To create the database you must log in to the user postgres, elevating privileges with ``sudo``:

.. code-block:: bash

    $ sudo su - postgres

Create the database using the command ``createdb`` :

.. code-block:: bash

    $ createdb organilab --encoding=utf8

Create the user
===============

To create the database user, using the ``postgres`` session, execute the next command:

.. code-block:: bash

    $ createuser organilab_user

Also you must set a password for the user. To do so, run the next commands:

.. code-block:: bash

    $ psql
    psql (9.4.8)
    Digite «help» para obtener ayuda.

    postgres=# \password organilab_user
    Ingrese la nueva contraseña: <SECURE_PASSWORD>
    Ingrésela nuevamente: <SECURE_PASSWORD>

Grant privileges to the user
============================

To grant privileges to the user on the ``organilab`` database, run the next commands:

.. code-block:: bash

    $ psql
    psql (9.4.8)
    Digite «help» para obtener ayuda.

    postgres=# GRANT ALL PRIVILEGES ON DATABASE organilab TO organilab_user;

Create the database structure
#############################

To create the schemas and the structure of the database, go to the ``organilab`` project root directory and run the next command:

.. code-block:: bash

    $ python manage.py migrate

Now the database structure is defined, the only step left is to populate it.

Populate the database
#####################

To populate the ``organilab`` database, go to the ``organilab`` project root directory and run the next command:

.. code-block:: bash

    $ python manage.py shell
    Python 3.4.2 (default, Oct  8 2014, 10:45:20)
    [GCC 4.9.1] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    (InteractiveConsole)
    >>>  from laboratory.create_data import create_data
    >>>  create_data()