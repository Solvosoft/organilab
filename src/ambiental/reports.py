"""Reportes del módulo ambiental sobre la infraestructura de ``report``.

Cada reporte es una función ``rows(report) -> (columns, rows)``; ``html_report`` y
``doc_report`` la envuelven en los generadores que ``report/register.py`` espera
(pantalla/PDF y hojas de cálculo). Así las dos salidas de un reporte no se pueden
separar: salen de la misma función.

Todos los filtros viajan en ``report.data`` tal como los limpió
``AmbientalReportForm``: organización, edificios, tipos de recurso y período. El
período filtra por ``period_end`` (el mes facturado).
"""
from collections import OrderedDict
from decimal import Decimal

from django.core.files.base import ContentFile
from django.utils.translation import gettext as _

from ambiental.ambiental_defaults import KEY_NORMALIZER, KEY_RESOURCE_TYPE
from ambiental.indicators import compare_periods, compute_indicator
from ambiental.models import ConsumptionRecord
from laboratory.models import Catalog, OrganizationStructure
from risk_management.models import Buildings
from laboratory.report_utils import ExcelGraphBuilder
from report.utils import format_datetime, get_report_name, set_format_table_columns


def as_text(value):
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    return str(value)


def parse_period(value):
    """``"dd/mm/YYYY - dd/mm/YYYY"`` -> ``(date, date)`` o ``(None, None)``."""
    if not value:
        return None, None
    parts = value.split("-")
    if len(parts) != 2:
        return None, None
    start = format_datetime(parts[0].strip(), "initial")
    end = format_datetime(parts[1].strip(), "final")
    if start is None or end is None:
        return None, None
    return start.date(), end.date()


def report_records(report, period_field="period"):
    """Los registros de la organización que cumplen los filtros del reporte."""
    data = report.data
    queryset = ConsumptionRecord.objects.filter(
        organization__pk=data["organization"]
    ).select_related(
        "point__building", "point__resource_type", "unit", "treatment",
        "waste_manager", "created_by",
    )
    if data.get("building"):
        queryset = queryset.filter(point__building__pk__in=data["building"])
    if data.get("resource_type"):
        queryset = queryset.filter(point__resource_type__pk__in=data["resource_type"])
    start, end = parse_period(data.get(period_field))
    if start and end:
        queryset = queryset.filter(period_end__range=(start, end))
    return queryset


def month_label(date):
    return date.strftime("%Y-%m")


def html_report(rows_function):
    def generate(report):
        columns, rows = rows_function(report)
        report.table_content = {
            "columns": set_format_table_columns(
                [{"name": name, "title": title} for name, title in columns]
            ),
            "dataset": rows,
        }
        report.save()
        return len(rows)

    generate.__name__ = rows_function.__name__ + "_html"
    return generate


def doc_report(rows_function):
    def generate(report):
        columns, rows = rows_function(report)
        report_name = get_report_name(report)
        content = [[report_name], [title for _name, title in columns]] + rows
        file = ExcelGraphBuilder().save_ods(content, format_type=report.file_type)
        file.seek(0)
        report.file = ContentFile(file.getvalue(), name="%s.%s" % (report_name, report.file_type))
        report.save()
        file.close()
        return len(rows)

    generate.__name__ = rows_function.__name__ + "_doc"
    return generate


# ---------------------------------------------------------------------------
# Paso 4: detalle, consolidado y costos
# ---------------------------------------------------------------------------


def consumption_detail_rows(report):
    columns = [
        ("building", _("Building")),
        ("point", _("Measurement point")),
        ("resource", _("Resource type")),
        ("period_start", _("Period start")),
        ("period_end", _("Period end")),
        ("quantity", _("Quantity")),
        ("unit", _("Unit")),
        ("unit_cost", _("Unit cost")),
        ("total_cost", _("Total cost")),
        ("document", _("Supporting document")),
        ("created_by", _("Registered by")),
    ]
    rows = []
    for record in report_records(report).order_by("point__building__name", "point__code", "period_end"):
        rows.append([
            as_text(record.point.building),
            str(record.point),
            record.point.resource_type.description,
            record.period_start.isoformat(),
            record.period_end.isoformat(),
            as_text(record.quantity),
            record.unit.description,
            as_text(record.unit_cost),
            as_text(record.total_cost),
            _("Yes") if record.document else _("No"),
            record.created_by.get_username() if record.created_by else "",
        ])
    return columns, rows


def grouped_totals(queryset, keys):
    """Suma cantidad y costo por ``keys`` + mes de ``period_end``.

    El mes se agrupa en Python y no con ``TruncMonth`` para no depender de la zona
    horaria de la base al truncar un ``DateField``.
    """
    groups = OrderedDict()
    for record in queryset.order_by(*keys, "period_end"):
        key = tuple(_resolve(record, name) for name in keys) + (month_label(record.period_end),)
        total = groups.setdefault(key, {"quantity": Decimal(0), "cost": Decimal(0), "has_cost": False})
        total["quantity"] += record.quantity
        if record.total_cost is not None:
            total["cost"] += record.total_cost
            total["has_cost"] = True
    return groups


def _resolve(record, path):
    value = record
    for part in path.split("__"):
        value = getattr(value, part, None)
        if value is None:
            return ""
    return str(value)


