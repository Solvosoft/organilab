"""Códigos de sustancia y de lote.

El código se parte en dos porque cada mitad responde a una pregunta distinta y
se conoce en un momento distinto:

    EQ-{laboratorio}-{organizacion}-{sustancia}      p. ej. EQ-QMG-CIE-000031
    ...-{año}-{mes}-{consecutivo}                    p. ej. ...-2026-08-0001

La primera mitad dice *qué* sustancia es y *dónde* se aprobó, y se conoce al
aprobarla; por eso no lleva consecutivo y es idempotente. La segunda identifica
*qué envase concreto* se está etiquetando, y solo tiene sentido cuando ese
envase existe.

Las siglas de laboratorio y organización se derivan del nombre: si el nombre ya
declara una entre paréntesis se respeta —quien la escribió ahí la eligió a
propósito— y en caso contrario se componen las iniciales de las palabras que
distinguen a esa unidad de las demás.
"""

import re
import unicodedata

PREFIX = "EQ"
CODE_LENGTH = 3

#: Palabras que no distinguen a una unidad de otra. La sigla debe identificar,
#: y los nombres suelen compartir el genérico («Laboratorio de …»): usarlo daría
#: la misma sigla a unidades que no tienen nada que ver entre sí.
STOPWORDS = {
    "laboratorio",
    "laboratory",
    "lab",
    "de",
    "del",
    "la",
    "las",
    "el",
    "los",
    "y",
    "e",
    "en",
    "para",
}

#: Caracteres con los que se resuelve un choque de siglas, en este orden.
SUFFIXES = "23456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

_PARENTHESISED = re.compile(r"\(([^)]+)\)")


def _strip_accents(text):
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def _significant_words(name):
    limpio = _strip_accents(name or "")
    palabras = re.findall(r"[A-Za-z0-9]+", limpio)
    significativas = [p for p in palabras if p.lower() not in STOPWORDS]
    return significativas or palabras


def suggest_code(name, taken=()):
    """Sigla de tres caracteres para un laboratorio o una organización.

    `taken` son las siglas ya usadas; si la propuesta choca se sustituye el
    último carácter hasta encontrar una libre. Devuelve None si del nombre no
    sale nada aprovechable.
    """
    tomadas = {c.upper() for c in taken if c}

    # 1. La sigla que el propio nombre ya declara entre paréntesis.
    match = _PARENTHESISED.search(name or "")
    candidata = ""
    if match:
        interior = re.sub(r"[^A-Za-z0-9]", "", _strip_accents(match.group(1)))
        if interior:
            candidata = interior[:CODE_LENGTH].upper()

    if not candidata:
        palabras = _significant_words(name)
        if not palabras:
            return None
        if len(palabras) == 1:
            # «Química» -> QUI
            candidata = palabras[0][:CODE_LENGTH].upper()
        else:
            # «Química General» -> QUG: dos letras de la primera, una de la segunda.
            candidata = (palabras[0][:2] + palabras[1][:1]).upper()

    candidata = candidata.ljust(CODE_LENGTH, "X")[:CODE_LENGTH]

    if candidata not in tomadas:
        return candidata

    base = candidata[: CODE_LENGTH - 1]
    for sufijo in SUFFIXES:
        alternativa = base + sufijo
        if alternativa not in tomadas:
            return alternativa
    return None


def build_substance_code(laboratory, organization, substance):
    """Parte estable del código: identifica la sustancia en ese laboratorio.

    Es idempotente a propósito —no consume numeración—, así que reaprobar una
    sustancia devuelve exactamente el mismo código. Devuelve None si falta
    alguna sigla: sin ellas el código no se puede formar, y quedarse sin código
    es preferible a inventarse uno.
    """
    if not laboratory or not organization or not substance:
        return None
    if not laboratory.code or not organization.code:
        return None
    return f"{PREFIX}-{laboratory.code}-{organization.code}-{substance.pk:06d}"


def build_lot_code(substance_code, year, month, counter):
    """Código completo que se imprime en la etiqueta del envase físico."""
    return f"{substance_code}-{year}-{month:02d}-{counter:04d}"


#: Reconoce un código completo para poder leer su consecutivo.
LOT_CODE_RE = re.compile(
    rf"^{PREFIX}-[A-Z0-9]{{{CODE_LENGTH}}}-[A-Z0-9]{{{CODE_LENGTH}}}-"
    r"(?P<substance>\d+)-(?P<year>\d{4})-(?P<month>\d{2})-(?P<counter>\d+)$"
)


def parse_lot_code(code):
    """Descompone un código completo, o None si no sigue la fórmula."""
    if not code:
        return None
    match = LOT_CODE_RE.match(code.strip().upper())
    if not match:
        return None
    return {
        "substance": int(match.group("substance")),
        "year": int(match.group("year")),
        "month": int(match.group("month")),
        "counter": int(match.group("counter")),
    }
