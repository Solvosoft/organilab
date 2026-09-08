# encoding: utf-8
"""Defaults de modelo que dependen de settings, expuestos como callables.

``default=settings.LANGUAGE_CODE`` congela el valor del entorno donde se corrió
``makemigrations``: la suite usa ``test_settings`` (``LANGUAGE_CODE = "en"``) y
producción usa ``settings`` (``"es"``), así que el autodetector veía un
``AlterField`` pendiente en un entorno u otro para siempre.  Con un callable el
estado de migraciones guarda la referencia a la función, no su valor, y deja de
depender de qué settings estaban activos.
"""

from django.conf import settings


def get_default_language():
    return settings.LANGUAGE_CODE


def get_language_choices():
    return settings.LANGUAGES
