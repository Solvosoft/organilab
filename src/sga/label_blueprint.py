# -*- coding: utf-8 -*-
"""
Capa de mapeo Organilab → ``LabelBlueprint`` del motor de etiquetas.

Convierte las entidades del dominio (``sga.Substance`` del catálogo y
``laboratory.ShelfObject`` —la instancia física en el laboratorio—) en un
``LabelBlueprint`` listo para ``sga.label_engine.LabelEngine``.

Aporta lo que el motor por sí solo no sabe del dominio Organilab:
- pictogramas GHS derivados de los H-codes (``HCODE_PICTOGRAMAS``),
- palabra de advertencia más severa,
- color del contenedor heredado del estante (``Shelf.color``) y
- tamaño de etiqueta coherente con la capacidad del envase.
"""
from __future__ import annotations

from sga.label_engine import LabelBlueprint

# ──────────────────────────────────────────────────────────────────────────────
# Mapa H-code → pictograma(s) GHS (nombres que entiende el motor, PICTOGRAMAS_OSHA)
# ──────────────────────────────────────────────────────────────────────────────
HCODE_PICTOGRAMAS = {
    'H200': ['Explosivo'], 'H201': ['Explosivo'], 'H202': ['Explosivo'],
    'H203': ['Explosivo'], 'H204': ['Explosivo'], 'H205': ['Explosivo'],
    'H220': ['Inflamable'], 'H221': ['Inflamable'], 'H222': ['Inflamable'],
    'H223': ['Inflamable'], 'H224': ['Inflamable'], 'H225': ['Inflamable'],
    'H226': ['Inflamable'], 'H227': ['Inflamable'], 'H228': ['Inflamable'],
    'H229': ['Gas Comprimido'],
    'H240': ['Explosivo'], 'H241': ['Explosivo'], 'H242': ['Inflamable'],
    'H250': ['Inflamable'], 'H251': ['Inflamable'], 'H252': ['Inflamable'],
    'H260': ['Inflamable'], 'H261': ['Inflamable'],
    'H270': ['Comburente'], 'H271': ['Comburente'], 'H272': ['Comburente'],
    'H280': ['Gas Comprimido'], 'H281': ['Gas Comprimido'],
    'H290': ['Corrosivo'],
    'H300': ['Tóxico'], 'H301': ['Tóxico'], 'H302': ['Irritante'],
    'H304': ['Peligro para la Salud'], 'H305': ['Peligro para la Salud'],
    'H310': ['Tóxico'], 'H311': ['Tóxico'], 'H312': ['Irritante'],
    'H314': ['Corrosivo'], 'H315': ['Irritante'], 'H317': ['Irritante'],
    'H318': ['Corrosivo'], 'H319': ['Irritante'],
    'H330': ['Tóxico'], 'H331': ['Tóxico'], 'H332': ['Irritante'],
    'H334': ['Peligro para la Salud'], 'H335': ['Irritante'], 'H336': ['Irritante'],
    'H340': ['Peligro para la Salud'], 'H341': ['Peligro para la Salud'],
    'H350': ['Peligro para la Salud'], 'H351': ['Peligro para la Salud'],
    'H360': ['Peligro para la Salud'], 'H361': ['Peligro para la Salud'],
    'H362': ['Peligro para la Salud'],
    'H370': ['Peligro para la Salud'], 'H371': ['Peligro para la Salud'],
    'H372': ['Peligro para la Salud'], 'H373': ['Peligro para la Salud'],
    'H400': ['Peligro Ambiental'], 'H410': ['Peligro Ambiental'],
    'H411': ['Peligro Ambiental'], 'H412': ['Peligro Ambiental'],
    'H413': ['Peligro Ambiental'], 'H420': ['Peligro Ambiental'],
}

