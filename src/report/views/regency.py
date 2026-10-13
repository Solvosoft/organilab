from django.core.files.base import ContentFile
from django.utils.translation import gettext as _

from laboratory.models import OrganizationStructure
from laboratory.report_utils import ExcelGraphBuilder
from report.utils import (
    format_date,
    get_report_name,
    sanitize_ods_table,
    set_format_table_columns,
)
from risk_management.utils_risk import (
    cargar_cuadro3,
    cargar_sga_referencia,
    clasificar_establecimiento,
    cargar_umbral_por_H,
    get_inventory,
)


REGENCY_DETAIL_COLUMNS = [
    ("nombre", "Nombre"),
    ("cas", "CAS"),
    ("cantidad_t", "Cantidad"),
    ("nominada", "Nominada"),
    ("umbral", "Umbral"),
    ("ratio", "Ratio"),
    ("h_codes", "H-codes"),
    ("regla_cruzada", "Regla Cruzada"),
    ("detalle", "Detalle"),
    ("advertencias", "Advertencias"),
    ("salud", "Contribuciones en salud"),
    ("fisico", "Contribuciones en físico"),
    ("ambiental", "Contribuciones en ambiente"),
]


def get_regency_result(report):
    filters = {
        "object__type": 0,
        "created_at__year": report.data["years"],
        "object__isnull": False,
        "measurement_unit__isnull": False,
        "laboratory__organization__pk": report.data["organization"],
    }
    if report.data["laboratory"]:
        filters.update({"laboratory__pk__in": report.data["laboratory"]})
    inv = get_inventory(filters)
    inv = inv.drop_duplicates(subset=["nombre", "h_codes", "cas", "cantidad_t"])
    c3 = cargar_cuadro3()
    c4 = cargar_umbral_por_H()
    mapH_tipo = cargar_sga_referencia()
    return clasificar_establecimiento(inv, c3, c4, mapH_tipo)


def get_regency_detail_rows(res):
    rows = []
    for data in res["detalles"]:
        rows.append(
            {
                "nombre": data["nombre"],
                "cas": data["cas"],
                "cantidad_t": data["cantidad_t"],
                "nominada": _("Yes") if data["nominada_c3"] else _("No"),
                "umbral": data["umbral_c3"] if data["umbral_c3"] else "",
                "ratio": data["ratio_c3"] if data["ratio_c3"] else "",
                "h_codes": data["h_codes"],
                "regla_cruzada": (
                    _("Yes") if data["regla_cruzada_salud"] else _("No")
                ),
                "detalle": (
                    data["detalle_contribuciones"]
                    if data["detalle_contribuciones"]
                    else "No hay detalle"
                ),
                "advertencias": (
                    data["advertencias"]
                    if data["advertencias"]
                    else "No hay advertencias"
                ),
                "salud": round(data["contribuciones"].get("Salud", 0.0), 3),
                "fisico": round(data["contribuciones"].get("Físico", 0.0), 3),
                "ambiental": round(data["contribuciones"].get("Ambiental", 0.0), 3),
            }
        )
    return rows


def report_regency_html(report):
    """Guarda el detalle como tabla, igual que el resto de reportes HTML.

    Antes armaba el HTML del PDF, lo descartaba y devolvía 0: el reporte en
    pantalla siempre salía vacío.
    """
    res = get_regency_result(report)
    sumatoria = res["sumatorias_por_categoria"]
    columns = [{"name": name, "title": _(title)} for name, title in REGENCY_DETAIL_COLUMNS]
    column_names = [name for name, _title in REGENCY_DETAIL_COLUMNS]
    rows = get_regency_detail_rows(res)
    report.table_content = {
        "columns": set_format_table_columns(columns),
        "dataset": [[row[name] for name in column_names] for row in rows],
        "summary": {
            "classification": str(res["clasificacion"]),
            "criterion": str(res["criterio"]),
            "physical": sumatoria.get("Físico", 0.0),
            "health": sumatoria.get("Salud", 0.0),
            "environmental": sumatoria.get("Ambiental", 0.0),
        },
    }
    report.save()
    return len(rows)


