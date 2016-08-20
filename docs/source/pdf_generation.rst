PDF Generation with Weasyprint
##############################

Follow this steps for generation PDF files with weasyprint.

Dependencies
============

* Install packages: With a ``sudo`` session (or with any superuser privileges session) you must install your platform’s packages (Linux, Debian/Ubuntu).

.. code-block:: bash

	$ sudo apt-get install python-dev python-pip python-lxml python-cffi libcairo2 libpango1.0-0 libgdk-pixbuf2.0-0 shared-mime-info

* You need to upgrade the next files. In organilab virtualenv:

.. code-block:: bash

	source ~/entornos/organilab/bin/activate

.. code-block:: bash

	pip install --upgrade setuptools pip

* Finally, you going to install Weasyprint.

.. code-block:: bash
	
	pip install WeasyPrint

Code
====