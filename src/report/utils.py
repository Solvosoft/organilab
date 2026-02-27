from datetime import datetime, timedelta

from django.db.models import Sum
from django.utils.module_loading import import_string
from django.utils.translation import gettext as _
from djgentelella.models import Notification

from laboratory.models import (
    Furniture,
    BaseUnitValues,
    ObjectLogChange,
    ObjectMaximumLimit,
    OrganizationStructure,
)
from report.models import (
    DocumentReportStatus,
    ObjectChangeLogReport,
    ObjectChangeLogReportBuilder,
)
from sga.models import (
    HCodeCategory,
    DangerSubstance,
    DangerSubstanceCategory,
    DangerIndication,
)


def format_date(value):
    dev = None
    try:
        dev = datetime.strptime(value, "%d/%m/%Y")
    except ValueError as e:
        pass
    return dev


def filter_period(text, queryset):

    dates = text.split("-")
    if len(dates) != 2:
        return queryset
    dates[0] = format_date(dates[0].strip())
    dates[1] = format_date(dates[1].strip())
    return queryset.filter(update_time__range=dates)


def set_format_table_columns(columns_fields):
    columns = []
    type = "string"
    title = ""
    js_column_types = [
        "string",
        "date",
        "datetime",
        "number",
        "select",
        "boolean",
        "integer",
        "null",
        "node",
        "array",
        "function",
        "object",
        "undefined",
    ]

    for field in columns_fields:
        if "name" in field and field["name"]:

            if "type" in field and field["type"] in js_column_types:
                type = field["type"]

            if "title" in field:
                title = field["title"]

            columns.append(
                {"name": field["name"], "title": title, "type": type, "visible": "true"}
            )
    return columns


def get_pdf_table_content(table_content, cell_style_fn=None):
    pdf_table = "<table id='pdf_table_report'><thead>"
    if "columns" and "dataset" in table_content:
        pdf_table += "<tr>"
        table_content["columns"].insert(0, {"title": "Item"})
        for col in table_content["columns"]:
            if "title" in col:
                pdf_table += "<th>%s</th>" % (col["title"])
        pdf_table += "</tr></thead><tbody>"
        i = 1
        for row in table_content["dataset"]:
            row.insert(0, i)
            i += 1
            pdf_table += "<tr>"
            for col_idx, item in enumerate(row):
                style_attr = ""
                if cell_style_fn:
                    style_attr = cell_style_fn(col_idx, item)
                pdf_table += "<td%s>%s</td>" % (style_attr, item)
            pdf_table += "</tr>"
        pdf_table += "</tbody></table>"
    else:
        pdf_table = ""
    return pdf_table


def get_furniture_queryset_by_filters(report):
    furniture, lab_room, lab = [], [], []
    organization = OrganizationStructure.objects.filter(
        pk=report.data["organization"]
    ).first()
    if "laboratory" in report.data:
        lab = (
            report.data["laboratory"]
            if len(report.data["laboratory"]) > 0
            else organization.get_my_laboratories
        )

    if "lab_room" in report.data:
        lab_room = report.data["lab_room"]

    if "furniture" in report.data:
        furniture = report.data["furniture"]

    if furniture:
        furniture_list = Furniture.objects.filter(pk__in=furniture)
    elif lab_room:
        furniture_list = Furniture.objects.filter(labroom__pk__in=lab_room)
    else:
        furniture_list = Furniture.objects.filter(labroom__laboratory__pk__in=lab)

    return furniture_list


def create_notification(user, message, url):
    noti = Notification.objects.create(
        state="visible",
        user=user,
        message_type="info",
        description=message,
        link=url,
    )


def get_report_name(report):
    report_name = _("Report")
    if "name" in report.data and report.data["name"]:
        report_name = report.data["name"]
    elif "title" in report.data and report.data["title"]:
        report_name = report.data["title"]
    elif "report_name" in report.data and report.data["report_name"]:
        report_name = report.data["report_name"]
    return report_name


def document_status(report, description):
    DocumentReportStatus.objects.create(report=report, description=description)


def calc_duration(start_time, end_time):
    duration = end_time - start_time
    duration_in_s = duration.total_seconds()
    minutos = divmod(duration_in_s, 60)[0]
    if divmod(duration_in_s, 60)[0] == 0:
        return duration.total_seconds(), _("seconds")
    return minutos, _("minutes")


