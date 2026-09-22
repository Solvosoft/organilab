"""Parámetros del sistema por organización.

Registro declarativo, análogo a ``report/register.py``: cada app agrega aquí los
parámetros que lee, con su tipo, su valor por defecto y el permiso que hace falta para
cambiarlo. El valor efectivo en una organización sale de, en orden:

1. el valor propio de la organización (``SystemParameter``);
2. el del ancestro más cercano que lo haya fijado;
3. el ``default`` del registro.

``get_parameter`` es lo que usa el código; ``resolve_parameter`` dice además de dónde
salió el valor, que es lo que muestra la pantalla de parámetros.
"""
import datetime
import json
from decimal import Decimal

from django.utils.translation import gettext_lazy as _

INT = "int"
FLOAT = "float"
DECIMAL = "decimal"
BOOL = "bool"
STR = "str"
DATE = "date"
JSON = "json"
DATA_TYPES = (
    (INT, _("Integer")),
    (FLOAT, _("Float")),
    (DECIMAL, _("Decimal")),
    (BOOL, _("Yes/No")),
    (STR, _("Text")),
    (DATE, _("Date (YYYY-MM-DD)")),
    (JSON, _("JSON")),
)

ORIGIN_OWN = "own"
ORIGIN_INHERITED = "inherited"
ORIGIN_DEFAULT = "default"
ORIGINS = {
    ORIGIN_OWN: _("Own"),
    ORIGIN_INHERITED: _("Inherited"),
    ORIGIN_DEFAULT: _("Default"),
}

PARAMETERS = {
    "ambiental.require_document": {
        "type": BOOL,
        "default": False,
        "label": _("Require a supporting document for consumption records"),
        "description": _("If enabled, a consumption or waste record cannot be saved without its bill or manifest."),
        "permission": "ambiental.add_measurementpoint",
    },
    "ambiental.alert_window_months": {
        "type": INT,
        "default": 12,
        "label": _("Months of history to detect atypical consumption"),
        "description": _("The last period of a measurement point is compared against the average of this many previous months."),
        "permission": "ambiental.add_measurementpoint",
    },
}

TRUE_VALUES = ("1", "true", "yes", "si", "sí", "on")
FALSE_VALUES = ("0", "false", "no", "off", "")


def get_definition(key):
    return PARAMETERS[key]


def cast_value(data_type, raw):
    """Texto guardado -> valor Python. Lanza ``ValueError`` si no es válido."""
    raw = "" if raw is None else str(raw).strip()
    if data_type == BOOL:
        lowered = raw.lower()
        if lowered in TRUE_VALUES:
            return True
        if lowered in FALSE_VALUES:
            return False
        raise ValueError(raw)
    if data_type == INT:
        return int(raw)
    if data_type == FLOAT:
        return float(raw)
    if data_type == DECIMAL:
        try:
            return Decimal(raw)
        except Exception:
            raise ValueError(raw)
    if data_type == DATE:
        return datetime.date.fromisoformat(raw)
    if data_type == JSON:
        return json.loads(raw)
    return raw


def serialize_value(data_type, value):
    """Valor Python -> texto que se guarda y se muestra en el formulario."""
    if value is None:
        return ""
    if data_type == BOOL:
        return "true" if value else "false"
    if data_type == DATE:
        return value.isoformat()
    if data_type == JSON:
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def organization_chain(organization):
    """La organización y sus ancestros, del más cercano al más lejano."""
    return [organization] + list(reversed(list(organization.ancestors())))


def resolve_parameter(organization, key):
    """``{"value", "origin", "source"}`` del parámetro en la organización."""
    from presentation.models import SystemParameter

    definition = get_definition(key)
    chain = organization_chain(organization)
    rows = {
        row.organization_id: row
        for row in SystemParameter.objects.filter(key=key, organization__in=chain)
    }
    for position, org in enumerate(chain):
        row = rows.get(org.pk)
        if row is None:
            continue
        try:
            value = cast_value(definition["type"], row.raw_value)
        except (TypeError, ValueError):
            continue
        return {
            "value": value,
            "origin": ORIGIN_OWN if position == 0 else ORIGIN_INHERITED,
            "source": org,
        }
    return {"value": definition["default"], "origin": ORIGIN_DEFAULT, "source": None}


def get_parameter(organization, key, request=None):
    """El valor efectivo del parámetro. Con ``request`` se cachea durante la petición."""
    from laboratory.models import OrganizationStructure

    if not hasattr(organization, "pk"):
        organization = OrganizationStructure.objects.get(pk=organization)
    cache = None
    if request is not None:
        cache = request.__dict__.setdefault("_system_parameters", {})
        if (organization.pk, key) in cache:
            return cache[(organization.pk, key)]
    value = resolve_parameter(organization, key)["value"]
    if cache is not None:
        cache[(organization.pk, key)] = value
    return value


def visible_parameters(user):
    """Las claves que el usuario puede ver y cambiar, según el permiso de cada una."""
    return [
        key for key, definition in PARAMETERS.items()
        if not definition.get("permission") or user.has_perm(definition["permission"])
    ]
