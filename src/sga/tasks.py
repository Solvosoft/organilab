import importlib
import logging

from celery.utils.log import get_task_logger
from django.conf import settings

from sga.models import SDSTraceability, SubstanceCharacteristics

app = importlib.import_module(settings.CELERY_MODULE).app
task_logger = get_task_logger(__name__)
logger = logging.getLogger("organilab")


@app.task()
def extract_sds_for_characteristics(sc_pk, user_pk=None, source="manual"):
    """Extrae los datos de la ficha subida y deja constancia de su origen.

    Se encola desde el paso 1 del asistente en cuanto el usuario sube el PDF. La
    extracción es heurística sobre el texto del documento, así que el resultado
    es una propuesta que el usuario revisa: si falla, la ficha queda guardada
    igualmente y se rellena a mano. Subir la ficha nunca debe fallar porque la
    extracción falle.
    """
    from laboratory.tasks import _update_substance_from_pdf

    characteristics = SubstanceCharacteristics.objects.filter(pk=sc_pk).first()
    if characteristics is None:
        return {"ok": False, "message": "characteristics not found", "fields": []}

    if not characteristics.security_sheet:
        return {"ok": False, "message": "no security sheet uploaded", "fields": []}

    try:
        # overwrite=False: lo extraído es una propuesta, así que solo rellena los
        # campos vacíos y nunca pisa lo que la persona ya haya escrito.
        success, message, data = _update_substance_from_pdf(
            characteristics, overwrite=False
        )
    except Exception as error:  # la subida ya está hecha: no propagar el fallo
        task_logger.exception("SDS extraction failed for sc=%s", sc_pk)
        return {"ok": False, "message": str(error), "fields": []}

    # La traza se crea aunque la extracción no dé nada: el valor de la
    # trazabilidad es registrar que esta ficha entró y de dónde vino.
    SDSTraceability.objects.create(
        sga_substance_characteristics=characteristics,
        source=source,
        revision_date=data.get("revision_date"),
        created_by_id=user_pk,
    )

    fields = sorted(
        key
        for key, value in data.items()
        if not key.startswith("_") and value not in (None, "", [])
    )
    return {"ok": bool(success), "message": message, "fields": fields}