def load_dataset_by_column(column_list, data_column):
    obj_item = []
    for name in column_list:
        value = ""
        if name in data_column:
            value = data_column[name]
        obj_item.append(value)
    return obj_item


def check_import_obj(path):
    try:
        import_obj = import_string(path)
    except ImportError:
        import_obj = None

    return import_obj


def get_pdf_log_change_table_content(report):
    table_content = ObjectChangeLogReport.objects.filter(task_report=report)
    pdf_table = ""

    for table in table_content:
        cas = table.object.cas_code if table.object.cas_code else ""
        pdf_table += "<p style='padding:0px; font-size:12px;'>%s</p>" % (
            f"{table.laboratory.name} | {table.object.name} {cas}"
        )
        pdf_table += "<p style='padding:0px; font-size:12px;' >%s</p>" % (
            f" :{table.diff_value} {table.unit.description}"
        )

        pdf_table += "<table id='pdf_table_report'><thead>"
        pdf_table += "<tr>"
        for col in [
            _("User"),
            _("Day"),
            _("Initial amount"),
            _("Final amount"),
            _("Difference"),
        ]:
            pdf_table += "<th>%s</th>" % (col)
        pdf_table += "</tr></thead><tbody>"
        table = ObjectChangeLogReportBuilder.objects.filter(report=table)

        for data in table:
            try:
                user = data.user.get_full_name()
                if not user:
                    user = data.user.username
            except Exception as e:
                user = ""
            pdf_table += "<tr>"
            pdf_table += "<td>%s</td>" % (user)
            pdf_table += "<td>%s</td>" % (
                data.update_time.strftime("%m/%d/%Y, %H:%M:%S")
            )
            pdf_table += "<td>%s</td>" % (data.old_value)
            pdf_table += "<td>%s</td>" % (data.new_value)
            pdf_table += "<td>%s</td>" % (data.diff_value)
            pdf_table += "</tr>"
        pdf_table += "</tbody></table><br><br>"

    return pdf_table


def format_datetime(value, position):
    day_result = None
    try:
        day_result = datetime.strptime(value, "%d/%m/%Y")
        if position == "initial":
            day_result = day_result + timedelta(hours=0, minutes=0)
        else:
            day_result = day_result + timedelta(hours=23, minutes=59)
    except ValueError as e:
        pass

    return day_result


def get_danger_categories(reactive, total=0):
    danger_categories_list = []
    category_h_total = {"environment": 0, "health": 0, "physical": 0}
    code_h = HCodeCategory.objects.filter(
        h_code__isnull=False,
        h_code__pk__in=reactive.sustancecharacteristics.h_code.values_list(
            "pk", flat=True
        ),
    ).distinct()
    for code in code_h:
        codes = set(code.h_code.values_list("pk", flat=True))
        obj_hcodes = set(
            reactive.sustancecharacteristics.h_code.values_list("pk", flat=True)
        )
        intersection = codes.intersection(obj_hcodes)
        if len(intersection) == code.count():
            category_h_total[code.danger_category] += code.threshold * 1000
            danger_categories_list.append(
                [reactive, total, code.danger_category, code.threshold * 1000]
            )
    return danger_categories_list


def get_conversion_units_to_kilograms(unit, amount, density=None):
    query = BaseUnitValues.objects.filter(measurement_unit=unit)
    result = 0
    if query.exists():
        unit = query.first()
        base = unit.measurement_unit
        value = unit.si_value

        if base.description == unit.measurement_unit_base.description:
            result = amount / value
        else:
            result = amount / value

        if unit.measurement_unit_base.description == "Litros":
            result = result * 0.8 if density else result * density
        elif unit.measurement_unit.description == "Libra":
            result = result * 0.4536 if density else result * density
    return result


def get_inventory(objs, units, extra_filters={}):
    dict_objs = []
    for obj in objs:
        total_shelfobjects = 0
        density = getattr(obj.sustancecharacteristics, "density", None)
        data = {}
        for unit in units:
            quantity = (
                ObjectMaximumLimit.objects.filter(
                    object=obj, measurement_unit=unit, **extra_filters
                )
                .distinct()
                .last()
                .quantity
            )
            if quantity > 0:
                total_shelfobjects += get_conversion_units_to_kilograms(
                    unit, quantity, density
                )
        h_codes = [
            h_codes
            for h_code in obj.sustancecharacteristics.h_code.values_list(
                "code", flat=True
            )
        ]
        data = {
            "name": obj.name,
            "cas": obj.cas_code,
            "cantidad_t": total_shelfobjects,
            "h_codes": ";".join(h_codes),
            "condicion_proceso": "",
        }
        dict_objs.append(data)
    return dict_objs


