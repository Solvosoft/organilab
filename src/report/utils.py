from datetime import datetime
from django.utils.translation import gettext as _

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