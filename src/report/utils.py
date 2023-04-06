from datetime import datetime


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