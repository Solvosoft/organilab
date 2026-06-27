# -*- coding: utf-8 -*-
"""
Catálogo de indicaciones de peligro (H) y consejos de prudencia (P) del SGA,
en español (RTCR 481:2015 / GHS rev.).

El motor expande un código (p.ej. ``H314``) a su frase completa para mostrarla en
la etiqueta, como exige el SGA. Si un código no está en el catálogo, se conserva el
código tal cual (fallback). El texto libre que no sea un código se respeta sin tocar.
"""
from __future__ import annotations

import re

# ─────────────────────────────────────────────────────────────────────────────
# Indicaciones de peligro (H)
# ─────────────────────────────────────────────────────────────────────────────
H_PHRASES: dict[str, str] = {
    "H200": "Explosivo inestable.",
    "H201": "Explosivo; peligro de explosión en masa.",
    "H202": "Explosivo; grave peligro de proyección.",
    "H203": "Explosivo; peligro de incendio, de onda expansiva o de proyección.",
    "H204": "Peligro de incendio o de proyección.",
    "H205": "Peligro de explosión en masa en caso de incendio.",
    "H220": "Gas extremadamente inflamable.",
    "H221": "Gas inflamable.",
    "H222": "Aerosol extremadamente inflamable.",
    "H223": "Aerosol inflamable.",
    "H224": "Líquido y vapores extremadamente inflamables.",
    "H225": "Líquido y vapores muy inflamables.",
    "H226": "Líquidos y vapores inflamables.",
    "H228": "Sólido inflamable.",
    "H240": "Peligro de explosión en caso de calentamiento.",
    "H241": "Peligro de incendio o explosión en caso de calentamiento.",
    "H242": "Peligro de incendio en caso de calentamiento.",
    "H250": "Se inflama espontáneamente en contacto con el aire.",
    "H260": "En contacto con el agua desprende gases inflamables que pueden inflamarse espontáneamente.",
    "H261": "En contacto con el agua desprende gases inflamables.",
    "H270": "Puede provocar o agravar un incendio; comburente.",
    "H271": "Puede provocar un incendio o una explosión; muy comburente.",
    "H272": "Puede agravar un incendio; comburente.",
    "H280": "Contiene gas a presión; peligro de explosión en caso de calentamiento.",
    "H281": "Contiene un gas refrigerado; puede provocar quemaduras o lesiones criogénicas.",
    "H290": "Puede ser corrosivo para los metales.",
    "H300": "Mortal en caso de ingestión.",
    "H301": "Tóxico en caso de ingestión.",
    "H302": "Nocivo en caso de ingestión.",
    "H304": "Puede ser mortal en caso de ingestión y penetración en las vías respiratorias.",
    "H310": "Mortal en contacto con la piel.",
    "H311": "Tóxico en contacto con la piel.",
    "H312": "Nocivo en contacto con la piel.",
    "H314": "Provoca quemaduras graves en la piel y lesiones oculares graves.",
    "H315": "Provoca irritación cutánea.",
    "H317": "Puede provocar una reacción alérgica en la piel.",
    "H318": "Provoca lesiones oculares graves.",
    "H319": "Provoca irritación ocular grave.",
    "H320": "Provoca irritación ocular.",
    "H330": "Mortal en caso de inhalación.",
    "H331": "Tóxico en caso de inhalación.",
    "H332": "Nocivo en caso de inhalación.",
    "H334": "Puede provocar síntomas de alergia o asma o dificultades respiratorias en caso de inhalación.",
    "H335": "Puede irritar las vías respiratorias.",
    "H336": "Puede provocar somnolencia o vértigo.",
    "H340": "Puede provocar defectos genéticos.",
    "H341": "Se sospecha que provoca defectos genéticos.",
    "H350": "Puede provocar cáncer.",
    "H351": "Se sospecha que provoca cáncer.",
    "H360": "Puede perjudicar la fertilidad o dañar al feto.",
    "H361": "Se sospecha que puede perjudicar la fertilidad o dañar al feto.",
    "H362": "Puede perjudicar a los niños alimentados con leche materna.",
    "H370": "Provoca daños en los órganos.",
    "H371": "Puede provocar daños en los órganos.",
    "H372": "Provoca daños en los órganos tras exposiciones prolongadas o repetidas.",
    "H373": "Puede provocar daños en los órganos tras exposiciones prolongadas o repetidas.",
    "H400": "Muy tóxico para los organismos acuáticos.",
    "H410": "Muy tóxico para los organismos acuáticos, con efectos nocivos duraderos.",
    "H411": "Tóxico para los organismos acuáticos, con efectos nocivos duraderos.",
    "H412": "Nocivo para los organismos acuáticos, con efectos nocivos duraderos.",
    "H413": "Puede ser nocivo para los organismos acuáticos, con efectos nocivos duraderos.",
}

