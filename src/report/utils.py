from datetime import datetime
from django.utils.translation import gettext as _

from laboratory.models import Furniture


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


def save_request_data(form, data):
    general_report_fields = ['laboratory', 'lab_room', 'furniture', 'users']

    for field in general_report_fields:
        if field in form.fields:
            data[field] = form.cleaned_data[field]