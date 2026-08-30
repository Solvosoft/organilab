# encoding: utf-8

"""
Free as freedom will be 13/10/2016

@author: luisza
"""

from laboratory import dataconfig
from laboratory.models import Shelf


def preserve_order(order, queryset):
    """Ordena el queryset según la lista de pks ``order``.

    Se conserva por compatibilidad con los llamadores existentes; la resolución
    real vive en :func:`laboratory.dataconfig.resolve_shelves`.
    """
    shelves = {shelf.pk: shelf for shelf in queryset}
    result = []
    for pk in order:
        try:
            pk = int(pk)
        except (TypeError, ValueError):
            continue
        if pk in shelves:
            result.append(shelves[pk])
    return result


def get_dataconfig(dataconfig_text):
    """``dataconfig`` -> matriz de instancias ``Shelf``, en una sola consulta.

    Delega en el módulo canónico: aquí ya no se parsea nada.
    """
    return dataconfig.resolve_shelves(dataconfig.parse(dataconfig_text))