# ─────────────────────────────────────────────────────────────────────────────
# Consejos de prudencia (P)
# ─────────────────────────────────────────────────────────────────────────────
P_PHRASES: dict[str, str] = {
    "P210": "Mantener alejado del calor, de superficies calientes, de chispas, de llamas abiertas y de cualquier otra fuente de ignición. No fumar.",
    "P220": "Mantener alejado de la ropa y otros materiales combustibles.",
    "P222": "No dejar que entre en contacto con el aire.",
    "P223": "Evitar todo contacto con el agua.",
    "P231": "Manipular y almacenar en gas inerte.",
    "P233": "Mantener el recipiente herméticamente cerrado.",
    "P235": "Mantener en lugar fresco.",
    "P240": "Conectar a tierra y enlace equipotencial del recipiente y del equipo receptor.",
    "P241": "Utilizar material eléctrico, de ventilación o de iluminación antideflagrante.",
    "P242": "Utilizar únicamente herramientas que no produzcan chispas.",
    "P243": "Tomar medidas de precaución contra las descargas electrostáticas.",
    "P244": "Mantener las válvulas y los racores libres de aceite y grasa.",
    "P250": "Evitar la abrasión, el choque y la fricción.",
    "P260": "No respirar el polvo, el humo, el gas, la niebla, los vapores o el aerosol.",
    "P261": "Evitar respirar el polvo, el humo, el gas, la niebla, los vapores o el aerosol.",
    "P264": "Lavarse concienzudamente tras la manipulación.",
    "P270": "No comer, beber ni fumar durante su utilización.",
    "P271": "Utilizar únicamente en exteriores o en un lugar bien ventilado.",
    "P273": "Evitar su liberación al medio ambiente.",
    "P280": "Llevar guantes, prendas y protección para los ojos y la cara.",
    "P281": "Utilizar el equipo de protección individual obligatorio.",
    "P282": "Llevar guantes que aíslen del frío y protección para la cara y los ojos.",
    "P284": "Llevar equipo de protección respiratoria.",
    "P301": "EN CASO DE INGESTIÓN:",
    "P302": "EN CASO DE CONTACTO CON LA PIEL:",
    "P303": "EN CASO DE CONTACTO CON LA PIEL (o el pelo):",
    "P304": "EN CASO DE INHALACIÓN:",
    "P305": "EN CASO DE CONTACTO CON LOS OJOS:",
    "P306": "EN CASO DE CONTACTO CON LA ROPA:",
    "P308": "EN CASO DE exposición manifiesta o presunta:",
    "P310": "Llamar inmediatamente a un CENTRO DE TOXICOLOGÍA o a un médico.",
    "P311": "Llamar a un CENTRO DE TOXICOLOGÍA o a un médico.",
    "P312": "Llamar a un CENTRO DE TOXICOLOGÍA o a un médico en caso de malestar.",
    "P321": "Se necesita un tratamiento específico (ver en la etiqueta).",
    "P330": "Enjuagarse la boca.",
    "P331": "NO provocar el vómito.",
    "P352": "Lavar con abundante agua y jabón.",
    "P364": "Y lavarla antes de volver a usarla.",
    "P378": "Utilizar el medio de extinción adecuado.",
    "P332": "En caso de irritación cutánea, consultar a un médico.",
    "P333": "En caso de irritación o erupción cutánea, consultar a un médico.",
    "P336": "Descongelar las partes heladas con agua tibia. No frotar la zona afectada.",
    "P337": "Si persiste la irritación ocular, consultar a un médico.",
    "P338": "Quitar las lentes de contacto, si lleva y resulta fácil. Seguir aclarando.",
    "P340": "Transportar a la persona al aire libre y mantenerla en una posición que le facilite la respiración.",
    "P351": "Aclarar cuidadosamente con agua durante varios minutos.",
    "P353": "Aclararse la piel con agua o ducharse.",
    "P361": "Quitar inmediatamente toda la ropa contaminada.",
    "P362": "Quitar la ropa contaminada y lavarla antes de volver a usarla.",
    "P363": "Lavar la ropa contaminada antes de volver a usarla.",
    "P370": "En caso de incendio:",
    "P371": "En caso de incendio importante y de grandes cantidades:",
    "P403": "Almacenar en un lugar bien ventilado.",
    "P405": "Guardar bajo llave.",
    "P410": "Proteger de la luz del sol.",
    "P411": "Almacenar a temperatura que no exceda la indicada.",
    "P420": "Almacenar separadamente.",
    "P501": "Eliminar el contenido y el recipiente conforme a la reglamentación vigente.",
}


