# encoding: utf-8

"""
Free as freedom will be 13/10/2016

@author: luisza
"""

import json
from laboratory.models import Shelf


def preserve_order(order, queryset):
    for item in queryset:
        index = order.index(item.pk)
        if index >= 0:
            order[index] = item
    return [shelf for shelf in order if isinstance(shelf, Shelf)]


def get_dataconfig(dataconfig):
    if dataconfig:
        dataconfig = json.loads(dataconfig)

    for irow, row in enumerate(dataconfig):
        for icol, col in enumerate(row):
            if col:
                val = None
                if isinstance(col, str):
                    val = col.split(",")
                elif isinstance(col, int):
                    val = [col]
                elif isinstance(col, list):
                    val = col
                else:
                    continue
                dataconfig[irow][icol] = preserve_order(
                    val, Shelf.objects.filter(pk__in=val)
                )
    return dataconfig
