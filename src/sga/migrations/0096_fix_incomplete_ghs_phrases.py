# -*- coding: utf-8 -*-
"""Completa las frases H/P del catálogo GHS que quedaron a medias en la base.

Varios consejos de prudencia guardaban sólo su encabezado ("EN CASO DE
INHALACIÓN:") o un texto cortado ("Lavar con abundante agua/..."), de modo que
la etiqueta impresa perdía la acción de primeros auxilios: el dato más crítico
de la frase.

Procedencia de los textos:
- Bloque CATALOG: catálogo de referencia del motor de etiquetas
  (``sga.label_engine.phrases_catalog``), que llegó con el Etiquetador.
- Bloque OFFICIAL: redacción oficial en español del Reglamento CLP / SGA-ONU,
  para las combinaciones que el catálogo de referencia no cubre.

No se tocan:
- Las frases con hueco a completar por el proveedor (P230 "Mantener humidificado
  con ...", P401 "Almacenar conforme a..."), donde los puntos suspensivos son
  parte de la frase.
- Los códigos simples que son encabezado por norma (P301, P302, P304, P305,
  P306, P308, P370): terminar en ":" es correcto para ellos.
- Diferencias de redacción u ortografía: sólo se completan textos incompletos.
"""
import re

from django.db import migrations

# Textos tomados del catálogo de referencia del motor de etiquetas.
CATALOG = {
    "P231": "Manipular y almacenar en gas inerte.",
    "P250": "Evitar la abrasión, el choque y la fricción.",
    "P301+P310": "EN CASO DE INGESTIÓN: Llamar inmediatamente a un CENTRO DE TOXICOLOGÍA o a un médico.",
    "P301+P330+P331": "EN CASO DE INGESTIÓN: Enjuagarse la boca. NO provocar el vómito.",
    "P302+P352": "EN CASO DE CONTACTO CON LA PIEL: Lavar con abundante agua y jabón.",
    "P304+P340": "EN CASO DE INHALACIÓN: Transportar a la persona al aire libre y mantenerla en una posición que le facilite la respiración.",
    "P305+P351+P338": "EN CASO DE CONTACTO CON LOS OJOS: Aclarar cuidadosamente con agua durante varios minutos. Quitar las lentes de contacto, si lleva y resulta fácil. Seguir aclarando.",
    "P310": "Llamar inmediatamente a un CENTRO DE TOXICOLOGÍA o a un médico.",
    "P311": "Llamar a un CENTRO DE TOXICOLOGÍA o a un médico.",
    "P342+P311": "En caso de síntomas respiratorios: Llamar a un CENTRO DE TOXICOLOGÍA o a un médico.",
    "P352": "Lavar con abundante agua y jabón.",
    "P501": "Eliminar el contenido y el recipiente conforme a la reglamentación vigente.",
}

# Combinaciones que el catálogo de referencia no trae; redacción oficial CLP/SGA.
OFFICIAL = {
    "P302+P334": "EN CASO DE CONTACTO CON LA PIEL: Sumergir en agua fría o envolver con vendas húmedas.",
    "P302+P334+P335": "EN CASO DE CONTACTO CON LA PIEL: Sumergir en agua fría o envolver con vendas húmedas. Sacudir las partículas sueltas depositadas sobre la piel.",
    "P302+P335+P334": "EN CASO DE CONTACTO CON LA PIEL: Sacudir las partículas sueltas depositadas sobre la piel. Sumergir en agua fría o envolver con vendas húmedas.",
    "P306+P360": "EN CASO DE CONTACTO CON LA ROPA: Enjuagar inmediatamente con agua abundante la ropa y la piel contaminadas antes de quitarse la ropa.",
    "P308+P311": "EN CASO DE exposición manifiesta o presunta: Llamar a un CENTRO DE TOXICOLOGÍA o a un médico.",
    "P370+P372+P373+P380": "En caso de incendio: Riesgo de explosión. Evacuar la zona. NO combatir el incendio cuando este afecte a la carga.",
    "P371+P380+P375": "En caso de incendio importante y en grandes cantidades: Evacuar la zona. Combatir el incendio a distancia debido al riesgo de explosión.",
}

FIXES = {**CATALOG, **OFFICIAL}


def _normalize(code):
    """Forma canónica del código: sin espacios y en mayúsculas."""
    return re.sub(r"\s+", "", (code or "")).upper()


def _is_incomplete(code, text):
    """El texto guardado está a medias.

    Se considera incompleto si está vacío, si quedó cortado con puntos
    suspensivos, o si es una combinación que se quedó en su encabezado.
    """
    value = re.sub(r"\s+", " ", (text or "")).strip()
    if not value:
        return True
    if re.search(r"(\.\.\.|…)$", value):
        return True
    return value.endswith(":") and "+" in _normalize(code)


def fix_phrases(apps, schema_editor):
    PrudenceAdvice = apps.get_model("sga", "PrudenceAdvice")

    updated = 0
    for advice in PrudenceAdvice.objects.all():
        replacement = FIXES.get(_normalize(advice.code))
        # Sólo se corrige lo que sigue incompleto: una redacción ya arreglada a
        # mano no se pisa, y volver a aplicar la migración no cambia nada.
        if not replacement or not _is_incomplete(advice.code, advice.name):
            continue
        advice.name = replacement
        advice.save(update_fields=["name"])
        updated += 1

    if updated:
        print(f"  Frases de prudencia completadas: {updated}")

    # No se toca aquí la caché de frases del motor: vive en memoria de cada
    # proceso y se rehace al arrancar, así que los procesos nuevos ya leen los
    # textos corregidos.


class Migration(migrations.Migration):

    dependencies = [
        ("sga", "0095_recipientsize_laboratory"),
    ]

    operations = [
        # Irreversible por diseño: la reversa restauraría textos incompletos que
        # dejarían las etiquetas sin la acción de primeros auxilios.
        migrations.RunPython(fix_phrases, migrations.RunPython.noop),
    ]
