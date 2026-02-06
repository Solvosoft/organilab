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
)
from risk_management.models import RiskZone


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
    get_dataset_report(report)
    record = RegencyReportBuilder.objects.filter(report__task_report=report).count()
    return record


def report_regency_doc(report):
    builder = ExcelGraphBuilder()
    totals, third_list, fourth_list = get_dataset_report_doc(report)
    content = []
    regency = RegencyReport.objects.filter(task_report=report).first()
    break_threshold = if_break(third_list, 2)
    if (
        regency.break_physical_total
        or regency.break_enviroment_total
        or regency.break_health_total
    ):
        content.append([_("High-risk establishment")])

    content.append([_("Dangerous substance of the list 3")])
    if third_list:

        content.append([_("Danger substance"), _("Total"), _("Break threshold")])
        content.extend(third_list)
    else:
        content.append([_("No data")])
    content.append([])
    if not break_threshold:
        break_threshold = if_break(fourth_list, 3)
        content.append([_("Dangerous substance of the list 4")])
        if fourth_list:
            content.append(
                [
                    _("Danger substance"),
                    _("Total"),
                    _("Danger category"),
                    _("Break threshold"),
                ]
            )
            content.extend(fourth_list)
        else:
            content.append([_("No data")])
    content.append([])
    if not break_threshold:
        content.append("Sum of dangers categories")
        content.append([_("Health totals:"), regency.health_total])
        content.append([_("Physical totals:"), regency.physical_total])
        content.append([_("Environmental totals:"), regency.enviroment_total])

    report_name = get_report_name(report)
    content.insert(0, [report_name])
    file = builder.save_ods(content, format_type=report.file_type)
    file_name = f"{report_name}.{report.file_type}"
    file.seek(0)
    doc = ContentFile(file.getvalue(), name=file_name)
    report.file = doc
    report.save()
    return totals


def if_break(datalist, col=2):
    for i, row in enumerate(datalist):
        if row[col] == "Si":
            return True
    return False


def get_pdf_regency_table_content(report):
    table_content = RegencyReportBuilder.objects.filter(report__task_report=report)
    pdf_table = ""
    regency = RegencyReport.objects.filter(task_report=report).first()
    third_list = table_content.filter(danger_list=3, break_threshold=True).exists()
    quarter_list = table_content.filter(danger_list=4, break_threshold=True).exists()
    if (
        third_list
        or quarter_list
        or regency.break_health_total
        or regency.break_enviroment_total
        or regency.break_physical_total
    ):
        pdf_table += "<h3>%s</h3>" % (_("High-risk establishment"))
    pdf_table += "<table id='pdf_table_report'><thead>"
    pdf_table += "<tr>"
    for col in [
        _("Dangerous substance of the list 3"),
        _("Total"),
        _("Break threshold"),
    ]:
        pdf_table += "<th>%s</th>" % (col)
    pdf_table += "</tr></thead><tbody>"
    for data in table_content.filter(danger_list=3):
        pdf_table += "<tr>"
        pdf_table += "<td>%s</td>" % (data.substance.name)
        pdf_table += "<td>%s</td>" % (data.total)
        pdf_table += "<td>%s</td>" % (_("Yes") if data.break_threshold else _("No"))
        pdf_table += "</tr>"

        pdf_table += "</tbody></table><br><br>"
    if not third_list:
        pdf_table += "<table id='pdf_table_report'><thead>"
        pdf_table += "<tr>"
        for col in [
            _("Dangerous substance of the list 4"),
            _("Total"),
            _("Break threshold"),
            _("Danger category"),
        ]:
            pdf_table += "<th>%s</th>" % (col)
        pdf_table += "</tr></thead><tbody>"
        for data in table_content.filter(danger_list=4):
            pdf_table += "<tr>"
            pdf_table += "<td>%s</td>" % (data.substance.name)
            pdf_table += "<td>%s</td>" % (data.total)
            pdf_table += "<td>%s</td>" % (_("Yes") if data.break_threshold else _("No"))
            pdf_table += "<td>%s</td>" % (data.danger_category)
            pdf_table += "</tr>"
        pdf_table += "</tbody></table><br><br>"
    if not quarter_list:
        pdf_table += "<p>%s</p>" % (_("Sum of dangers categories"))
        pdf_table += "<br>"
        pdf_table += "<p>%s %s</p>" % (_("Health totals:"), regency.health_total)
        pdf_table += "<p>%s %s</p>" % (_("Physical totals:"), regency.physical_total)
        pdf_table += "<p>%s %s</p>" % (
            _("Environmental totals:"),
            regency.enviroment_total,
        )
    return pdf_table
