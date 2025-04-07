from django.core.files.base import ContentFile
from django.utils.translation import gettext as _

from laboratory.models import Object
from laboratory.report_utils import ExcelGraphBuilder
from report.utils import set_format_table_columns, get_report_name, load_dataset_by_column
from report.utils import get_furniture_queryset_by_filters

def get_dataset(report, column_list=None):
    dataset = []
    furniture_list = get_furniture_queryset_by_filters(report)
    attrs = {}
    if "object_type" in report.data:
        attrs['object__type'] = report.data["object_type"]
        if "is_precursor" in report.data and report.data["object_type"] == '0':
            attrs['object__sustancecharacteristics__is_precursor'] = (
                report.data)["is_precursor"]
    for furniture in furniture_list:
        objects = furniture.get_objects().filter(**attrs)
        for shelfobject in objects:
            shelf_unit = shelfobject.get_measurement_unit_display()
            furniture = shelfobject.shelf.furniture
            data_column = {
                'code': shelfobject.object.code,
                'object': shelfobject.object.name,
                'quantity': f'{shelfobject.quantity} {shelf_unit}',
                'laboratory': shelfobject.in_where_laboratory.name,
                'laboratory_room': furniture.labroom.name,
                'furniture': furniture.name,
                'shelf': shelfobject.shelf.name
            }
            obj_item = list(data_column.values())
            if column_list:
                obj_item = load_dataset_by_column(column_list, data_column)
            dataset.append(obj_item)
    return dataset

def lab_room_html(report):
    columns_fields = [
        {'name': 'code', 'title': _("Code")}, {'name': 'object', 'title': _("Object")},
        {'name': 'quantity', 'title': _("Quantity")}, {'name': 'laboratory', 'title': _("Laboratory")},
        {'name': 'laboratory_room', 'title': _("Laboratory Room")}, {'name': 'furniture', 'title': _("Furniture")},
        {'name': 'shelf', 'title': _("Shelf")}
    ]
    columns_fields = set_format_table_columns(columns_fields)
    column_list = list(map(lambda x: x['name'], columns_fields))
    report.table_content = {
        'columns': columns_fields,
        'dataset': get_dataset(report, column_list)
    }
    report.save()
    return len(report.table_content['dataset'])

def lab_room_doc(report):
    builder = ExcelGraphBuilder()
    content = [[_("Code"), _("Object"), _("Quantity"), _("Laboratory"), _("Laboratory Room"), _("Furniture"), _("Shelf")]]
    content = content + get_dataset(report, None)
    record_total=len(content)-1

    report_name = get_report_name(report)
    content.insert(0, [report_name])
    file = builder.save_ods(content, format_type=report.file_type)

    file_name = f'{report_name}.{report.file_type}'
    if "object_type" in report.data:
        file_name = f'{report_name}_{dict(Object.TYPE_CHOICES)[report["object_type"]]}.{report.file_type}'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.save()
    file.close()
    return record_total
