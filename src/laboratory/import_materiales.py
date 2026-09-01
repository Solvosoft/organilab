# encoding: utf-8

"""
Free as freedom will be 10/10/2016

@author: luisza
"""


from laboratory.models import LaboratoryRoom, Furniture, Shelf, Object, ShelfObject
import re

from laboratory import dataconfig


def get_dataconfig(furniture):
    """Matriz del mueble.  Delega en el módulo canónico."""
    return furniture.get_grid()


def set_dataconfig(furniture, col, value):
    """Coloca el estante en la columna ``col``, en la primera fila libre.

    Antes este módulo escribía celdas CSV (``"1,2"``), un tercer formato
    incompatible con los otros dos; ahora la posición la escribe el servicio,
    que serializa siempre listas de enteros.
    """
    grid = furniture.get_grid()
    row = 0
    for irow, cells in enumerate(grid):
        if col >= len(cells) or not cells[col]:
            row = irow
            break
    else:
        row = len(grid)
    dataconfig.DataconfigService(furniture).place_shelf(value, row, col)
    return furniture.get_grid()


def set_in_position(furniture, code, tipo=None):
    _type = Shelf.CRATE
    if tipo is not None:
        if "estante simple" != tipo:
            _type = Shelf.DRAWER
    shelf, _ = Shelf.objects.get_or_create(
        name=code.upper(), type=_type, furniture=furniture
    )

    pos = int(re.findall(r"\d+", code)[0])

    set_dataconfig(furniture, pos, shelf.pk)

    return shelf


def get_furniture_name(code):
    return code[0].upper()


def carge_inventario_materiales():
    with open("data/inventario.csv") as arch:
        for x in arch.read().split("\n"):
            if not x:
                continue
            data = dict(
                zip(
                    [
                        "nombre",
                        "marca",
                        "modelo",
                        "codigo",
                        "serie",
                        "num_activo",
                        "ubicacion",
                        "posicion",
                    ],
                    x.split("\t"),
                )
            )

            lab, _ = LaboratoryRoom.objects.get_or_create(name=data["ubicacion"])
            furniture, _ = Furniture.objects.get_or_create(
                labroom=lab,
                name=get_furniture_name(data["posicion"]),
                type=Furniture.FURNITURE,
            )

            shelf = set_in_position(furniture, data["posicion"])
            obj = Object.objects.create(
                code=data["codigo"],
                name=data["nombre"],
                type=Object.EQUIPMENT,
                description="""
        Marca: %s
        Modelo: %s
        Serie: %s
        Núm activo: %s
        """
                % (data["marca"], data["modelo"], data["serie"], data["num_activo"]),
            )

            ShelfObject.objects.create(
                shelf=shelf, object=obj, quantity=1, measurement_unit=ShelfObject.U
            )


def carge_cristaleria():
    with open("data/cristaleria.csv") as arch:
        for x in arch.read().split("\n"):
            if not x:
                continue
            data = dict(
                zip(
                    [
                        "codigo",
                        "nombre",
                        "tipo",
                        "descripcion",
                        "caracteristica",
                        "ubicacion",
                        "posicion",
                    ],
                    x.split("\t"),
                )
            )

            lab, _ = LaboratoryRoom.objects.get_or_create(name=data["ubicacion"])
            furniture, _ = Furniture.objects.get_or_create(
                labroom=lab,
                name=get_furniture_name(data["posicion"]),
                type=Furniture.FURNITURE,
            )

            shelf = set_in_position(furniture, data["posicion"], data["tipo"])
            obj = Object.objects.create(
                code=data["codigo"],
                name=data["nombre"],
                type=Object.EQUIPMENT,
                description="""
            Descripción: %s
            Características: %s
            """
                % (
                    data["descripcion"],
                    data["caracteristica"],
                ),
            )

            ShelfObject.objects.create(
                shelf=shelf, object=obj, quantity=1, measurement_unit=ShelfObject.U
            )
