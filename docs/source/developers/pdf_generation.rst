PDF Generation with Weasyprint
***********************************

Follow this steps for generation PDF files with weasyprint.

Dependencies
===============

* Update the file: ``requirements.txt``.

.. code-block:: bash

	$ pip install -r requirements.txt

* Install packages: With a ``sudo`` session (or with any superuser privileges session) you must install your platform’s packages (Linux, Debian/Ubuntu).

.. code-block:: bash

	$ sudo apt-get install python-dev python-pip python-lxml python-cffi libcairo2 libpango1.0-0 libgdk-pixbuf2.0-0 shared-mime-info

* Install the next package: With a ``sudo`` session.

.. code-block:: bash

	$ sudo apt-get install libxml2-dev libxslt1-dev libffi-dev


* You need to upgrade the next files. In organilab virtualenv:

.. code-block:: bash

	source ~/entornos/organilab/bin/activate

.. code-block:: bash

	pip install --upgrade setuptools pip

* Finally, you going to install Weasyprint.

.. code-block:: bash

	pip install WeasyPrint

Code
=========

* You need to define a HTML view ("example_pdf.html"). In this HTML view, you can define the top, the body and the bottom of the PDF file.

.. code-block:: bash

    <html>
        <head>
            <style>
                @page {
                    margin: 3cm 2cm; padding-left: 1.5cm;

                    @top-left {
                        content: "Example Report";
                    }
                    @top-right {
                        content: "Date: {{ datetime }}";
                    }
                    @bottom-right {
                        content: "Page " counter(page) " of " counter(pages) ;
                    }
                    @bottom-left {
                        content:  "User: {{ request.user }}";
                        color: red;
                    }
                }
                body {
                    text-align: justify
                }
            </style>
        </head>
        <body>
            <h3>
                Hello, this is my report!!
            </h3>
        </body>
    </html>

* Define de PDF generator method.

.. code-block:: python

    def report_example(request):
        varModel = Model.objects.all()

        template = get_template('pdf/example_pdf.html')

        context = {
                   'object_list': varModel,
                   'datetime': timezone.now(),
                   'request': request
                   }

        html = template.render(Context(context)).encode("UTF-8")

        page = HTML(string=html, encoding='utf-8').write_pdf()

        response = HttpResponse(page, content_type='application/pdf')

        response[
                  'Content-Disposition'] = 'attachment; filename="report_example.pdf"'
        return response

* Create the URL.

.. code-block:: python

    url(r"^report/example$", views.report_example, name="report_example"),
