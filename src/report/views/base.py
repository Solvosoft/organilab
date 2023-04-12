from django.utils.module_loading import import_string

from laboratory.models import TaskReport, Furniture
from report import register


def build_report(pk):
    report = TaskReport.objects.get(pk=pk)

    if report.type_report in register.REPORT_FORMS:
        if report.file_type in register.REPORT_FORMS[report.type_report]:
            import_string(register.REPORT_FORMS[report.type_report][report.file_type])(report)



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