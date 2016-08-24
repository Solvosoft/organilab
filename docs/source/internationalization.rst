Internationalization
####################

The goal of internationalization and localization is to allow a single Web application to offer its content in languages and formats tailored to the audience.

Django has full support for translation of text, formatting of dates, times and numbers, and time zones.

Essentially, Django does two things:

* It allows developers and template authors to specify which parts of their apps should be translated or formatted for local languages and cultures.
* It uses these hooks to localize Web apps for particular users according to their preferences.

To specify which parts (specially string and unicode instances) must be translated to the local language where the web app is being deployed, Django offers the functions located in ``django.utils.translation``.

Standard translation
====================

To specify an standard translation, use the ``ugettext_lazy`` function:

* In a view:

.. code-block:: python

    from django.utils.translation import ugettext_lazy as _
    from django.http import HttpResponse

    def some_view(request):
        output = _('Hello World')
        return HttpResponse(output)

* In a model:

.. code-block:: python

    from django.db import models
    from django.utils.translation import ugettext_lazy as _

    class Object(models.Model):
        REACTIVE = '0'
        MATERIAL = '1'
        EQUIPMENT = '2'
        TYPE_CHOICES = (
            (REACTIVE, _('Reactive')),
            (MATERIAL, _('Material')),
            (EQUIPMENT, _('Equipment'))
        )
        shelf = models.ForeignKey('Shelf')
        type = models.CharField(_('Type'), max_length=2, choices=TYPE_CHOICES)
        code = models.CharField(_('Code'), max_length=255)
        description = models.TextField(_('Description'))
        name = models.CharField(_('Name'), max_length=255)
        feature = models.ManyToManyField('ObjectFeatures')

* In a template:

.. code-block:: bash

	{% load i18n %} 
	<html>
		<head>
			<title> {% trans "This is the title." %} </title>
		</head>
		<body>
			<h1> {% trans "Hello World!!" %} </h1>
		</body>
	</html>

* In a template with CSS:

.. code-block:: bash

	<html>
		<head>
			<title> {% trans "This is the title." %} </title>
			<style>
				@page {
					margin: 3cm 2cm; padding-left: 1.5cm;
					@top-left {
						content: "{% trans "Organilab Report" %}";
					}
					@top-right {
						content: "{% trans "Date:" %} {{ datetime }}";
					}
					@bottom-right {
						content: "{% trans "Page" %} " counter(page)
						" {% trans "of" %} " counter(pages) ;
					}
					@bottom-left {
						content:  "{% trans "User:" %} {{ request.user }}";
						color: red;
					}
				}
				body {
					text-align: justify
				}
			</style>
		</head>
		<body>
			<h1> {% trans "Hello World!!" %} </h1>
		</body>
	</html>
	

