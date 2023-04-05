from django.core.files.base import ContentFile
from django.db.models import Sum
from django.template.loader import render_to_string
from io import BytesIO
from django.utils.translation import gettext as _
from weasyprint import HTML

from laboratory.models import Object, ObjectLogChange, ShelfObject, Laboratory
from datetime import datetime

from laboratory.report_utils import ExcelGraphBuilder
from laboratory.utils import get_user_laboratories
from laboratory.views.djgeneric import ResultQueryElement


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


def resume_queryset(queryset):
    objects = set(queryset.values_list('object', flat=True))
    list_obj = []
    user=""
    for obj in objects:
        obj_check = Object.objects.filter(pk=obj)
        if obj_check.exists():
            ini = queryset.filter(object=obj).values('old_value')[0]['old_value']
            end = queryset.filter(object=obj).last()
            diff = queryset.filter(object=obj).aggregate(balance=Sum('diff_value'))['balance']
            try:
                user = end.user.get_full_name()
            except Exception as e:
                user = ""

            list_obj.append(ResultQueryElement({'user': user,
                                                'laboratory': end.laboratory,
                                                'object': end.object,
                                                'update_time': end.update_time,
                                                'old_value': ini,
                                                'new_value': end.new_value,
                                                'diff_value': diff,
                                                'measurement_unit': end.measurement_unit
                                                })
                            )
    return list_obj


def get_queryset(report):
    query = ObjectLogChange.objects.all().order_by('update_time')
    if 'period' in report.data:
        query = filter_period(report.data['period'], query)
    if 'precursor' in report.data:
        query = query.filter(precursor=True)
    if 'all_labs_org' in report.data:
        query = query.filter(laboratory__in=get_user_laboratories(report.creator))
    else:
        query = query.filter(laboratory__pk=report.data['lab_pk'])
    if 'resume' in report.data:
        query = query
    return query



def report_objectlogchange_html(report):
    queryset = get_queryset(report)
    object_list=resume_queryset(queryset)

    table =f'<thead><tr><th>{_("User")}</th><th>{_("Laboratory")}</th>' \
           f'<th>{_("Object")}</th><th>{_("Day")}</th><th>{_("Old")}</th>' \
           f'<th>{_("New")}</th><th>{_("Difference")}</th>'\
           f'<th>{_("Unit")}</th></tr></thead>'

    table+="<tbody>"
    for obj in object_list:

        table+=f'<tr><td>{obj.user}</td><td>{str(obj.laboratory)}</td>' \
               f'<td>{str(obj.object)}</td><td>{obj.update_time.strftime("%m/%d/%Y, %H:%M:%S")}</td>' \
               f'<td>{obj.old_value}</td><td>{obj.new_value}</td>' \
               f'<td>{obj.diff_value}</td><td>{str(obj.measurement_unit)}</td></tr>'
    table+='</tbody>'
    report.table_content = table
    report.status = _('Generated')
    report.save()

def report_objectlogchange_pdf(report):

    report_objectlogchange_html(report)
    context = {
        'datalist': report.table_content,
        'laboratory': report.data['lab_pk'],
        'user': report.creator,
    }

    html = render_to_string('report/base_report_pdf.html', context=context)
    file = BytesIO()

    HTML(string=html, encoding='utf-8').write_pdf(file)

    file_name = f'{report.data["name"]}.pdf'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.status = _('Generated')
    report.save()
    file.close()

def report_objectlogchange_doc(report):
    queryset = get_queryset(report)
    object_list=resume_queryset(queryset)
    content = []
    builder = ExcelGraphBuilder()
    content.append([
        _("User"), _("Laboratory"), _("Object"), _("Day"), _('Old'),
        _('New'),_("Difference"),_("Unit")
    ])


    for obj in object_list:
        content.append([obj.user,
                        str(obj.laboratory),
                        str(obj.object),
                        obj.update_time.strftime("%m/%d/%Y, %H:%M:%S"),
                        obj.old_value,
                        obj.new_value,
                        obj.diff_value,
                        str(obj.measurement_unit)
                        ])

    builder.add_table(content, report.data['title'])
    file=builder.save()
    report_name = report.data['name'] if report.data['name'] else 'report'
    file_name = f'{report_name}.{report.file_type}'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.status = _('Generated')
    report.save()
    file.close()
