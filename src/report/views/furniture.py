from django.core.files.base import ContentFile
from django.utils.translation import gettext as _

from laboratory.report_utils import ExcelGraphBuilder
from report.utils import update_table_report
from report.views.base import get_furniture_queryset_by_filters


def furniture_html(report):
    furniture_list = get_furniture_queryset_by_filters(report)
    rows = ""
    col_list = [_("Code"), _("Object"), _("Type"), _("Quantity"), _("Laboratory"), _("Laboratory Room"), _("Furniture"), _("Shelf")]
    for furniture in furniture_list:
        for shelfobject in furniture.get_objects():
            shelf_unit = shelfobject.get_measurement_unit_display()
            obj_type = shelfobject.object.get_type_display()
            furniture = shelfobject.shelf.furniture
            rows += f'<tr><td>{shelfobject.object.code}</td><td>{shelfobject.object.name}</td><td>{obj_type}</td>' \
                     f'<td>{shelfobject.quantity} {shelf_unit}</td><td>{shelfobject.in_where_laboratory.name}</td>' \
                     f'<td>{furniture.labroom.name}</td><td>{furniture.name}</td><td>{shelfobject.shelf.name}</td></tr>'
    update_table_report(report, col_list, rows)


def furniture_doc(report):
    furniture_list = get_furniture_queryset_by_filters(report)
    content = []
    builder = ExcelGraphBuilder()
    content.append([_("Code"), _("Object"), _("Type"), _("Quantity"), _("Laboratory"), _("Laboratory Room"), _("Furniture"), _("Shelf")])

    for furniture in furniture_list:
        for shelfobject in furniture.get_objects():
            shelf_unit = shelfobject.get_measurement_unit_display()
            obj_type = shelfobject.object.get_type_display()
            furniture = shelfobject.shelf.furniture
            content.append([
                shelfobject.object.code,
                shelfobject.object.name,
                obj_type,
                f'{shelfobject.quantity} {shelf_unit}',
                shelfobject.in_where_laboratory.name,
                furniture.labroom.name,
                furniture.name,
                shelfobject.shelf.name
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