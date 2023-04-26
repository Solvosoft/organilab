from datetime import datetime
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

    for field in columns_fields:
        if 'type' in field:
            type = field['type']

        columns.append({
            'name': field['name'],
            'title': field['title'],
            'type': type,
            'visible': 'true'
        })

    return columns


def get_pdf_table_content(table_content):
    pdf_table = "<thead>"
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
        "</tbody>"
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

def save_request_data(form, data):
    general_report_fields = ['laboratory', 'lab_room', 'furniture', 'users']

    for field in general_report_fields:
        if field in form.fields:
            data[field] = form.cleaned_data[field]


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