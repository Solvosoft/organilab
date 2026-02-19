import json

from django.core.files.base import ContentFile
from django.db.models import Sum
from django.utils.translation import gettext as _
from laboratory.models import (
    ShelfObject,
    Object,
    Catalog,
    ObjectLogChange,
    OrganizationStructure,
)
from laboratory.report_utils import ExcelGraphBuilder
from laboratory.utils_base_unit import get_conversion_units
from report.models import RegencyReportBuilder, RegencyReport
from report.utils import (
    filter_period,
    set_format_table_columns,
    get_report_name,
    load_dataset_by_column,
    get_danger_categories,
    get_conversion_units_to_kilograms,
    evaluate_table_tree,
    evaluate_square_quarter,
    substance_contributions,
)
from risk_management.models import RiskZone
from risk_management.utils_risk import (
    cargar_cuadro3,
    cargar_sga_referencia,
    clasificar_establecimiento,
    cargar_umbral_por_H,
    get_inventory,
)


def get_dataset_report(report, column_list=None):
    dataset = []
    filters = {"object__type": 0}
    logs = ObjectLogChange.objects.filter(
        organization_where_action_taken__pk=report.data["organization"],
        update_time__year=report.data["years"],
        laboratory__pk__in=report.data["laboratory"],
    )
    objs = Object.objects.filter(
        pk__in=logs.values_list("object__pk", flat=True),
        sustancecharacteristics__isnull=False,
    ).distinct()
    units = Catalog.objects.filter(
        pk__in=logs.values_list("measurement_unit", flat=True)
    )
    fourth_list = []
    organization = OrganizationStructure.objects.filter(
        pk=report.data["organization"]
    ).first()
    data = {
        "organization": organization,
        "year": report.data["years"],
        "task_report": report,
    }

    report_regency = RegencyReport.objects.create(**data)
    objs = get_inventory(filters)
    inv_c3 = evaluate_table_tree(objs)

    exists_ratio = any(x["ratio"] >= 1.0 for x in inv_c3)
    if exists_ratio:
        details = []
        for r in inv_c3:
            details.append(
                {
                    "nombre": r["name"],
                    "cas": r["cas"],
                    "total": float(r["total"]),
                    "nominate": bool(r["nominate"]),
                    "threshold_c3": (
                        None if r["threshold"] == 0.0 else float(r["threshold"])
                    ),
                    "ratio": (None if r["ratio"] == 0.0 else float(r["ratio"])),
                    "h_codes": r["h_codes"],
                    "contribuciones": {},
                    "detalle_contribuciones": [],
                    "regla_cruzada_salud": False,
                }
            )
            return {
                "clasificacion": "riesgo mayor",
                "criterio": "Al menos una sustancia nominada (Cuadro 3) cumple o supera su umbral.",
                "sumatorias_por_categoria": {},
                "detalles": details,
                "trazabilidad": {},
            }
    for obj in inv_c3:
        results = evaluate_square_quarter(obj)
        if results["supera"]:
            details = []
            for r in inv_c3:
                details.append(
                    {
                        "name": r["name"],
                        "cas": r["cas"],
                        "total": float(r["total"]),
                        "nominate": bool(r["nominate"]),
                        "threshold_c3": (
                            None if r["threshold"] == 0.0 else float(r["threshold"])
                        ),
                        "ratio_c3": (
                            None if r["ratio_c3"] == 0.0 else float(r["ratio_c3"])
                        ),
                        "h_codes": r["h_codes"],
                        "contribuciones": {},
                        "detalle_contribuciones": [],
                        "regla_cruzada_salud": False,
                        "paso4_supera": (
                            r["nombre"] == obj["nombre"] and r["cas"] == obj["cas"]
                        ),
                    }
                )

            return {
                "clasificacion": "riesgo mayor",
                "criterio": (
                    f"Sustancia '{obj['name']}' supera umbral individual del Cuadro 4 "
                    f"({results['h_code']}: {obj['total']}t >= {results['threshold_cat']}t)."
                ),
                "sumatorias_por_categoria": {},
                "detalles": details,
                "trazabilidad": {},
            }
    # Paso 5: sumatoria por categoría usando Cuadro 4
    sum_per_category = {"Físico": 0.0, "Salud": 0.0, "Ambiental": 0.0}
    details = []

    advertencias_globales = []

    for obj in inv_c3:
        res_sust = substance_contributions(obj)

        for cat, val in res_sust["contribuciones"].items():
            if cat in sum_per_category:
                sum_per_category[cat] += val

        # Propagar advertencias con nombre de sustancia
        for adv in res_sust.get("advertencias", []):
            advertencias_globales.append(f"{obj['nombre']}: {adv}")

        details.append(
            {
                "nombre": obj["nombre"],
                "cas": obj["cas"],
                "cantidad_t": float(obj["total"]),
                "nominada_c3": bool(obj["nominate"]),
                "umbral_c3": (
                    None if obj["threshold_cat"] else float(obj["threshold_cat"])
                ),
                "ratio_c3": None if obj["ratio"] else float(obj["ratio"]),
                "h_codes": obj["h_codes"],
                "contribuciones": res_sust["contribuciones"],
                "detalle_contribuciones": res_sust["detalle"],
                "regla_cruzada_salud": res_sust["regla_cruzada_salud"],
                "advertencias": res_sust.get("advertencias", []),
            }
        )
    # Redondear sumatorias
    for cat in sum_per_category:
        sum_per_category[cat] = round(sum_per_category[cat], 4)

    criterio = "Sumatoria por categorías SGA (Cuadro 4) "
    if any(v >= 1.0 for v in sum_per_category.values()):
        clasif = "riesgo mayor"
        criterio += "≥ 1 en al menos una categoría."
    else:
        clasif = "riesgo menor"
        criterio += "< 1 en todas las categorías."

    x = {
        "clasificacion": clasif,
        "criterio": criterio,
        "sumatorias_por_categoria": sum_per_category,
        "detalles": details,
        "advertencias": advertencias_globales,
        "trazabilidad": {},
    }

    return x


