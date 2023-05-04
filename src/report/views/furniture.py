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
            obj_type = shelfobject.object.get_type_display()
            furniture = shelfobject.shelf.furniture
            dataset.append([
                shelfobject.object.code, shelfobject.object.name, obj_type, f'{shelfobject.quantity} {shelf_unit}',
                shelfobject.in_where_laboratory.name, furniture.labroom.name, furniture.name, shelfobject.shelf.name
            ])
    return dataset


def furniture_html(report):
    columns_fields = [
        {'name': 'code', 'title': _("Code")}, {'name': 'object', 'title': _("Object")},
        {'name': 'type', 'title': _("Type")}, {'name': 'quantity', 'title': _("Quantity")},
        {'name': 'laboratory', 'title': _("Laboratory")}, {'name': 'laboratory_room', 'title': _("Laboratory Room")},
        {'name': 'furniture', 'title': _("Furniture")}, {'name': 'shelf', 'title': _("Shelf")}
    ]
    report.table_content = {
        'columns': set_format_table_columns(columns_fields),
        'dataset': get_dataset(report)
    }
    report.save()
    return len(report.table_content['dataset'])

def furniture_doc(report):
    builder = ExcelGraphBuilder()
    content = [[_("Code"), _("Object"), _("Type"), _("Quantity"), _("Laboratory"), _("Laboratory Room"), _("Furniture"), _("Shelf")]]
    content = content + get_dataset(report)
    record_total=len(content)-1

    report_name = get_report_name(report)
    file=None
    if report.file_type != 'ods':
        builder.add_table(content, report_name)
        file = builder.save()
    else:
        content.insert(0, [report_name])
        file = builder.save_ods(content)
    file_name = f'{report_name}.{report.file_type}'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.save()
    file.close()
    return record_total
