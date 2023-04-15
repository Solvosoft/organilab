from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils.module_loading import import_string
from django.utils.translation import gettext as _
from laboratory.models import TaskReport, Furniture
from report import register
from django.utils import translation, timezone
from weasyprint import HTML
from io import BytesIO

from report.utils import get_pdf_table_content


def build_report(pk, absolute_uri):
    report = TaskReport.objects.get(pk=pk)
    translation.activate(report.language)

    if report.type_report in register.REPORT_FORMS:
        report_obj = register.REPORT_FORMS[report.type_report]
        if report.file_type in register.REPORT_FORMS[report.type_report]:
            if report.file_type == 'pdf' and 'html' in report_obj:
                    f_pdf = report_obj[report.file_type]
                    import_string(report_obj['html'])(report) #GET DATASET AND COLUMNS
                    import_string(f_pdf)(report, absolute_uri) #(ABSOLUTE URL MEDIA REQUIRED)
            else:
                import_string(report_obj[report.file_type])(report)


def base_pdf(report, uri):
    context = {
        'datalist': get_pdf_table_content(report.table_content),
        'user': report.creator,
        'title': report.data['title'],
        'datetime': timezone.now(),
        'size_sheet': 'landscape'
    }

    html = render_to_string('report/base_report_pdf.html', context=context)
    file = BytesIO()
    HTML(string=html, base_url=uri, encoding='utf-8').write_pdf(file)
    file_name = f'{report.data["name"]}.pdf'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.save()
    file.close()


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