def get_dataset_report_x(report, column_list=None):
    dataset = []
    filters = {"object__type": 0}
    logs = ObjectLogChange.objects.filter(
        organization_where_action_taken__pk=report.data["organization"],
        update_time__year=report.data["years"],
        laboratory__pk__in=report.data["laboratory"],
    )
    objs = Object.objects.filter(
        pk__in=logs.values_list("object__pk", flat=True),
        is_dangerous=True,
    ).distinct()
    units = Catalog.objects.filter(
        pk__in=logs.values_list("measurement_unit", flat=True)
    )
    third_list = []
    fourth_list = []
    organization = OrganizationStructure.objects.filter(
        pk=report.data["organization"]
    ).first()
    data = {
        "organization": organization,
        "year": report.data["years"],
        "task_report": report,
    }

    report_regency = RegencyReport.objects.create(**data)
    reactive_list = []
    for reactive in objs:
        third_square = False
        total_shelfobjects = 0
        density = getattr(reactive.sustancecharacteristics, "density", None)

        for unit in units:
            quantity = (
                logs.filter(object=reactive, measurement_unit=unit)
                .distinct()
                .aggregate(Sum("diff_value", default=0))["diff_value__sum"]
            )
            if quantity > 0:
                total_shelfobjects += get_conversion_units_to_kilograms(
                    unit, quantity, density
                )  # list 3

        reactive_list.append(
            RegencyReportBuilder(
                report=report_regency,
                substance=reactive,
                danger_category=3,
                total=total_shelfobjects,
                break_threshold=(reactive.threshold * 1000) < total_shelfobjects,
            )
        )

        if not third_square and hasattr(reactive, "sustancecharacteristics"):
            # list 4
            danger_categories_list = get_danger_categories(
                reactive,
                total_shelfobjects,
            )
            if len(danger_categories_list) > 0:
                if danger_categories_list[-1].threshold * 1000 < total_shelfobjects:
                    danger_categories_list.append(_("Yes Exceeds Threshold"))
                else:
                    danger_categories_list.append(_("No Exceeds Threshold"))
                fourth_list.extend(danger_categories_list)

    total_fifth_list = {
        "enviroment": {"substance": 0, "category_threshold": 0, "total": 0},
        "health": {"substance": 0, "category_threshold": 0, "total": 0},
        "physical": {"substance": 0, "category_threshold": 0, "total": 0},
    }
    if len(fourth_list) > 0:
        for danger in fourth_list:
            total_fifth_list[danger[2]]["substance"] += danger[3]
            total_fifth_list[danger[2]]["category_threshold"] += danger[4]
            try:
                total_fifth_list[danger[2]]["total"] += danger[3] / danger[4]
            except ZeroDivisionError:
                total_fifth_list[danger[2]]["total"] = 0

            reactive_list.append(
                RegencyReportBuilder(
                    report=report_regency,
                    substance=reactive,
                    danger_category=4,
                    total=total_fifth_list[danger[2]]["total"],
                )
            )

        for danger in total_fifth_list:
            total_fifth_list[danger]["category_threshold"] /= 1000

    totals = 0
    if reactive_list:
        RegencyReportBuilder.objects.bulk_create(reactive_list)
        totals = len(reactive_list)

    return totals