def report_regency_xlsx(report):
    builder = ExcelGraphBuilder()
    builder.ws.title = "Resumen"
    builder.wb.create_sheet("Sumatoria_categoría")
    builder.wb.create_sheet("Detalle")
    organization = OrganizationStructure.objects.filter(
        pk=report.data["organization"]
    ).first()

    filters = {
        "object__type": 0,
        "object__isnull": False,
        "measurement_unit__isnull": False,
        "laboratory__pk__in": organization.get_my_laboratories,
    }
    if report.data["laboratory"]:
        filters.update({"laboratory__pk__in": report.data["laboratory"]})
    if "period" in report.data:
        if report.data["period"]:
            dates = report.data["period"].split("-")
            if len(dates) == 2:
                dates[0] = format_date(dates[0].strip())
                dates[1] = format_date(dates[1].strip())
                filters.update({"created_at__range": dates})

    inv = get_inventory(filters)
    inv = inv.drop_duplicates(subset=["nombre", "h_codes", "cas", "cantidad_t"])
    c3 = cargar_cuadro3()
    c4 = cargar_umbral_por_H()
    mapH_tipo = cargar_sga_referencia()
    try:

        res = clasificar_establecimiento(inv, c3, c4, mapH_tipo)

        builder.ws.append([_("Classification"), _("Criterion")])
        builder.ws.append([str(res["clasificacion"]), str(res["criterio"])])
        builder.style_header()
        builder.autosize_columns()

        # Las clasificaciones de «riesgo mayor» por Cuadro 3/4 no calculan
        # sumatorias y devuelven el diccionario vacío: indexarlo tiraba KeyError
        # y el `except` de abajo publicaba «riesgo menor», justo lo contrario.
        sumatoria = res["sumatorias_por_categoria"]

        builder.ws = builder.wb["Sumatoria_categoría"]
        builder.ws.append([_("Physical"), _("Health"), _("Environmental")])
        builder.ws.append(
            [
                sumatoria.get("Físico", 0.0),
                sumatoria.get("Salud", 0.0),
                sumatoria.get("Ambiental", 0.0),
            ]
        )
        builder.style_header()
        builder.autosize_columns()

        builder.ws = builder.wb["Detalle"]
        builder.ws.append(
            [
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
        )

        for details in res["detalles"]:
            builder.ws.append(
                [
                    details["nombre"],
                    details["cas"],
                    round(details["cantidad_t"], 3),
                    builder.safe_bool(details["nominada_c3"]),
                    details["umbral_c3"],
                    details["ratio_c3"],
                    details["h_codes"],
                    builder.safe_bool(details["regla_cruzada_salud"]),
                    (
                        " | ".join(details["detalle_contribuciones"])
                        if details["detalle_contribuciones"]
                        else ""
                    ),
                    " | ".join(
                        details["advertencias"] if details["advertencias"] else ""
                    ),
                    round(details["contribuciones"].get("Salud", 0.0), 3),
                    round(details["contribuciones"].get("Físico", 0.0), 3),
                    round(details["contribuciones"].get("Ambiental", 0.0), 3),
                ]
            )
        builder.style_header()
        builder.autosize_columns()
        builder.format_border_cell(len(res["detalles"]), 13)

    except Exception as e:
        builder.ws.append([_("Classification"), _("Criterion")])
        builder.ws.append(["riesgo menor", ""])
        builder.style_header()
        builder.autosize_columns()
        builder.ws = builder.wb["Sumatoria_categoría"]
        builder.ws.append([_("Physical"), _("Health"), _("Environmental")])
        builder.ws.append(
            [
                0.0,
                0.0,
                0.0,
            ]
        )
        builder.style_header()
        builder.autosize_columns()

        builder.ws = builder.wb["Detalle"]
        builder.ws.append(
            [
                _("Data not available"),
            ]
        )

    report_name = get_report_name(report)
    file = builder.save()
    file_name = f"{report_name}.{report.file_type}"
    file.seek(0)
    doc = ContentFile(file.getvalue(), name=file_name)
    report.file = doc
    report.save()
    return 0


def report_regency_doc(report):
    builder = ExcelGraphBuilder()
    organization = OrganizationStructure.objects.filter(
        pk=report.data["organization"]
    ).first()
    filters = {
        "object__type": 0,
        "object__isnull": False,
        "measurement_unit__isnull": False,
        "laboratory__pk__in": organization.get_my_laboratories,
    }
    if "period" in report.data:
        if report.data["period"]:
            dates = report.data["period"].split("-")
            if len(dates) == 2:
                dates[0] = format_date(dates[0].strip())
                dates[1] = format_date(dates[1].strip())
                filters.update({"created_at__range": dates})

    if report.data["laboratory"]:
        filters.update({"laboratory__pk__in": report.data["laboratory"]})
    content = []
    inv = get_inventory(filters)
    inv = inv.drop_duplicates(subset=["nombre", "h_codes", "cas", "cantidad_t"])
    c3 = cargar_cuadro3()
    c4 = cargar_umbral_por_H()
    mapH_tipo = cargar_sga_referencia()
    try:
        res = clasificar_establecimiento(inv, c3, c4, mapH_tipo)
        # Las clasificaciones de «riesgo mayor» por Cuadro 3/4 no calculan
        # sumatorias y devuelven el diccionario vacío: indexarlo tiraba KeyError
        # y el `except` de abajo publicaba «riesgo menor», justo lo contrario.
        sumatoria = res["sumatorias_por_categoria"]
        content = [
            [_("Classification"), _("Criterion")],
            [str(res["clasificacion"]), str(res["criterio"])],
            [],
            [_("Totals by category")],
            [_("Physical"), _("Health"), _("Environmental")],
            [
                sumatoria.get("Físico", 0.0),
                sumatoria.get("Salud", 0.0),
                sumatoria.get("Ambiental", 0.0),
            ],
        ]
        content.append([])
        content.append([_("Details of the substances")])
        content.append(
            [
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
        )

        for details in res["detalles"]:
            content.append(
                [
                    details["nombre"],
                    details["cas"],
                    round(details["cantidad_t"], 3),
                    _("Yes") if details["nominada_c3"] else _("No"),
                    details["umbral_c3"],
                    details["ratio_c3"],
                    details["h_codes"],
                    _("Yes") if details["regla_cruzada_salud"] else _("No"),
                    (
                        " | ".join(details["detalle_contribuciones"])
                        if details["detalle_contribuciones"]
                        else ""
                    ),
                    " | ".join(
                        details["advertencias"] if details["advertencias"] else ""
                    ),
                    round(details["contribuciones"].get("Salud", 0.0), 3),
                    round(details["contribuciones"].get("Físico", 0.0), 3),
                    round(details["contribuciones"].get("Ambiental", 0.0), 3),
                ]
            )
    except Exception as e:
        content = [
            [_("Classification"), _("Criterion")],
            ["riesgo menor", ""],
            [],
            [_("Totals by category")],
            [_("Physical"), _("Health"), _("Environmental")],
            [0.0, 0.0, 0.0],
        ]
        content.append([])
        content.append([_("Details of the substances")])
        content.append(_("Data not available"))
    report_name = get_report_name(report)
    content.insert(0, [report_name])
    content = sanitize_ods_table(content)
    file = builder.save_ods(content, format_type=report.file_type)
    file_name = f"{report_name}.{report.file_type}"
    file.seek(0)
    doc = ContentFile(file.getvalue(), name=file_name)
    report.file = doc
    report.save()
    return len(content)


def get_pdf_regency_table_content(report):
    """Tablas del PDF de regencia.

    El PDF corre después de ``report_regency_html``, que ya dejó el cálculo en
    ``table_content``: se reutiliza en vez de clasificar el inventario dos
    veces.
    """
    content = report.table_content or {}
    if "summary" not in content:
        report_regency_html(report)
        content = report.table_content
    summary = content["summary"]
    parts = ["<h3>Resumen</h3><table id='pdf_table_report'><thead><tr>"]
    for col in [_("Classification"), _("Criterion")]:
        parts.append("<th>%s</th>" % (col))
    parts.append("</tr></thead><tbody>")
    parts.append(
        "<tr><td>%s</td><td>%s</td></tr></tbody></table>"
        % (summary["classification"], summary["criterion"])
    )
    parts.append(
        "<br><table id='pdf_table_report'><thead><tr><th>%s</th><th>%s</th><th>%s</th></tr></thead><tbody>"
        % (_("Físico"), _("Salud"), _("Ambiental"))
    )
    parts.append(
        "<tr><td>%s</td><td>%s</td><td>%s</td></tr></tbody></table><br>"
        % (summary["physical"], summary["health"], summary["environmental"])
    )
    parts.append(
        "<h3>Detalle de las sustancias</h3><table id='pdf_table_report'><thead><tr>"
    )
    for _name, title in REGENCY_DETAIL_COLUMNS:
        parts.append("<th>%s</th>" % _(title))
    parts.append("</tr></thead><tbody>")
    for row in content["dataset"]:
        parts.append("<tr>")
        parts.extend("<td>%s</td>" % value for value in row)
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)
