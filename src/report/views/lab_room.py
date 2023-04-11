from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from io import BytesIO
from django.utils.translation import gettext as _
from weasyprint import HTML

from laboratory.models import Laboratory, Furniture
from report.utils import update_table_report
from report.views.base import get_furniture_queryset_by_filters


def lab_room_html(report):
    furniture_list = get_furniture_queryset_by_filters(report)
    rows = ""
    col_list = [_("Code"), _("Object"), _("Quantity"), _("Laboratory"), _("Laboratory Room"), _("Furniture"), _("Shelf")]
    for furniture in furniture_list:
        for shelfobject in furniture.get_objects():
            shelf_unit = shelfobject.get_measurement_unit_display()
            furniture = shelfobject.shelf.furniture
            rows += f'<tr><td>{shelfobject.object.code}</td><td>{shelfobject.object.name}</td>' \
                     f'<td>{shelfobject.quantity} {shelf_unit}</td><td>{shelfobject.in_where_laboratory.name}</td>' \
                     f'<td>{furniture.labroom.name}</td><td>{furniture.name}</td><td>{shelfobject.shelf.name}</td></tr>'
    update_table_report(report, col_list, rows)

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
    report.save()
    file.close()