# Estado físico de Organilab → código de estado del motor ("l" → "(líq)").
PHYSICAL_STATUS_TO_ESTADO = {
    "liquid": "l", "viscuos liquid": "l", "colloidal": "l",
    "Gaseous": "g",
    "solid": "s", "solid powder": "s", "solid granular or crystalline": "s",
}

# Tamaños de etiqueta (mm) por tramo de capacidad del envase. Alineados con
# LABEL_SIZES del motor; el motor valida luego el mínimo legible.
SIZE_TIERS_MM = (
    (50, (50, 30)),      # ≤ 50 mL  → Pequeña
    (500, (70, 40)),     # ≤ 500 mL → Mediana
    (2000, (100, 60)),   # ≤ 2 L    → Grande
)
SIZE_DEFAULT_MM = (70, 40)       # capacidad desconocida → mediana
SIZE_LARGE_MM = (120, 80)        # > 2 L → Extra grande

# Factores de conversión de unidad de volumen → mililitros.
_VOLUME_TO_ML = {
    "ml": 1.0, "milliliter": 1.0, "mililitro": 1.0, "cc": 1.0, "cm3": 1.0,
    "l": 1000.0, "lt": 1000.0, "liter": 1000.0, "litro": 1000.0,
    "ul": 0.001, "microliter": 0.001, "microlitro": 0.001,
    "kl": 1_000_000.0,
}


# ──────────────────────────────────────────────────────────────────────────────
# Resolución de pictogramas y palabra de advertencia (portado de label_generator)
# ──────────────────────────────────────────────────────────────────────────────
def resolver_pictogramas(h_codes):
    """Nombres de pictogramas (los del motor) a partir de una lista de H-codes."""
    pictogramas = set()
    for code in h_codes:
        for parte in (p.strip() for p in code.replace(" + ", "+").split("+")):
            if parte in HCODE_PICTOGRAMAS:
                pictogramas.update(HCODE_PICTOGRAMAS[parte])
    return sorted(pictogramas)


def resolver_palabra_advertencia(warning_words):
    """Palabra de advertencia más severa de un iterable de ``WarningWord``."""
    palabra = ""
    for ww in warning_words:
        nombre = (getattr(ww, "name", "") or "").strip().lower()
        if nombre == "peligro":
            return "PELIGRO"
        if nombre in ("atención", "atencion"):
            palabra = "ATENCIÓN"
    return palabra


def _fields_from_danger_indications(danger_qs, *, extra_prudence=None,
                                    extra_warning=None, warning_word=None):
    """Campos GHS comunes (pictogramas, frases H/P y palabra) desde un queryset
    de ``DangerIndication``. Sirve tanto para ``Substance`` como para
    ``ShelfObject`` porque ambos exponen indicaciones de peligro homogéneas."""
    danger = list(danger_qs)

    frases_peligro = "\n".join(f"{di.code} - {di.description}" for di in danger)

    p_codes = set()
    warning_words = []
    for di in danger:
        if getattr(di, "warning_words", None):
            warning_words.append(di.warning_words)
        for pa in di.prudence_advice.all():
            p_codes.add((pa.code, pa.name))
    if extra_prudence:
        for pa in extra_prudence:
            p_codes.add((pa.code, pa.name))
    if extra_warning:
        warning_words.append(extra_warning)

    consejos = "\n".join(f"{code} - {name}" for code, name in sorted(p_codes))
    simbolos = resolver_pictogramas([di.code for di in danger])
    palabra = warning_word or resolver_palabra_advertencia(warning_words)

    return {
        "simbolos": simbolos,
        "frases_peligro": frases_peligro,
        "consejos_prudencia": consejos,
        "palabra_advertencia": palabra or "",
    }


# ──────────────────────────────────────────────────────────────────────────────
# Coherencia de tamaño según la capacidad del envase
# ──────────────────────────────────────────────────────────────────────────────
def _unit_name(unit):
    """Nombre normalizado (minúsculas) de un ``Catalog`` de unidades."""
    if unit is None:
        return ""
    return (getattr(unit, "description", "") or "").strip().lower()


