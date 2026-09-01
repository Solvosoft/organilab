# -*- coding: utf-8 -*-
"""Resolvedor de frases H/P contra la base de datos para el motor de etiquetas.

El catálogo que trae ``sga.label_engine`` sólo cubre las frases y combinaciones
más frecuentes. La fuente de verdad son ``DangerIndication`` y
``PrudenceAdvice``, que además incluyen las combinaciones oficiales completas
(registradas con el ``+`` separado por espacios: ``"P370 + P378"``).

El motor no conoce el ORM: la app le inyecta este resolvedor en
``SgaConfig.ready()`` y él lo consulta antes de su catálogo local.

La caché es un diccionario en memoria del proceso, no el framework de caché:
la caché por defecto del proyecto es ``DatabaseCache`` y una consulta suya
fallida (tabla ausente) abortaría la transacción en curso de quien esté
generando la etiqueta. El catálogo GHS es pequeño y cambia rara vez, así que
basta con rehacerlo al arrancar cada proceso.
"""
import threading

from sga.label_engine.phrases_catalog import normalize_code

_lock = threading.Lock()
_phrase_map = None


def build_phrase_map() -> dict[str, str]:
    """Mapa ``código normalizado -> texto`` desde la base de datos."""
    from sga.models import DangerIndication, PrudenceAdvice

    mapping: dict[str, str] = {}
    for code, text in DangerIndication.objects.values_list("code", "description"):
        key = normalize_code(code)
        if key and text:
            mapping[key] = text.strip()
    for code, text in PrudenceAdvice.objects.values_list("code", "name"):
        key = normalize_code(code)
        if key and text:
            mapping[key] = text.strip()
    return mapping


def get_phrase_map() -> dict[str, str]:
    """Mapa de frases, construido una vez por proceso."""
    global _phrase_map
    if _phrase_map is None:
        with _lock:
            if _phrase_map is None:
                _phrase_map = build_phrase_map()
    return _phrase_map


def invalidate() -> None:
    """Descarta el mapa en memoria (tras editar el catálogo GHS)."""
    global _phrase_map
    with _lock:
        _phrase_map = None


def resolve(code: str) -> str | None:
    """Texto de un código H/P (suelto o combinado), o None si no está en la BD.

    Nunca propaga errores: si la base no está disponible el motor cae a su
    catálogo local en vez de dejar la etiqueta sin generar.
    """
    try:
        return get_phrase_map().get(normalize_code(code))
    except Exception:  # noqa: BLE001 - la etiqueta no debe caer por el catálogo
        return None
