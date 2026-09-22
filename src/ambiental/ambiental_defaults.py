"""
Valores por defecto del módulo ambiental (consumos y residuos por edificio).

Las *listas* (tipos de recurso, unidades, tipos de punto, normalizadores,
tratamientos de residuo y niveles de alerta) se guardan como entradas del modelo
global ``laboratory.Catalog`` y se eligen con ``GTForeignKey`` filtrando por
``key``. Lo que ``Catalog`` no puede guardar (unidad por defecto, ícono, si el
recurso es un residuo y qué campos extra pide) vive aquí, indexado por el
``description`` sembrado.

Los textos sembrados son la **clave estable** de los metadatos: no deben
renombrarse sin actualizar este módulo. Mismo patrón que
``risk_management/iper_defaults.py``.
"""
from django.utils.translation import gettext_lazy as _

# --- keys de Catalog -------------------------------------------------------
KEY_RESOURCE_TYPE = "ambiental_resource_type"
KEY_MEASURE_UNIT = "ambiental_measure_unit"
KEY_POINT_TYPE = "ambiental_point_type"
KEY_NORMALIZER = "ambiental_normalizer"
KEY_WASTE_TREATMENT = "ambiental_waste_treatment"
KEY_ALERT_LEVEL = "ambiental_alert_level"

# --- unidades --------------------------------------------------------------
UNIT_CUBIC_METER = "m³"
UNIT_KWH = "kWh"
UNIT_LITER = "L"
UNIT_KILOGRAM = "kg"
UNIT_REAM = "resmas"
UNIT_UNITS = "unidades"
MEASURE_UNITS = (
    UNIT_CUBIC_METER,
    UNIT_KWH,
    UNIT_LITER,
    UNIT_KILOGRAM,
    UNIT_REAM,
    UNIT_UNITS,
)

# --- campos extra por recurso ----------------------------------------------
# nombre en extra_data -> etiqueta
EXTRA_FIELDS = {
    "vehicle_plate": _("Vehicle plate"),
    "fuel_type": _("Fuel type"),
    "paper_type": _("Paper type"),
    "waste_code": _("Waste code"),
    "manifest_number": _("Manifest number"),
}

WASTE_EXTRA_FIELDS = ("waste_code", "manifest_number")

# --- tipos de recurso ------------------------------------------------------
# description (clave) -> unidad por defecto, ícono (font awesome), residuo,
# campos extra permitidos en ConsumptionRecord.extra_data
RESOURCE_WATER = "Agua"
RESOURCE_ELECTRICITY = "Electricidad"
RESOURCE_FUEL = "Combustible"
RESOURCE_GAS = "Gas"
RESOURCE_PAPER = "Papel"
RESOURCE_SOLID_WASTE = "Residuo sólido separado"
RESOURCE_HAZARDOUS_WASTE = "Residuo peligroso"
RESOURCE_SPECIAL_WASTE = "Residuo especial"

RESOURCE_TYPES = {
    RESOURCE_WATER: {
        "unit": UNIT_CUBIC_METER,
        "icon": "fa-tint",
        "is_waste": False,
        "extra_fields": (),
    },
    RESOURCE_ELECTRICITY: {
        "unit": UNIT_KWH,
        "icon": "fa-bolt",
        "is_waste": False,
        "extra_fields": (),
    },
    RESOURCE_FUEL: {
        "unit": UNIT_LITER,
        "icon": "fa-car",
        "is_waste": False,
        "extra_fields": ("vehicle_plate", "fuel_type"),
    },
    RESOURCE_GAS: {
        "unit": UNIT_KILOGRAM,
        "icon": "fa-fire",
        "is_waste": False,
        "extra_fields": (),
    },
    RESOURCE_PAPER: {
        "unit": UNIT_REAM,
        "icon": "fa-file-text-o",
        "is_waste": False,
        "extra_fields": ("paper_type",),
    },
    RESOURCE_SOLID_WASTE: {
        "unit": UNIT_KILOGRAM,
        "icon": "fa-recycle",
        "is_waste": True,
        "extra_fields": WASTE_EXTRA_FIELDS,
    },
    RESOURCE_HAZARDOUS_WASTE: {
        "unit": UNIT_KILOGRAM,
        "icon": "fa-exclamation-triangle",
        "is_waste": True,
        "extra_fields": WASTE_EXTRA_FIELDS,
    },
    RESOURCE_SPECIAL_WASTE: {
        "unit": UNIT_KILOGRAM,
        "icon": "fa-trash",
        "is_waste": True,
        "extra_fields": WASTE_EXTRA_FIELDS,
    },
}

# --- tipos de punto de medición --------------------------------------------
POINT_TYPES = ("Medidor", "Tanque", "Punto de acopio", "Estimado")

# --- normalizadores --------------------------------------------------------
NORMALIZER_AREA = "Por m²"
NORMALIZER_PERSON = "Por persona"
NORMALIZERS = (NORMALIZER_AREA, NORMALIZER_PERSON)

# --- tratamientos de residuo -----------------------------------------------
WASTE_TREATMENTS = (
    "Reciclaje",
    "Incineración",
    "Relleno sanitario",
    "Gestor autorizado",
    "Devolución a proveedor",
)

# --- niveles de alerta -----------------------------------------------------
ALERT_LEVEL_INFO = "Informativa"
ALERT_LEVEL_MEDIUM = "Media"
ALERT_LEVEL_CRITICAL = "Crítica"
ALERT_LEVELS = (ALERT_LEVEL_INFO, ALERT_LEVEL_MEDIUM, ALERT_LEVEL_CRITICAL)


def get_resource_info(resource_type):
    """Metadatos de un tipo de recurso (``Catalog`` o su ``description``).

    Un recurso que no está en ``RESOURCE_TYPES`` (p. ej. agregado a mano en el
    catálogo) se trata como consumo sin campos extra ni unidad por defecto.
    """
    description = getattr(resource_type, "description", resource_type)
    return RESOURCE_TYPES.get(
        description,
        {"unit": None, "icon": "fa-leaf", "is_waste": False, "extra_fields": ()},
    )


def get_catalog_seed():
    """Devuelve la lista de tuplas ``(key, description)`` a sembrar en Catalog."""
    seed = []
    for desc in RESOURCE_TYPES:
        seed.append((KEY_RESOURCE_TYPE, desc))
    for desc in MEASURE_UNITS:
        seed.append((KEY_MEASURE_UNIT, desc))
    for desc in POINT_TYPES:
        seed.append((KEY_POINT_TYPE, desc))
    for desc in NORMALIZERS:
        seed.append((KEY_NORMALIZER, desc))
    for desc in WASTE_TREATMENTS:
        seed.append((KEY_WASTE_TREATMENT, desc))
    for desc in ALERT_LEVELS:
        seed.append((KEY_ALERT_LEVEL, desc))
    return seed


def seed_ambiental(Catalog):
    """Siembra idempotente de los catálogos ambientales.

    Recibe la clase ``Catalog`` (real o histórica) para poder invocarse tanto
    desde ``migrations.RunPython`` como desde un management command.
    """
    for key, description in get_catalog_seed():
        Catalog.objects.get_or_create(key=key, description=description)
