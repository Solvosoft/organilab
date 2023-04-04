from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from io import BytesIO
from django.utils.translation import gettext as _
from weasyprint import HTML

from laboratory.models import Laboratory, Furniture


def lab_room_html(report):
    lab = report.data['laboratory']
    lab_room = report.data['lab_room']

    if not lab_room:
        furniture_list = Furniture.objects.filter(labroom__laboratory__pk__in=lab)
    else:
        furniture_list = Furniture.objects.filter(labroom__pk__in=lab_room)

    table = f'<thead><tr><th>{_("Code")}</th><th>{_("Object")}</th><th>{_("Quantity")}</th>' \
            f'<th>{_("Shelf")}</th></tr></thead>'
    table+='<tbody>'
    for furniture in furniture_list:
        for shelfobject in furniture.get_objects():
            table += f'<tr><td>{shelfobject.object.code}</td><td>{shelfobject.object.name}</td>' \
                     f'<td>{shelfobject.quantity} {shelfobject.get_measurement_unit_display()}</td><td>{shelfobject.shelf.name}</td></tr>'
    table+='</tbody>'
    report.table_content = table
    report.status = _('Generated')
    report.save()

def lab_room_pdf(report):

    lab_room_html(report)
    context = {
        'datalist': report.table_content,
        'laboratory': report.data['laboratory'],
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
