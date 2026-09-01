"""Lote del envase físico: la segunda mitad del código de la etiqueta.

La primera mitad la emite la aprobación de la sustancia y vive en
`sga.SubstanceLaboratory`. Aquí se le añade `-AAAA-MM-NNNN`.

El consecutivo cuenta los envases de esa sustancia en ese laboratorio dentro del
mes: así el número que se lee en una etiqueta dice cuántos envases de ese
reactivo se prepararon ahí ese mes, que es la pregunta que responde un lote.
Reiniciar cada mes mantiene el número corto y lo ata al periodo.
"""

import logging

from django.db import transaction
from django.utils import timezone

from sga.substance_codes import build_lot_code

logger = logging.getLogger("organilab")


def get_substance_laboratory(shelfobject):
    """La pareja sustancia-laboratorio a la que pertenece este envase.

    Se llega por el objeto de inventario: `object` → características SGA →
    sustancia → su fila para el laboratorio donde está el envase. Devuelve None
    en cuanto falte un eslabón: un envase puede no venir de una sustancia del
    catálogo SGA, o estar en un laboratorio que no la solicitó, y en ninguno de
    los dos casos existe un código al que pertenecer.
    """
    from sga.models import SubstanceLaboratory

    if not shelfobject.object_id or not shelfobject.in_where_laboratory_id:
        return None

    characteristics = shelfobject.object.substancharacteristics_object.first()
    if characteristics is None or characteristics.substance_id is None:
        return None

    return (
        SubstanceLaboratory.objects.filter(
            substance_id=characteristics.substance_id,
            laboratory_id=shelfobject.in_where_laboratory_id,
        )
        .exclude(code=None)
        .exclude(code="")
        .first()
    )


def next_counter(substance_laboratory, year, month):
    """Siguiente consecutivo del mes, reservándolo contra carreras."""
    from laboratory.models import ShelfObjectCodeCounter

    with transaction.atomic():
        contador, _creado = ShelfObjectCodeCounter.objects.select_for_update(
        ).get_or_create(
            substance_laboratory=substance_laboratory, year=year, month=month
        )
        contador.counter += 1
        contador.save(update_fields=["counter"])
        return contador.counter


def assign_lot_code(shelfobject):
    """Escribe el código completo en el envase, si se puede componer.

    Un envase sin sustancia SGA detrás —o de un laboratorio que no solicitó esa
    sustancia— se queda sin código: es preferible a inventarse uno.
    """
    enlace = get_substance_laboratory(shelfobject)
    if enlace is None:
        return None

    ahora = timezone.localtime()
    try:
        consecutivo = next_counter(enlace, ahora.year, ahora.month)
    except Exception:  # noqa: BLE001
        logger.exception(
            "No se pudo reservar el consecutivo de lote para el shelfobject %s",
            shelfobject.pk,
        )
        return None

    codigo = build_lot_code(enlace.code, ahora.year, ahora.month, consecutivo)
    shelfobject.shelfobject_code = codigo
    shelfobject.save(update_fields=["shelfobject_code"])
    return codigo
