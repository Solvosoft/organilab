from datetime import datetime, time, timedelta

from django.db.models import Prefetch
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.translation import gettext as _
from djgentelella.models import Notification

from laboratory.models import (
    Furniture,
    OrganizationStructure,
)
from laboratory.utils_base_unit import get_unit_info
from report.models import (
    DocumentReportStatus,
    ObjectChangeLogReport,
    ObjectChangeLogReportBuilder,
)


def format_date(value):
    dev = None
    try:
        dev = datetime.strptime(value, "%d/%m/%Y")
    except ValueError as e:
        pass
    return dev


def period_range(text, input_format="%d/%m/%Y"):
    dates = (text or "").split("-")
    if len(dates) != 2:
        return None
    try:
        start, end = (datetime.strptime(d.strip(), input_format).date() for d in dates)
    except ValueError:
        return None
    return (
        timezone.make_aware(datetime.combine(start, time.min)),
        timezone.make_aware(datetime.combine(end, time.max)),
    )


def report_file_date():
    """Fecha local para el nombre de los archivos de reporte (dd-mm-aaaa)."""
    return timezone.localdate().strftime("%d-%m-%Y")


def local_datetime(value, fmt="%d/%m/%Y %H:%M:%S"):
    if not value:
        return ""
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.strftime(fmt)


def filter_period(text, queryset):
    period = period_range(text)
    if period is None:
        return queryset
    return queryset.filter(update_time__range=period)


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


#: Filas por tabla en el PDF. xhtml2pdf parte una tabla gigante entre páginas
#: con un costo que crece más que lineal; en bloques de este tamaño el tiempo
#: crece en línea recta con las filas.
PDF_TABLE_CHUNK = 100

#: Ancho fijo en el PDF para columnas de texto largo. xhtml2pdf no parte una
#: fila entre páginas: con el ancho automático la columna de indicaciones de
#: peligro quedaba estrecha, una sustancia con muchos códigos H (formaldehído)
#: daba una fila más alta que la página y el PDF entero fallaba con LayoutError.
PDF_COLUMN_WIDTHS = {
    "danger_indication": "35%",
    "substances_a": "18%",
    "substances_b": "18%",
    "laboratory_a": "8%",
    "laboratory_b": "8%",
    "reason": "8%",
}

#: En tablas anchas (más de PDF_WIDE_TABLE columnas, las que van en B4) el
#: reparto automático deja el nombre tan estrecho que los nombres IUPAC
#: ("2,4-Dinitrofenilhidracina") se montan sobre las columnas vecinas.
PDF_WIDE_TABLE = 8
PDF_WIDE_COLUMN_WIDTHS = {"name": "13%", "features": "9%"}


def _pdf_header_cell(col, wide=False):
    width = PDF_COLUMN_WIDTHS.get(col.get("name"))
    if not width and wide:
        width = PDF_WIDE_COLUMN_WIDTHS.get(col.get("name"))
    if width:
        return "<th width='%s'>%s</th>" % (width, col["title"])
    return "<th>%s</th>" % col["title"]


def get_pdf_table_content(table_content, cell_style_fn=None, chunk_size=PDF_TABLE_CHUNK):
    # Se arma en una lista y se une al final: concatenar con `+=` miles de
    # filas copiaba la tabla entera en cada vuelta.
    if not ("columns" in table_content and "dataset" in table_content):
        return ""
    table_content["columns"].insert(0, {"title": "Item"})
    wide = len(table_content["columns"]) > PDF_WIDE_TABLE
    header = "".join(
        _pdf_header_cell(col, wide) for col in table_content["columns"] if "title" in col
    )
    # repeat="1": xhtml2pdf repite el encabezado en cada página.
    opening = "<table id='pdf_table_report' repeat='1'><thead><tr>%s</tr></thead><tbody>" % header
    closing = "</tbody></table>"
    parts = [opening]
    items = table_content.get("items")
    for i, row in enumerate(table_content["dataset"], start=1):
        if i > 1 and (i - 1) % chunk_size == 0:
            parts.append(closing)
            parts.append(opening)
        row.insert(0, items[i - 1] if items else i)
        parts.append("<tr>")
        for col_idx, item in enumerate(row):
            style_attr = cell_style_fn(col_idx, item) if cell_style_fn else ""
            parts.append("<td%s>%s</td>" % (style_attr, "" if item is None else item))
        parts.append("</tr>")
    if not table_content["dataset"]:
        parts.append(
            "<tr><td colspan='%s'>%s</td></tr>" % (len(table_content["columns"]), _("No records."))
        )
    parts.append(closing)
    return "".join(parts)


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
    # Todo precargado (laboratorio, objeto con su ficha, unidad, detalle con su
    # usuario) y armado en una lista: antes eran varias consultas por bloque y
    # una concatenación que copiaba el documento entero en cada fila.
    table_content = (
        ObjectChangeLogReport.objects.filter(task_report=report)
        .select_related("laboratory", "object", "unit")
        .prefetch_related(
            "object__substancharacteristics_object",
            Prefetch(
                "objectchangelogreportbuilder_set",
                queryset=ObjectChangeLogReportBuilder.objects.select_related(
                    "user"
                ).order_by("pk"),
            ),
        )
        .order_by("pk")
    )
    headers = "".join(
        "<th>%s</th>" % col
        for col in [
            _("User"),
            _("Day"),
            _("Initial amount"),
            _("Final amount"),
            _("Difference"),
        ]
    )
    parts = []
    for table in table_content:
        cas = table.object.cas_code if table.object.cas_code else ""
        parts.append(
            "<p style='padding:0px; font-size:12px;'>%s</p>"
            % f"{table.laboratory.name} | {table.object.name} {cas}"
        )
        parts.append(
            "<p style='padding:0px; font-size:12px;' >%s</p>"
            % f"{_('Difference')}: {table.diff_value} {table.unit.description}"
        )
        parts.append(
            "<table id='pdf_table_report' repeat='1'><thead><tr>%s</tr></thead><tbody>"
            % headers
        )
        for data in table.objectchangelogreportbuilder_set.all():
            user = ""
            if data.user is not None:
                user = data.user.get_full_name() or data.user.username
            parts.append(
                "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                % (
                    user,
                    local_datetime(data.update_time),
                    data.old_value,
                    data.new_value,
                    data.diff_value,
                )
            )
        parts.append("</tbody></table><br><br>")

    if not parts:
        parts.append("<p>%s</p>" % _("No changes were recorded with the selected filters."))
    return "".join(parts)


def format_datetime(value, position):
    day = format_date(value)
    if day is None:
        return None
    moment = time.min if position == "initial" else time.max
    return timezone.make_aware(datetime.combine(day.date(), moment))


def get_conversion_units_to_kilograms(unit, amount, density=None):
    # Lee la unidad del mapa compartido (`cached_units`) cuando hay uno: el
    # reporte de regencia convierte una cantidad por sustancia.
    info = get_unit_info(unit)
    result = 0
    if info is not None:
        result = amount / info.si_value

        # La condición estaba invertida: sin densidad multiplicaba por None
        # (TypeError) y con densidad la ignoraba. Para volúmenes se usa la
        # densidad de la sustancia y, si no la hay, 0.8 como aproximación.
        if info.base_description == "Litros":
            result = result * density if density else result * 0.8
        elif info.description == "Libra":
            # Libra -> kilogramo es una masa: la densidad no interviene.
            result = result * 0.4536
    return result
