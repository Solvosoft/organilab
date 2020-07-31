# encoding: utf-8

'''
Free as freedom will be 10/10/2016

@author: luisza
'''

from laboratory.models import LaboratoryRoom, Furniture, Shelf, Object,\
    ShelfObject
import json
import re


def get_dataconfig(furniture):
    if furniture.dataconfig:
        dataconfig = json.loads(furniture.dataconfig)
    else:
        dataconfig = []
    return dataconfig


def build_dataconfig(furniture, col, row):
    dataconfig = get_dataconfig(furniture)
    if len(dataconfig) > 0:
        # Work with rows
        row2 = len(dataconfig) - 1
        col2 = len(dataconfig[0]) - 1
        if row2 < row:
            row_less = row - row2
            for x in range(row_less):
                dataconfig.append([''] * (col2 + 1))
        # Work with columns
        if col2 < col:
            col_less = col - col2
            for i, x in enumerate(dataconfig):
                dataconfig[i] = dataconfig[i] + [''] * col_less
    else:
        for x in range(row + 1):
            dataconfig.append([''] * (col + 1))
    return dataconfig


def _set_dataconfig(furniture, col, row, value):
    dataconfig = build_dataconfig(furniture, col, row)
    if dataconfig[row][col]:
        dataconfig[row][col] += ","
    dataconfig[row][col] += str(value)
    furniture.dataconfig = json.dumps(dataconfig)
    furniture.save()
    return dataconfig


def set_dataconfig(furniture, col, value):
    data = get_dataconfig(furniture)
    row = 0
    if len(data) > col:
        row = len(data[col])
    return _set_dataconfig(furniture, col, row, value)


def set_in_position(furniture, code, tipo=None):
    _type = Shelf.CRATE
    if tipo is not None:
        if 'estante simple' != tipo:
            _type = Shelf.DRAWER
    shelf, _ = Shelf.objects.get_or_create(
        name=code.upper(),
        type=_type,
        furniture=furniture
    )

    pos = int(re.findall('\d+', code)[0])

    set_dataconfig(furniture, pos, shelf.pk)

    return shelf


def get_furniture_name(code):
    return code[0].upper()


def carge_inventario_materiales():
    with open('data/inventario.csv') as arch:
        for x in arch.read().split('\n'):
            if not x:
                continue
            data = dict(zip(['nombre', 'marca', 'modelo',
                             'codigo',  'serie',
                             'num_activo', 'ubicacion', 'posicion'],
                            x.split('\t')))

            lab, _ = LaboratoryRoom.objects.get_or_create(
                name=data['ubicacion'])
            furniture, _ = Furniture.objects.get_or_create(
                labroom=lab,
                name=get_furniture_name(data['posicion']),
                type=Furniture.FURNITURE
            )

            shelf = set_in_position(furniture, data['posicion'])
            obj = Object.objects.create(
                code=data['codigo'],
                name=data['nombre'],
                type=Object.EQUIPMENT,
                description="""
        Marca: %s
        Modelo: %s
        Serie: %s
        Núm activo: %s
        """ % (
                    data['marca'],
                    data['modelo'],
                    data['serie'],
                    data['num_activo']
                )

            )

            ShelfObject.objects.create(
                shelf=shelf,
                object=obj,
                quantity=1,
                measurement_unit=ShelfObject.U
            )


def carge_cristaleria():
    with open('data/cristaleria.csv') as arch:
        for x in arch.read().split('\n'):
            if not x:
                continue
            data = dict(zip(['codigo', 'nombre',
                             'tipo', 'descripcion',
                             'caracteristica', 'ubicacion', 'posicion'],
                            x.split('\t')))

            lab, _ = LaboratoryRoom.objects.get_or_create(
                name=data['ubicacion'])
            furniture, _ = Furniture.objects.get_or_create(
                labroom=lab,
                name=get_furniture_name(data['posicion']),
                type=Furniture.FURNITURE
            )

            shelf = set_in_position(furniture, data['posicion'],
                                    data['tipo'])
            obj = Object.objects.create(
                code=data['codigo'],
                name=data['nombre'],
                type=Object.EQUIPMENT,
                description="""
            Descripción: %s
            Características: %s
            """ % (
                    data['descripcion'],
                    data['caracteristica'],
                )

            )

            ShelfObject.objects.create(
                shelf=shelf,
                object=obj,
                quantity=1,
                measurement_unit=ShelfObject.U
            )