# ─────────────────────────────────────────────────────────────────────────────
# Combinaciones oficiales SGA (frases combinadas).
# La clave es la tupla de códigos en su orden canónico; el valor es el texto
# conjunto. El motor agrupa los códigos presentes en una de estas combinaciones y
# muestra el texto combinado (p.ej. P305+P351+P338).
# ─────────────────────────────────────────────────────────────────────────────
H_COMBINATIONS: dict[tuple[str, ...], str] = {
    ("H300", "H310"): "Mortal en caso de ingestión o en contacto con la piel.",
    ("H300", "H330"): "Mortal en caso de ingestión o en caso de inhalación.",
    ("H310", "H330"): "Mortal en contacto con la piel o si se inhala.",
    ("H300", "H310", "H330"): "Mortal en caso de ingestión, en contacto con la piel o si se inhala.",
    ("H301", "H311"): "Tóxico en caso de ingestión o en contacto con la piel.",
    ("H301", "H331"): "Tóxico en caso de ingestión o en caso de inhalación.",
    ("H311", "H331"): "Tóxico en contacto con la piel o si se inhala.",
    ("H301", "H311", "H331"): "Tóxico en caso de ingestión, en contacto con la piel o si se inhala.",
    ("H302", "H312"): "Nocivo en caso de ingestión o en contacto con la piel.",
    ("H302", "H332"): "Nocivo en caso de ingestión o en caso de inhalación.",
    ("H312", "H332"): "Nocivo en contacto con la piel o si se inhala.",
    ("H302", "H312", "H332"): "Nocivo en caso de ingestión, en contacto con la piel o si se inhala.",
}

P_COMBINATIONS: dict[tuple[str, ...], str] = {
    ("P301", "P310"): "EN CASO DE INGESTIÓN: Llamar inmediatamente a un CENTRO DE TOXICOLOGÍA o a un médico.",
    ("P301", "P312"): "EN CASO DE INGESTIÓN: Llamar a un CENTRO DE TOXICOLOGÍA o a un médico en caso de malestar.",
    ("P301", "P330", "P331"): "EN CASO DE INGESTIÓN: Enjuagarse la boca. NO provocar el vómito.",
    ("P302", "P352"): "EN CASO DE CONTACTO CON LA PIEL: Lavar con abundante agua y jabón.",
    ("P303", "P361", "P353"): "EN CASO DE CONTACTO CON LA PIEL (o el pelo): Quitar inmediatamente toda la ropa contaminada. Aclararse la piel con agua o ducharse.",
    ("P304", "P340"): "EN CASO DE INHALACIÓN: Transportar a la persona al aire libre y mantenerla en una posición que le facilite la respiración.",
    ("P305", "P351", "P338"): "EN CASO DE CONTACTO CON LOS OJOS: Aclarar cuidadosamente con agua durante varios minutos. Quitar las lentes de contacto, si lleva y resulta fácil. Seguir aclarando.",
    ("P308", "P313"): "EN CASO DE exposición manifiesta o presunta: Consultar a un médico.",
    ("P333", "P313"): "En caso de irritación o erupción cutánea: Consultar a un médico.",
    ("P337", "P313"): "Si persiste la irritación ocular: Consultar a un médico.",
    ("P342", "P311"): "En caso de síntomas respiratorios: Llamar a un CENTRO DE TOXICOLOGÍA o a un médico.",
    ("P361", "P364"): "Quitar inmediatamente toda la ropa contaminada y lavarla antes de volver a usarla.",
    ("P370", "P378"): "En caso de incendio: Utilizar el medio de extinción adecuado.",
    ("P403", "P233"): "Almacenar en un lugar bien ventilado. Mantener el recipiente herméticamente cerrado.",
    ("P403", "P235"): "Almacenar en un lugar bien ventilado. Mantener en lugar fresco.",
    ("P410", "P403"): "Proteger de la luz del sol. Almacenar en un lugar bien ventilado.",
    ("P410", "P412"): "Proteger de la luz del sol. No exponer a temperaturas superiores a 50 °C.",
    ("P411", "P235"): "Almacenar a una temperatura controlada. Mantener en lugar fresco.",
}


