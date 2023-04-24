from django.core.files.base import ContentFile
from django.utils.translation import gettext as _

from laboratory.report_utils import ExcelGraphBuilder
from report.utils import set_format_table_columns, get_report_name
from report.utils import get_furniture_queryset_by_filters

def get_dataset(report):
    dataset = []
    furniture_list = get_furniture_queryset_by_filters(report)
    for furniture in furniture_list:
        for shelfobject in furniture.get_objects():
            shelf_unit = shelfobject.get_measurement_unit_display()
            furniture = shelfobject.shelf.furniture
            dataset.append([
                shelfobject.object.code, shelfobject.object.name, f'{shelfobject.quantity} {shelf_unit}',
                shelfobject.in_where_laboratory.name, furniture.labroom.name, furniture.name, shelfobject.shelf.name
            ])
    return dataset

def lab_room_html(report):
    columns_fields = [
        {'name': 'code', 'title': _("Code")}, {'name': 'object', 'title': _("Object")},
        {'name': 'quantity', 'title': _("Quantity")}, {'name': 'laboratory', 'title': _("Laboratory")},
        {'name': 'laboratory_room', 'title': _("Laboratory Room")}, {'name': 'furniture', 'title': _("Furniture")},
        {'name': 'shelf', 'title': _("Shelf")}
    ]
    report.table_content = {
        'columns': set_format_table_columns(columns_fields),
        'dataset': get_dataset(report)
    }
    report.save()


def lab_room_doc(report):
    builder = ExcelGraphBuilder()
    content = [[_("Code"), _("Object"), _("Quantity"), _("Laboratory"), _("Laboratory Room"), _("Furniture"), _("Shelf")]]
    content = content + get_dataset(report)
    report_name = get_report_name(report)
    builder.add_table(content, report_name)
    file=builder.save()
    file_name = f'{report_name}.{report.file_type}'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.save()
    file.close()