def get_dataset_report_doc(report, column_list=None):
    dataset = []
    filters = {"object__type": 0}
    logs = ObjectLogChange.objects.filter(
        organization_where_action_taken__pk=report.data["organization"],
        update_time__year=report.data["years"],
        laboratory__pk__in=report.data["laboratory"],
    )

    objs = Object.objects.filter(
        pk__in=logs.values_list("object__pk", flat=True),
        has_threshold=True,
        is_dangerous=True,
        threshold__isnull=False,
    ).distinct()
    units = Catalog.objects.filter(
        pk__in=logs.values_list("measurement_unit", flat=True)
    )
    third_list = []
    fourth_list = []
    organization = OrganizationStructure.objects.filter(
        pk=report.data["organization"]
    ).first()
    data = {
        "organization": organization,
        "year": report.data["years"],
        "task_report": report,
    }
    report_regency = RegencyReport.objects.create(**data)
    reactive_list = []
    for reactive in objs:
        third_square = False
        total_shelfobjects = 0
        density = getattr(reactive.sustancecharacteristics, "density", None)

        for unit in units:
            quantity = (
                logs.filter(object=reactive, measurement_unit=unit)
                .distinct()
                .aggregate(Sum("diff_value", default=0))["diff_value__sum"]
            )
            if quantity > 0:
                total_shelfobjects += get_conversion_units_to_kilograms(
                    unit, quantity, density
                )  # list 3
        if_break_threshold = reactive.threshold * 1000 < total_shelfobjects
        third_list.append(
            [
                reactive.name,
                total_shelfobjects,
                _("Yes") if if_break_threshold else _("No"),
            ]
        )

        if not if_break_threshold and hasattr(reactive, "sustancecharacteristics"):
            # list 4
            danger_categories_list = get_danger_categories(
                reactive,
                total_shelfobjects,
            )
            if len(danger_categories_list) > 0:
                fourth_list.append(danger_categories_list)

    total_fifth_list = {
        "enviroment": {"substance": 0, "category_threshold": 0, "total": 0},
        "health": {"substance": 0, "category_threshold": 0, "total": 0},
        "physical": {"substance": 0, "category_threshold": 0, "total": 0},
    }
    if len(fourth_list) > 0:
        i = 0
        for danger in fourth_list:
            total_fifth_list[danger[2]]["substance"] += danger[3]
            total_fifth_list[danger[2]]["category_threshold"] += danger[4]
            try:
                total_fifth_list[danger[2]]["total"] += danger[3] / danger[4]
            except ZeroDivisionError:
                total_fifth_list[danger[2]]["total"] = 0
            fourth_list[i][-1] = (
                _("Yes") if fourth_list[i][-1] < fourth_list[i][1] else _("No")
            )
            i += 1
        for danger in total_fifth_list:
            total_fifth_list[danger]["category_threshold"] /= 1000

    totals = len(third_list) + len(fourth_list) - 2

    return totals, third_list, fourth_list


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