def evaluate_table_tree(data):
    data_list = []
    for obj in data:
        obj["ratio"] = 0.0
        danger_substances = DangerSubstance.objects.filter(cas_code=obj["cas"])
        patron_names = DangerSubstance.objects.filter(type_match="nombre_patron")
        h_categories = DangerSubstance.objects.filter(type_match="h_categoria")
        # Add threshold by cas code
        if danger_substances.exists():
            for danger in danger_substances:
                data = obj.copy()
                data.update(
                    threshold=danger.threshold,
                    especial_condition=danger.especial_condition,
                )
                data_list.append(data)
        else:
            # Add threshold by nombre_patron
            for patron_name in patron_names:
                patrons = [
                    p.strip().lower()
                    for p in patron_name.patron_name.split(";")
                    if p.strip()
                ]
                for patron in patrons:
                    if patron in obj["name"].lower():
                        data = obj.copy()
                        data.update(
                            threshold=patron_name.threshold,
                            especial_condition=patron_name.especial_condition,
                        )
                    data_list.append(data)
            # Add threshold by h_categoria
            for h_category in h_categories.filter(h_codes_match__pk__in=obj["h_codes"]):
                for h_code in h_category.h_codes_match.filter(pk__in=obj["h_codes"]):
                    if h_code in obj["h_codes"]:
                        data = obj.copy()
                        data.update(
                            threshold=h_category.threshold,
                            especial_condition=h_category.especial_condition,
                        )
                        data_list.append(data)

    # evaluate is the substance nominated and extract ratio
    for data in data_list:
        nominate = False
        ratio = 0.0
        if "threshold" in data:
            try:
                nominate = True
                ratio = data["total"] / data["threshold"]
            except ZeroDivisionError:
                ratio = 0.0
        data.update(nominate=nominate, ratio=ratio)

    return data_list


def evaluate_square_quarter(obj):
    data_list = []
    if obj["total"] <= 0:
        return {"supera": False}
    hcodes = obj["h_codes"]
    especial_condition = obj["especial_condition"]
    hcodes_list = DangerSubstanceCategory.objects.filter(
        h_code__pk__in=hcodes
    ).values_list("h_code__pk")
    resuls_rows = []

    if hcodes_list.exists():
        for hcode in set(hcodes_list):
            hcodes = DangerSubstanceCategory.objects.filter(h_code__pk=hcode)
            conditions = hcodes.filter(process_condition__isnull=False)
            if not conditions.exists():
                for candition in conditions:
                    resuls_rows.append(
                        {
                            "h_code": hcode,
                            "process_condition": candition.process_condition,
                            "category": candition.category,
                            "threshold_cat": candition.threshold,
                            "section": candition.section,
                            "notes": candition.note,
                        }
                    )
            elif especial_condition:
                especial_condition_codes = hcodes_list.filter(
                    process_condition=especial_condition
                ).order_by("threshold")
                if especial_condition_codes.exists():
                    especial_condition_code = especial_condition_codes.first()
                    resuls_rows.append(
                        {
                            "h_code": hcode,
                            "process_condition": especial_condition,
                            "category": especial_condition_code.category,
                            "threshold_cat": especial_condition_code.threshold,
                            "section": especial_condition_code.section,
                            "notes": especial_condition_code.note,
                        }
                    )
                else:
                    for condition in especial_condition_codes:
                        resuls_rows.append(
                            {
                                "h_code": hcode,
                                "process_condition": condition.process_condition,
                                "category": condition.category,
                                "threshold_cat": condition.threshold,
                                "section": condition.section,
                                "notes": condition.note,
                            }
                        )

            else:
                hcode_low = hcodes.order_by("threshold").first()
                resuls_rows.append(
                    {
                        "h_code": hcode,
                        "process_condition": hcode_low.process_condition,
                        "category": hcode_low.category,
                        "threshold_cat": hcode_low.threshold,
                        "section": hcode_low.section,
                        "notes": hcode_low.note,
                    }
                )
    else:
        return {"supera": False}

    for row in resuls_rows:
        if row["threshold_cat"] > 0 and obj["total"] >= row["threshold_cat"] * 1000:
            return {
                "supera": True,
                "h_code": row["h_code"],
                "category": row["category"],
                "threshold_cat": row["threshold_cat"],
            }