def capacity_to_ml(value, unit):
    """Convierte ``value`` en la unidad ``unit`` (Catalog) a mililitros.

    Devuelve ``None`` si no hay valor o la unidad no es de volumen reconocida.
    """
    if value in (None, "", 0):
        return None
    factor = _VOLUME_TO_ML.get(_unit_name(unit))
    if factor is None:
        return None
    try:
        return float(value) * factor
    except (TypeError, ValueError):
        return None


def capacity_to_size_mm(capacity_ml):
    """Tamaño de etiqueta ``(ancho_mm, alto_mm)`` coherente con la capacidad."""
    if capacity_ml is None:
        return SIZE_DEFAULT_MM
    for limit, size in SIZE_TIERS_MM:
        if capacity_ml <= limit:
            return size
    return SIZE_LARGE_MM


def recipient_size_to_mm(recipient_size):
    """Convierte un ``sga.RecipientSize`` (cm/mm/inch) a ``(ancho_mm, alto_mm)``."""
    to_mm = {"mm": 1.0, "cm": 10.0, "inch": 25.4}
    width = float(recipient_size.width) * to_mm.get(recipient_size.width_unit, 10.0)
    height = float(recipient_size.height) * to_mm.get(recipient_size.height_unit, 10.0)
    return width, height


def _shelfobject_capacity_ml(shelfobject):
    """Capacidad del envase de un ``ShelfObject`` en mL.

    Prioriza la capacidad declarada del contenedor (``MaterialCapacity``) y, en
    su defecto, la cantidad almacenada con su unidad de medida.
    """
    obj = shelfobject.object
    material_capacity = getattr(obj, "materialcapacity", None)
    if material_capacity is not None:
        ml = capacity_to_ml(material_capacity.capacity,
                            material_capacity.capacity_measurement_unit)
        if ml is not None:
            return ml
    return capacity_to_ml(shelfobject.quantity, shelfobject.measurement_unit)


# ──────────────────────────────────────────────────────────────────────────────
# Color y ubicación del contenedor
# ──────────────────────────────────────────────────────────────────────────────
def _shelf_color(shelf):
    """Color del contenedor heredado del estante (fallback al mueble)."""
    if shelf is None:
        return ""
    if getattr(shelf, "color", ""):
        return shelf.color
    furniture = getattr(shelf, "furniture", None)
    return getattr(furniture, "color", "") or ""


def _apply_overrides(blueprint, overrides):
    """Aplica overrides (p.ej. params GET) sobre campos válidos del blueprint."""
    for key, value in overrides.items():
        if value in (None, ""):
            continue
        if hasattr(blueprint, key):
            setattr(blueprint, key, value)
    return blueprint


# ──────────────────────────────────────────────────────────────────────────────
# Constructores de blueprint
# ──────────────────────────────────────────────────────────────────────────────
def blueprint_from_substance(substance, *, organization=None, **overrides):
    """Construye un ``LabelBlueprint`` desde un ``sga.Substance`` del catálogo."""
    from sga.models import SGAComplement

    complement = SGAComplement.objects.filter(substance=substance).first()
    extra_prudence = complement.prudence_advice.all() if complement else None
    extra_warning = complement.warningword if complement else None

    fields = _fields_from_danger_indications(
        substance.danger_indications.all(),
        extra_prudence=extra_prudence,
        extra_warning=extra_warning,
        warning_word=substance.warning_word,
    )

    chars = getattr(substance, "substancecharacteristics", None)

    blueprint = LabelBlueprint(
        nombre=substance.comercial_name or substance.uipa_name or "",
        formula=getattr(chars, "molecular_formula", "") or "",
        cas=getattr(chars, "cas_id_number", "") or "",
        institucion=getattr(organization, "name", "") or "",
        **fields,
    )
    return _apply_overrides(blueprint, overrides)


