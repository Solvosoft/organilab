# encoding: utf-8

'''
Free as freedom will be 13/10/2016

@author: luisza
'''

import json
from laboratory.models import Shelf


def get_dataconfig(dataconfig):
    if dataconfig:
        dataconfig = json.loads(dataconfig)

    for irow, row in enumerate(dataconfig):
        for icol, col in enumerate(row):
            if col:
                val = None
                if type(col) == str:
                    val = col.split(",")
                elif type(col) == int:
                    val = [col]
                elif type(col) == list:
                    val = col
                else:
                    continue
                dataconfig[irow][icol] = Shelf.objects.filter(
                    pk__in=val)
    return dataconfig