_CODE_RE = re.compile(r'^([HP]\d{3})([A-Za-z+]*)$')


def lookup(code: str) -> str | None:
    """Texto completo de un código H/P, o None si no está en el catálogo."""
    code = code.strip().upper()
    if code in H_PHRASES:
        return H_PHRASES[code]
    if code in P_PHRASES:
        return P_PHRASES[code]
    return None


def expand_item(item: str, with_code: bool = True) -> str:
    """Expande un ítem a su texto completo si es un código conocido.

    - ``'H314'`` → ``'H314 Provoca quemaduras graves...'`` (with_code=True).
    - Código desconocido o texto libre → se devuelve sin cambios.
    """
    s = item.strip()
    m = _CODE_RE.match(s)
    if not m:
        return s
    code = m.group(1)
    texto = lookup(code)
    if not texto:
        return s
    return f"{code} {texto}" if with_code else texto


def is_code(item: str) -> bool:
    """True si el ítem es un único código H/P (no texto libre)."""
    return bool(_CODE_RE.match(item.strip()))


def group_codes(items: list[str], kind: str) -> list[tuple[str | None, str]]:
    """Agrupa códigos en sus combinaciones SGA oficiales y devuelve los ítems a
    mostrar, en el orden de aparición, respetando el agrupamiento.

    kind: 'H' o 'P'. Devuelve una lista de ``(codigos_str, texto_completo)``:
    - combinación: ``('P305+P351+P338', 'EN CASO DE CONTACTO CON LOS OJOS: ...')``
    - código suelto: ``('P210', 'P210 Mantener alejado...')``
    - texto libre (no es código): ``(None, '<texto>')``
    Solo se agrupa cuando TODOS los códigos de una combinación están presentes
    (así el texto siempre se corresponde con la agrupación).
    """
    combos = H_COMBINATIONS if kind == 'H' else P_COMBINATIONS

    # Orden canónico SGA: si todos los ítems son códigos, ordenarlos por número
    # ascendente (p.ej. P305 antes de P310 = encabezado antes de la acción). El
    # texto libre se respeta tal cual (no se reordena).
    if items and all(_CODE_RE.match(it.strip()) for it in items):
        items = sorted(items, key=lambda it: int(_CODE_RE.match(it.strip()).group(1)[1:]))

    parsed = []          # (codigo|None, raw)
    present = set()
    for it in items:
        mobj = _CODE_RE.match(it.strip())
        if mobj:
            parsed.append((mobj.group(1), it))
            present.add(mobj.group(1))
        else:
            parsed.append((None, it))

    # Combinaciones aplicables (todas sus partes presentes); las más largas primero.
    used: set[str] = set()
    applicable: dict[str, tuple[tuple[str, ...], str]] = {}  # codigo -> (combo, texto)
    for combo, texto in sorted(combos.items(), key=lambda kv: -len(kv[0])):
        if all(c in present and c not in used for c in combo):
            used.update(combo)
            for c in combo:
                applicable[c] = (combo, texto)

    out: list[tuple[str | None, str]] = []
    emitted: set[tuple[str, ...]] = set()
    for code, raw in parsed:
        if code is None:
            out.append((None, raw.strip()))
            continue
        if code in applicable:
            combo, texto = applicable[code]
            if combo not in emitted:
                emitted.add(combo)
                codes_str = "+".join(combo)
                out.append((codes_str, f"{codes_str} {texto}"))
            # si ya se emitió la combinación, este código se omite (va incluido).
        else:
            out.append((code, expand_item(raw, with_code=True)))
    return out