def substance_contributions(obj):
    quantity = obj["total"]
    hlist = obj["h_codes"]
    details = []
    globals_advert = []
    especial_condition = obj["especial_condition"]
    results = {
        "contribuciones": {},
        "detalle": [],
        "regla_cruzada_salud": False,
        "advertencias": [],
    }

    if hlist and quantity <= 0:
        return results

    if not DangerSubstanceCategory.objects.filter(h_code__pk__in=hlist).exists():
        return results
    filas_resueltas = []
    advertencias = []
    hcodes_list = DangerSubstanceCategory.objects.filter(h_code__pk__in=hlist)
    resuls_rows = []

    if hcodes_list.exists():
        for hcode in hcodes_list.values_list("h_code__pk"):
            hcodes = DangerSubstanceCategory.objects.filter(h_code__pk=hcode)
            conditions = hcodes.filter(process_condition__isnull=False)
            if not conditions.exists():
                for candition in conditions:
                    resuls_rows.append(
                        {
                            "h_code": hcode,
                            "process_condition": candition.process_condition,
                            "category": candition.category,
                            "threshold_cat": candition.threshold,
                            "section": candition.section,
                            "notes": candition.note,
                        }
                    )
            elif especial_condition:
                especial_condition_codes = hcodes_list.filter(
                    process_condition=especial_condition
                ).order_by("threshold")
                if especial_condition_codes.exists():
                    especial_condition_code = especial_condition_codes.first()
                    resuls_rows.append(
                        {
                            "h_code": hcode,
                            "process_condition": especial_condition,
                            "category": especial_condition_code.category,
                            "threshold_cat": especial_condition_code.threshold,
                            "section": especial_condition_code.section,
                            "notes": especial_condition_code.note,
                        }
                    )
                else:
                    for condition in especial_condition_codes:
                        resuls_rows.append(
                            {
                                "h_code": hcode,
                                "process_condition": condition.process_condition,
                                "category": condition.category,
                                "threshold_cat": condition.threshold,
                                "section": condition.section,
                                "notes": condition.note,
                            }
                        )
            else:
                # Sin condición especificada → más conservador + advertencia
                hcode_low = hcodes.order_by("threshold").first()
                resuls_rows.append(
                    {
                        "h_code": hcode,
                        "process_condition": hcode_low.process_condition,
                        "category": hcode_low.category,
                        "threshold_cat": hcode_low.threshold,
                        "section": hcode_low.section,
                        "notes": hcode_low.note,
                    }
                )
                advertencias.append(
                    f"{hcode}: condicion no especificada, "
                    f"usando umbral mas bajo ({hcode_low.threshold}t)"
                )

        # Agrupar por categoría → tomar umbral mínimo por categoría
        contribuciones_directas = {}
        detalles = []

        for category in ["Físico", "Salud", "Ambiental"]:
            cat = hcodes_list.filter(category=category)
            umbral_min = cat.threshold
            if umbral_min > 0:
                contrib = quantity / umbral_min
                contribuciones_directas[category] = contrib
                h_usados = ", ".join(
                    set(cat.h_code.values_list("hcode__code", flat=True))
                )
                notas_usadas = ", ".join(set(cat.notas.values_list("notw", flat=True)))
                detalle_str = f"{category}: {quantity}/{umbral_min} = {contrib:.4f} (H-codes: {h_usados})"
                if notas_usadas:
                    detalle_str += f" [{notas_usadas}]"
                detalles.append(detalle_str)

        if "Salud" not in contribuciones_directas:
            umbral_min_global = hcodes_list.threshold
            h_salud_sga = []
            if umbral_min_global > 0:
                contrib_salud = quantity / umbral_min_global
                contribuciones_directas["Salud"] = contrib_salud
                results["regla_cruzada_salud"] = True
                for h in hlist:
                    danger = DangerIndication.objects.filter(
                        code=h, danger_type="Salud"
                    ).first()
                    if danger:
                        h_salud_sga.append(h.danger_type)
                detalles.append(
                    f"Salud (inclusión C4): {quantity}/{umbral_min_global} = {contrib_salud:.4f} "
                    f"(H-codes SGA salud: {', '.join(h_salud_sga) if h_salud_sga else 'ninguno'})"
                )

        results["contribuciones"] = contribuciones_directas
        results["detalle"] = detalles
        results["advertencias"] = advertencias

    return results
