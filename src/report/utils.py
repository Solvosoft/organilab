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

def update_table_report(report, col_list, rows):
    columns = '<thead><tr>'
    for col in col_list:
        columns += f'<th>{col}</th>'
    columns += '</tr></thead>'
    table = columns + '<tbody>' + rows +'</tbody>'
    report.table_content = table
    report.status = _('Generated')
    report.save()