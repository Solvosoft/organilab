# -*- coding: utf-8 -*-
"""Corrige la ortografía de las indicaciones de peligro del catálogo GHS.

Continuación de sga.0096, que completó las frases truncadas. Aquí se arregla
sólo la forma, nunca el contenido: los textos salen impresos en la etiqueta y
llegaban sin tildes ("Liquido y vapores muy inflamables"), sin punto final o
con erratas ("peligro de expasión en masa").

Se comparó cada frase con el catálogo de referencia del motor
(``sga.label_engine.phrases_catalog``) y se clasificaron las diferencias por
sus palabras, ignorando tildes, mayúsculas y puntuación:

- COSMETIC: mismas palabras exactas; cambian tildes, puntuación o espacios.
- SPELLING: una sola palabra difiere en una o dos letras — errata ("expasión")
  o concordancia con la redacción oficial CLP/SGA ("Muy tóxicos" → "Muy
  tóxico"). No alteran el significado de la frase.

Deliberadamente NO se tocan las 90 frases cuya redacción difiere de verdad: en
varias la base dice más que el catálogo (H261 detalla que los gases "pueden
inflamarse espontáneamente", el catálogo no), así que elegir entre una y otra
es criterio del área química, no de una migración.
"""
import re
import unicodedata

from django.db import migrations

# Mismas palabras: sólo tildes, puntuación o espacios.
COSMETIC = {
    "H200": "Explosivo inestable.",
    "H202": "Explosivo; grave peligro de proyección.",
    "H203": "Explosivo; peligro de incendio, de onda expansiva o de proyección.",
    "H204": "Peligro de incendio o de proyección.",
    "H220": "Gas extremadamente inflamable.",
    "H221": "Gas inflamable.",
    "H222": "Aerosol extremadamente inflamable.",
    "H223": "Aerosol inflamable.",
    "H224": "Líquido y vapores extremadamente inflamables.",
    "H225": "Líquido y vapores muy inflamables.",
    "H228": "Sólido inflamable.",
    "H260": "En contacto con el agua desprende gases inflamables que pueden inflamarse espontáneamente.",
    "H271": "Puede provocar un incendio o una explosión; muy comburente.",
    "H272": "Puede agravar un incendio; comburente.",
    "H300": "Mortal en caso de ingestión.",
    "H300+H310": "Mortal en caso de ingestión o en contacto con la piel.",
    "H300+H310+H330": "Mortal en caso de ingestión, en contacto con la piel o si se inhala.",
    "H301": "Tóxico en caso de ingestión.",
    "H301+H311": "Tóxico en caso de ingestión o en contacto con la piel.",
    "H302": "Nocivo en caso de ingestión.",
    "H310": "Mortal en contacto con la piel.",
    "H310+H330": "Mortal en contacto con la piel o si se inhala.",
    "H311": "Tóxico en contacto con la piel.",
    "H312": "Nocivo en contacto con la piel.",
    "H315": "Provoca irritación cutánea.",
    "H318": "Provoca lesiones oculares graves.",
    "H319": "Provoca irritación ocular grave.",
    "H320": "Provoca irritación ocular.",
    "H413": "Puede ser nocivo para los organismos acuáticos, con efectos nocivos duraderos.",
}

# Una palabra difiere en 1-2 letras: errata o concordancia con la forma oficial.
# Aquí sí cambian las palabras, así que se guarda el texto que se espera
# encontrar: si la base dice otra cosa, alguien ya lo editó y no se toca.
SPELLING = {
    "H205": (
        "Peligro de expasión en masa en caso de incendio",
        "Peligro de explosión en masa en caso de incendio.",
    ),
    "H226": (
        "Liquido y vapores inflamables",
        "Líquidos y vapores inflamables.",
    ),
    "H290": (
        "Puede ser corrosiva para los metales",
        "Puede ser corrosivo para los metales.",
    ),
    "H400": (
        "Muy tóxicos para los organismos acuáticos",
        "Muy tóxico para los organismos acuáticos.",
    ),
    "H410": (
        "Muy tóxicos para los organismos acuáticos, con efectos nocivos duraderos",
        "Muy tóxico para los organismos acuáticos, con efectos nocivos duraderos.",
    ),
    "H411": (
        "Tóxicos para los organismos acuáticos, con efectos nocivos duraderos",
        "Tóxico para los organismos acuáticos, con efectos nocivos duraderos.",
    ),
    "H412": (
        "Nocivos para los organismos acuáticos, con efectos nocivos duraderos",
        "Nocivo para los organismos acuáticos, con efectos nocivos duraderos.",
    ),
}


def _normalize_code(code):
    """Forma canónica del código: sin espacios y en mayúsculas."""
    return re.sub(r"\s+", "", (code or "")).upper()


def _same_words(a, b):
    """Los dos textos coinciden salvo tildes, mayúsculas y puntuación."""

    def skeleton(text):
        plain = "".join(
            c
            for c in unicodedata.normalize("NFD", text or "")
            if unicodedata.category(c) != "Mn"
        )
        return re.sub(r"[^a-z0-9]", "", plain.lower())

    return skeleton(a) == skeleton(b)


def fix_spelling(apps, schema_editor):
    DangerIndication = apps.get_model("sga", "DangerIndication")

    updated = 0
    for indication in DangerIndication.objects.all():
        code = _normalize_code(indication.code)
        current = (indication.description or "").strip()

        # Una redacción cambiada a mano no se pisa: cada bloque comprueba que
        # el texto guardado siga siendo el que se detectó.
        if code in COSMETIC:
            replacement = COSMETIC[code]
            # Mismas palabras: basta con que sólo difiera en tildes o puntuación.
            if not _same_words(current, replacement):
                continue
        elif code in SPELLING:
            expected, replacement = SPELLING[code]
            if not _same_words(current, expected):
                continue
        else:
            continue

        if current == replacement:
            continue
        indication.description = replacement
        indication.save(update_fields=["description"])
        updated += 1

    if updated:
        print(f"  Indicaciones de peligro corregidas: {updated}")


class Migration(migrations.Migration):

    dependencies = [
        ("sga", "0096_fix_incomplete_ghs_phrases"),
    ]

    operations = [
        # Irreversible por diseño: la reversa devolvería las erratas.
        migrations.RunPython(fix_spelling, migrations.RunPython.noop),
    ]