def consumption_summary_rows(report):
    columns = [
        ("building", _("Building")),
        ("resource", _("Resource type")),
        ("month", _("Month")),
        ("quantity", _("Quantity")),
        ("unit", _("Unit")),
        ("total_cost", _("Total cost")),
    ]
    groups = grouped_totals(
        report_records(report),
        ["point__building__name", "point__resource_type__description", "unit__description"],
    )
    rows = [
        [building, resource, month, as_text(total["quantity"]), unit,
         as_text(total["cost"]) if total["has_cost"] else ""]
        for (building, resource, unit, month), total in groups.items()
    ]
    return columns, rows


def consumption_cost_rows(report):
    columns = [
        ("resource", _("Resource type")),
        ("month", _("Month")),
        ("quantity", _("Quantity")),
        ("unit", _("Unit")),
        ("unit_cost", _("Average unit cost")),
        ("total_cost", _("Total cost")),
    ]
    groups = grouped_totals(
        report_records(report).filter(total_cost__isnull=False),
        ["point__resource_type__description", "unit__description"],
    )
    rows = []
    for (resource, unit, month), total in groups.items():
        average = (total["cost"] / total["quantity"]).quantize(Decimal("0.0001")) if total["quantity"] else None
        rows.append([resource, month, as_text(total["quantity"]), unit, as_text(average), as_text(total["cost"])])
    return columns, rows


report_consumption_detail_html = html_report(consumption_detail_rows)
report_consumption_detail_doc = doc_report(consumption_detail_rows)
report_consumption_summary_html = html_report(consumption_summary_rows)
report_consumption_summary_doc = doc_report(consumption_summary_rows)
report_consumption_cost_html = html_report(consumption_cost_rows)
report_consumption_cost_doc = doc_report(consumption_cost_rows)


# ---------------------------------------------------------------------------
# Paso 5: indicadores y comparación entre períodos
# ---------------------------------------------------------------------------


def report_scope(report):
    """Organización, edificios y recursos que abarca el reporte."""
    data = report.data
    organization = OrganizationStructure.objects.get(pk=data["organization"])
    buildings = Buildings.objects.filter(organization=organization).order_by("name")
    if data.get("building"):
        buildings = buildings.filter(pk__in=data["building"])
    resources = Catalog.objects.filter(key=KEY_RESOURCE_TYPE).order_by("pk")
    if data.get("resource_type"):
        resources = resources.filter(pk__in=data["resource_type"])
    return organization, buildings, resources


def environmental_indicator_rows(report):
    columns = [
        ("building", _("Building")),
        ("resource", _("Resource type")),
        ("normalizer", _("Normalizer")),
        ("raw_total", _("Consumption")),
        ("unit", _("Unit")),
        ("base", _("Base")),
        ("base_year", _("Base year")),
        ("value", _("Indicator")),
    ]
    organization, buildings, resources = report_scope(report)
    start, end = parse_period(report.data.get("period"))
    normalizers = Catalog.objects.filter(key=KEY_NORMALIZER).order_by("pk")
    if report.data.get("normalizer"):
        normalizers = normalizers.filter(pk__in=report.data["normalizer"])
    rows = []
    for building in buildings:
        for resource in resources:
            for normalizer in normalizers:
                result = compute_indicator(organization, building, resource, normalizer, start, end)
                if not result["records"]:
                    continue
                value = as_text(result["value"])
                if result["mixed_units"]:
                    value = _("Mixed units")
                elif result["value"] is None:
                    value = _("No base")
                rows.append([
                    building.name, resource.description, normalizer.description,
                    as_text(result["raw_total"]), result["unit"] or "",
                    as_text(result["base"]), as_text(result["base_year"]), value,
                ])
    return columns, rows


def consumption_comparison_rows(report):
    columns = [
        ("building", _("Building")),
        ("resource", _("Resource type")),
        ("previous", _("Previous period")),
        ("current", _("Current period")),
        ("unit", _("Unit")),
        ("absolute", _("Absolute variation")),
        ("percent", _("Variation (%)")),
        ("previous_cost", _("Previous cost")),
        ("current_cost", _("Current cost")),
    ]
    organization, buildings, resources = report_scope(report)
    periods = [
        parse_period(report.data.get("comparison_period")),
        parse_period(report.data.get("period")),
    ]
    rows = []
    for building in buildings:
        for resource in resources:
            previous, current = compare_periods(organization, resource, periods, building)
            if previous["quantity"] is None and current["quantity"] is None and not current["mixed_units"]:
                continue
            rows.append([
                building.name, resource.description,
                as_text(previous["quantity"]), as_text(current["quantity"]),
                current["unit"] or previous["unit"] or "",
                _("Mixed units") if current["mixed_units"] else as_text(current["absolute"]),
                as_text(current["percent"]),
                as_text(previous["cost"]), as_text(current["cost"]),
            ])
    return columns, rows


report_environmental_indicators_html = html_report(environmental_indicator_rows)
report_environmental_indicators_doc = doc_report(environmental_indicator_rows)
report_consumption_comparison_html = html_report(consumption_comparison_rows)
report_consumption_comparison_doc = doc_report(consumption_comparison_rows)
