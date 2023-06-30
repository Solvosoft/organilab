from datetime import datetime

from django.utils.module_loading import import_string
from django.utils.translation import gettext as _
from djgentelella.models import Notification

from laboratory.models import Furniture
from report.models import DocumentReportStatus


def format_date(value):
    dev = None
    try:
        dev = datetime.strptime(value, '%d/%m/%Y')
    except ValueError as e:
        pass
    return dev


def filter_period(text, queryset):

    dates = text.split('-')
    if len(dates) != 2:
        return queryset
    dates[0] = format_date(dates[0].strip())
    dates[1] = format_date(dates[1].strip())
    return queryset.filter(update_time__range=dates)


def set_format_table_columns(columns_fields):
    columns = []
    type = 'string'
    title = ''
    js_column_types = ['string', 'date', 'datetime', 'number', 'select', 'boolean', 'integer',
                    'null', 'node', 'array', 'function', 'object', 'undefined']

    for field in columns_fields:
        if 'name' in field and field['name']:

            if 'type' in field and field['type'] in js_column_types:
                type = field['type']

            if 'title' in field:
                title = field['title']

            columns.append({
                'name': field['name'],
                'title': title,
                'type': type,
                'visible': 'true'
            })
    return columns


def get_pdf_table_content(table_content):
    pdf_table = "<table id='pdf_table_report'><thead>"
    if 'columns' and 'dataset' in table_content:
        pdf_table += '<tr>'
        for col in table_content['columns']:
            if 'title' in col:
                pdf_table += "<th>%s</th>" % (col['title'])
        pdf_table += '</tr></thead><tbody>'

        for row in table_content['dataset']:
            pdf_table += '<tr>'
            for item in row:
                pdf_table += '<td>%s</td>' % (item)
            pdf_table += '</tr>'
        "</tbody></table>"
    else:
        pdf_table = ""
    return pdf_table


def get_furniture_queryset_by_filters(report):
    furniture, lab_room, lab = [], [], []
    if 'laboratory' in report.data:
        lab = report.data['laboratory']

    if 'lab_room' in report.data:
        lab_room = report.data['lab_room']

    if 'furniture' in report.data:
        furniture = report.data['furniture']

    if furniture:
        furniture_list = Furniture.objects.filter(pk__in=furniture)
    elif lab_room:
        furniture_list = Furniture.objects.filter(labroom__pk__in=lab_room)
    else:
        furniture_list = Furniture.objects.filter(labroom__laboratory__pk__in=lab)

    return furniture_list

def create_notification(user, message,url):
    noti = Notification.objects.create(
        state='visible',
        user=user,
        message_type="info",
        description=message,
        link=url,
    )


def get_report_name(report):
    report_name = _('Report')
    if 'name' in report.data and report.data['name']:
        report_name = report.data['name']
    elif 'title' in report.data and report.data['title']:
        report_name = report.data['title']
    elif 'report_name' in report.data and report.data['report_name']:
        report_name = report.data['report_name']
    return report_name


def document_status(report,description):
    DocumentReportStatus.objects.create(
        report=report,
        description=description
    )

def calc_duration(start_time, end_time):
    duration = end_time - start_time
    duration_in_s = duration.total_seconds()
    minutos=divmod(duration_in_s, 60)[0]
    if divmod(duration_in_s, 60)[0] == 0:
        return duration.total_seconds(), _('seconds')
    return minutos, _('minutes')


def load_dataset_by_column(column_list, data_column):
    obj_item = []
    for name in column_list:
        value = ''
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

def get_pdf_log_change_table_content(table_content):
    pdf_table=""
    for table in table_content['dataset']:
        pdf_table+= "<p>%s</p>" %(f'{table["lab"]} {table["obj"]} {table["diff"]}')
        pdf_table += "<table id='pdf_table_report'><thead>"
        pdf_table += '<tr>'
        for col in [_("User"), _("Day"), _('Old'), _('New'), _("Difference"), _("Unit")]:
            pdf_table += "<th>%s</th>" % (col)
        pdf_table += '</tr></thead><tbody>'

        for row in table['values']:
            pdf_table += '<tr>'
            for item in row:
                pdf_table += '<td>%s</td>' % (row[item])
            pdf_table += '</tr>'
        pdf_table+="</tbody></table><br><br>"

    return pdf_table
