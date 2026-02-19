from django.core.files.base import ContentFile
from django.utils.translation import gettext as _
from laboratory.report_utils import ExcelGraphBuilder
from report.utils import get_report_name
from risk_management.utils_risk import (
    cargar_cuadro3,
    cargar_sga_referencia,
    clasificar_establecimiento,
    cargar_umbral_por_H,
    get_inventory,
)


def report_regency_html(report):
    get_pdf_regency_table_content(report)
    return 0


def report_regency_xlsx(report):
    builder = ExcelGraphBuilder()
    builder.ws.title = "Resumen"
    builder.wb.create_sheet("Sumatoria_categoría")
    builder.wb.create_sheet("Detalle")

    content = []
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
    res = clasificar_establecimiento(inv, c3, c4, mapH_tipo)

    builder.ws.append([_("Classification"), _("Criterion")])
    builder.ws.append([str(res["clasificacion"]), str(res["criterio"])])
    builder.style_header()
    builder.autosize_columns()

    sumatoria = res["sumatorias_por_categoria"]

    builder.ws = builder.wb["Sumatoria_categoría"]
    builder.ws.append([_("Physical"), _("Health"), _("Environmental")])
    builder.ws.append(
        [
            sumatoria["Físico"],
            sumatoria["Salud"],
            sumatoria["Ambiental"],
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
                details["cantidad_t"],
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
                " | ".join(details["advertencias"] if details["advertencias"] else ""),
                details["contribuciones"].get("Salud", 0.0),
                details["contribuciones"].get("Físico", 0.0),
                details["contribuciones"].get("Ambiental", 0.0),
            ]
        )
    builder.style_header()
    builder.autosize_columns()
    builder.format_border_cell(len(res["detalles"]), 13)

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
    res = clasificar_establecimiento(inv, c3, c4, mapH_tipo)
    sumatoria = res["sumatorias_por_categoria"]
    content = [
        [_("Classification"), _("Criterion")],
        [str(res["clasificacion"]), str(res["criterio"])],
        [],
        ["Totals by category"],
        [_("Physical"), _("Health"), _("Environmental")],
        [sumatoria["Físico"], sumatoria["Salud"], sumatoria["Ambiental"]],
    ]
    content.append([], ["Details of the substances"])
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
                details["cantidad_t"],
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
                " | ".join(details["advertencias"] if details["advertencias"] else ""),
                details["contribuciones"].get("Salud", 0.0),
                details["contribuciones"].get("Físico", 0.0),
                details["contribuciones"].get("Ambiental", 0.0),
            ]
        )

    report_name = get_report_name(report)
    content.insert(0, [report_name])
    file = builder.save_ods(content, format_type=report.file_type)
    file_name = f"{report_name}.{report.file_type}"
    file.seek(0)
    doc = ContentFile(file.getvalue(), name=file_name)
    report.file = doc
    report.save()
    return len(content)


def get_pdf_regency_table_content(report):
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
    res = clasificar_establecimiento(inv, c3, c4, mapH_tipo)
    sumatoria = res["sumatorias_por_categoria"]
    pdf_table = ""
    pdf_table += "<h3>Resumen</h3><table id='pdf_table_report'><thead><tr>"
    for col in [_("Classification"), _("Criterion")]:
        pdf_table += "<th>%s</th>" % (col)
    pdf_table += "</tr></thead><tbody>"
    pdf_table += "<tr><td>%s</td><td>%s</td></tr></tbody></table>" % (
        res["clasificacion"],
        res["criterio"],
    )
    pdf_table += (
        "<br><table id='pdf_table_report'><thead><tr><th>%s</th><th>%s</th><th>%s</th></tr></thead><tbody>"
        % (_("Físico"), _("Salud"), _("Ambiental"))
    )
    pdf_table += "<tr><td>%s</td><td>%s</td><td>%s</td></tr></tbody></table>" % (
        sumatoria["Físico"],
        sumatoria["Salud"],
        sumatoria["Ambiental"],
    )
    pdf_table += "</tr></thead></table><br>"
    pdf_table += (
        "<h3>Detalle de las sustancias</h3><table id='pdf_table_report'><thead><tr>"
    )
    pdf_table += (
        "<th>%s</th>"
        "<th>%s</th>"
        "<th>%s</th>"
        "<th>%s</th>"
        "<th>%s</th>"
        "<th>%s</th>"
        "<th>%s</th>"
        "<th>%s</th>"
        "<th>%s</th>"
        "<th>%s</th>"
        "<th>%s</th>"
        "<th>%s</th>"
        "<th>%s</th>"
    ) % (
        _("Nombre"),
        _("CAS"),
        _("Cantidad"),
        _("Nominada"),
        _("Umbral"),
        _("Ratio"),
        _("H-codes"),
        _("Regla Cruzada"),
        _("Detalle"),
        _("Advertencias"),
        _("Contribuciones en salud"),
        _("Contribuciones en físico"),
        _("Contribuciones en ambiente"),
    )
    pdf_table += "</tr></thead><tbody>"
    for data in res["detalles"]:
        pdf_table += "<tr>"
        pdf_table += "<td>%s</td>" % (data["nombre"])
        pdf_table += "<td>%s</td>" % (data["cas"])
        pdf_table += "<td>%s</td>" % (data["cantidad_t"])
        pdf_table += "<td>%s</td>" % (_("Yes") if data["nominada_c3"] else _("No"))
        pdf_table += "<td>%s</td>" % (data["umbral_c3"] if data["umbral_c3"] else "")
        pdf_table += "<td>%s</td>" % (data["ratio_c3"] if data["ratio_c3"] else "")
        pdf_table += "<td>%s</td>" % (data["h_codes"])
        pdf_table += "<td>%s</td>" % (
            _("Yes") if data["regla_cruzada_salud"] else _("No")
        )
        pdf_table += "<td>%s</td>" % (
            data["detalle_contribuciones"]
            if data["detalle_contribuciones"]
            else "No hay detalle"
        )
        pdf_table += "<td>%s</td>" % (
            data["advertencias"] if data["advertencias"] else "No hay advertencias"
        )
        pdf_table += "<td>%s</td>" % (data["contribuciones"].get("Salud", 0.0))
        pdf_table += "<td>%s</td>" % (data["contribuciones"].get("Físico", 0.0))
        pdf_table += "<td>%s</td>" % data["contribuciones"].get("Ambiental", 0.0)
        pdf_table += "</tr>"
    pdf_table += "</tbody></table>"

    return pdf_table