def blueprint_from_displaylabel(display_label, *, organization=None, **overrides):
    """Construye un ``LabelBlueprint`` desde un ``sga.DisplayLabel`` del editor.

    Usa la sustancia asociada (si la hay), el tamaño del recipiente seleccionado
    y el logo personalizado de la etiqueta. Sirve para previsualizar y para
    guardar el PNG del motor en ``DisplayLabel.label_in_png``.
    """
    label = display_label.label
    substance = getattr(label, "substance", None)

    if substance is not None:
        blueprint = blueprint_from_substance(substance, organization=organization)
        if not blueprint.nombre:
            blueprint.nombre = display_label.name or ""
    else:
        blueprint = LabelBlueprint(
            nombre=display_label.name or "",
            institucion=getattr(organization, "name", "") or "",
        )

    # Tamaño según el recipiente seleccionado en el editor.
    recipient_size = display_label.recipient_size
    if recipient_size is not None:
        blueprint.ancho_mm, blueprint.alto_mm = recipient_size_to_mm(recipient_size)

    # Logo personalizado de la etiqueta (lado derecho del encabezado).
    logo = getattr(display_label, "logo", None)
    if logo:
        try:
            blueprint.logo_der_path = logo.path
        except (ValueError, NotImplementedError):
            pass

    return _apply_overrides(blueprint, overrides)


def blueprint_from_shelfobject(shelfobject, *, organization=None, **overrides):
    """Construye un ``LabelBlueprint`` desde un ``laboratory.ShelfObject``.

    Es la instancia física: hereda contenedor (color del estante), ubicación,
    cantidad, lote y caducidad, y ajusta el tamaño a la capacidad del envase.
    """
    obj = shelfobject.object
    chars = getattr(obj, "sustancecharacteristics", None)

    danger_qs = chars.h_code.all() if chars else []
    fields = _fields_from_danger_indications(danger_qs)

    # Tamaño coherente con la capacidad del envase.
    ancho_mm, alto_mm = capacity_to_size_mm(_shelfobject_capacity_ml(shelfobject))

    # Cantidad almacenada (con unidad).
    cantidad = ""
    if shelfobject.quantity is not None:
        unidad = getattr(shelfobject.measurement_unit, "description", "") or ""
        cantidad = f"{shelfobject.quantity:g} {unidad}".strip()

    # Ubicación legible: laboratorio · estante.
    lab = getattr(shelfobject.in_where_laboratory, "name", "") or ""
    shelf = shelfobject.shelf
    shelf_name = getattr(shelf, "name", "") or ""
    ubicacion = " · ".join(p for p in (lab, shelf_name) if p)

    # Nombre del recipiente: el contenedor padre si existe, si no el estante.
    if shelfobject.container_id and shelfobject.container:
        recipiente_nombre = getattr(shelfobject.container.object, "name", "") or shelf_name
    else:
        recipiente_nombre = shelf_name

    blueprint = LabelBlueprint(
        nombre=obj.name or "",
        formula=getattr(chars, "molecular_formula", "") or "",
        cas=getattr(chars, "cas_id_number", "") or "",
        estado_fisico=PHYSICAL_STATUS_TO_ESTADO.get(shelfobject.physical_status, ""),
        cantidad=cantidad,
        lote=shelfobject.batch or "",
        fecha_caducidad=(shelfobject.reactive_expiration_date.strftime("%d/%m/%Y")
                         if shelfobject.reactive_expiration_date else ""),
        ubicacion=ubicacion,
        institucion=getattr(organization, "name", "") or "",
        recipiente_nombre=recipiente_nombre,
        recipiente_color=_shelf_color(shelf),
        qr_url=shelfobject.shelf_object_url or "",
        ancho_mm=ancho_mm,
        alto_mm=alto_mm,
        **fields,
    )
    return _apply_overrides(blueprint, overrides)
