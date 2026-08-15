# -*- coding: utf-8 -*-
"""Resolvedor de frases H/P contra la base de datos para el motor de etiquetas.

El catálogo que trae ``sga.label_engine`` sólo cubre las frases y combinaciones
más frecuentes. La fuente de verdad son ``DangerIndication`` y
``PrudenceAdvice``, que además incluyen las combinaciones oficiales completas
(registradas con el ``+`` separado por espacios: ``"P370 + P378"``).

El motor no conoce el ORM: la app le inyecta este resolvedor en
``SgaConfig.ready()`` y él lo consulta antes de su catálogo local.
"""
from django.core.cache import cache

from sga.label_engine.phrases_catalog import normalize_code

CACHE_KEY = "sga_label_phrases_map"
CACHE_TIMEOUT = 60 * 60  # 1 h: el catálogo GHS cambia muy rara vez.


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
    """Mapa cacheado de frases. Se reconstruye al expirar la caché."""
    mapping = cache.get(CACHE_KEY)
    if mapping is None:
        mapping = build_phrase_map()
        cache.set(CACHE_KEY, mapping, CACHE_TIMEOUT)
    return mapping


def invalidate() -> None:
    """Descarta el mapa cacheado (tras editar el catálogo GHS)."""
    cache.delete(CACHE_KEY)


def resolve(code: str) -> str | None:
    """Texto de un código H/P (suelto o combinado), o None si no está en la BD.

    Nunca propaga errores: si la base no está disponible el motor cae a su
    catálogo local en vez de dejar la etiqueta sin generar.
    """
    try:
        return get_phrase_map().get(normalize_code(code))
    except Exception:  # noqa: BLE001 - la etiqueta no debe caer por el catálogo
        return None
