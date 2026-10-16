from django.core.files.base import ContentFile
from django.db.models import Min
from django.utils import timezone
from django.utils.translation import gettext as _

from laboratory.models import ObjectMaximumLimit, OrganizationStructure
from laboratory.report_utils import write_spreadsheet
from report.utils import (
    format_date,
    get_report_name,
)
from risk_management.utils_risk import (
    cargar_cuadro3,
    cargar_sga_referencia,
    clasificar_establecimiento,
    cargar_umbral_por_H,
    get_inventory,
)


def get_regency_filters(report):
    """Filtro del inventario, el mismo para XLS, XLSX y ODS.

    Toma los laboratorios elegidos (o todos los de la organización) y el
    `period` del formulario; sin periodo, o con una fecha que no se entiende,
    se usan todos los registros hasta hoy.
    """
    organization = OrganizationStructure.objects.filter(
        pk=report.data["organization"]
    ).first()
    filters = {
        "object__type": 0,
        "object__isnull": False,
        "measurement_unit__isnull": False,
        "laboratory__pk__in": organization.get_my_laboratories,
    }
    if report.data.get("laboratory"):
        filters.update({"laboratory__pk__in": report.data["laboratory"]})
    period = get_regency_period(report)
    if period:
        filters.update({"created_at__range": list(period)})
    return filters


def get_regency_period(report):
    """(inicio, fin) del `period` del formulario, o None si viene vacío o no se entiende."""
    dates = (report.data.get("period") or "").split("-")
    if len(dates) == 2:
        start, end = format_date(dates[0].strip()), format_date(dates[1].strip())
        if start and end:
            return start, end
    return None


def get_regency_period_label(report):
    """El período que cubren los datos, para mostrarlo en el resumen.

    Sin período elegido se usan todos los registros: va desde el primero
    hasta hoy.
    """
    period = get_regency_period(report)
    if period:
        start, end = period
    else:
        start = ObjectMaximumLimit.objects.filter(
            **get_regency_filters(report)
        ).aggregate(first=Min("created_at"))["first"]
        end = timezone.localdate()
        if start is None:
            return "-"
    return "%s - %s" % (start.strftime("%d/%m/%Y"), end.strftime("%d/%m/%Y"))


def get_regency_inventory(report):
    inv = get_inventory(get_regency_filters(report))
    return inv.drop_duplicates(subset=["nombre", "h_codes", "cas", "cantidad_t"])


def classify_regency(inv):
    c3 = cargar_cuadro3()
    c4 = cargar_umbral_por_H()
    mapH_tipo = cargar_sga_referencia()
    return clasificar_establecimiento(inv, c3, c4, mapH_tipo)


REGENCY_SHEETS = ("Resumen", "Sumatoria_categoría", "Detalle")
#: Ancho máximo de columna por hoja: el criterio del resumen es una frase que
#: debe verse entera (XLS no agranda la fila); el detalle se ajusta en líneas.
REGENCY_MAX_WIDTH = {"Resumen": 90}


def get_regency_detail_header():
    return [
        _("Name"),
        _("CAS"),
        _("Quantity"),
        _("Nominated"),
        _("Threshold"),
        _("Ratio"),
        _("H-codes"),
        _("Cross rule"),
        _("Detail"),
        _("Warnings"),
        _("Health contributions"),
        _("Physical contributions"),
        _("Environmental contributions"),
    ]


def get_regency_detail_row(details):
    return [
        details["nombre"],
        details["cas"],
        round(details["cantidad_t"], 3),
        _("Yes") if details["nominada_c3"] else _("No"),
        details["umbral_c3"],
        details["ratio_c3"],
        details["h_codes"],
        _("Yes") if details["regla_cruzada_salud"] else _("No"),
        " | ".join(details["detalle_contribuciones"] or []),
        " | ".join(details["advertencias"] or []),
        round(details["contribuciones"].get("Salud", 0.0), 3),
        round(details["contribuciones"].get("Físico", 0.0), 3),
        round(details["contribuciones"].get("Ambiental", 0.0), 3),
    ]


def get_regency_sheets(report):
    """Contenido del informe regencial, igual para XLSX, XLS y ODS.

    Devuelve ``(hojas, total)``: cada hoja es ``(nombre, filas)`` y cada fila
    ``(rol, celdas)``. El rol (title, label, header, cell, risk) dice cómo se
    dibuja; cada formato solo lo traduce a su librería, así las tres salidas
    no se desalinean. ``total`` es cuántas sustancias tiene el detalle.
    """
    title = report.data.get("title") or get_report_name(report)
    inv = get_regency_inventory(report)
    try:
        res = classify_regency(inv)
        # Las clasificaciones de «riesgo mayor» por Cuadro 3/4 no calculan
        # sumatorias y devuelven el diccionario vacío.
        sumatoria = res["sumatorias_por_categoria"]
        classification = [str(res["clasificacion"]), str(res["criterio"])]
        totals = [
            sumatoria.get("Físico", 0.0),
            sumatoria.get("Salud", 0.0),
            sumatoria.get("Ambiental", 0.0),
        ]
        detail = [("header", get_regency_detail_header())]
        detail += [("cell", get_regency_detail_row(d)) for d in res["detalles"]]
        total = len(res["detalles"])
    except Exception:
        classification = ["riesgo menor", ""]
        totals = [0.0, 0.0, 0.0]
        detail = [("cell", [_("Data not available")])]
        total = 0
    summary = [
        ("title", [title]),
        ("label", [_("Period"), get_regency_period_label(report)]),
        ("blank", []),
        ("header", [_("Classification"), _("Criterion")]),
        ("risk", classification),
    ]
    totals_sheet = [
        ("header", [_("Physical"), _("Health"), _("Environmental")]),
        ("cell", totals),
    ]
    return list(zip(REGENCY_SHEETS, (summary, totals_sheet, detail))), total


def save_regency_file(report, content):
    report_name = get_report_name(report)
    report.file = ContentFile(
        content.getvalue(), name=f"{report_name}.{report.file_type}"
    )
    report.save()


def report_regency(report):
    """XLSX, XLS y ODS: las mismas hojas, filas y estilos."""
    sheets, total = get_regency_sheets(report)
    book = []
    for name, rows in sheets:
        options = {"max_width": REGENCY_MAX_WIDTH.get(name, 50)}
        if rows and rows[0][0] == "header":
            options["freeze_row"] = 1
        book.append((name, rows, options))
    save_regency_file(report, write_spreadsheet(book, report.file_type))
    return total
