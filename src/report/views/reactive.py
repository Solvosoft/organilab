from django.core.files.base import ContentFile
from django.utils.translation import gettext as _
from laboratory.models import ShelfObject
from laboratory.report_utils import ExcelGraphBuilder
from report.utils import filter_period, set_format_table_columns, get_report_name, load_dataset_by_column


def get_dataset_report_reactive(report, column_list=None):
    dataset = []
    filters = {"object__type":0}
    if 'laboratory' in report.data:
        filters['in_where_laboratory__pk'] = report.data['laboratory']

    objs = ShelfObject.objects.filter(**filters).distinct('pk').order_by('pk')
    for reactive in objs:
        physical = ""
        health = ""
        enviroment = ""
        cas_id =""
        if hasattr(reactive.object, 'sustancecharacteristics'):
            physical = " ".join(reactive.object.sustancecharacteristics.h_code.filter(category_h_code__danger_category="physical").values_list("description", flat=True))
            health = " ".join(reactive.object.sustancecharacteristics.h_code.filter(category_h_code__danger_category="health").values_list("description", flat=True))
            enviroment = " ".join(reactive.object.sustancecharacteristics.h_code.filter(category_h_code__danger_category="environment").values_list("description", flat=True))
            cas_id = reactive.object.cas_code

        location = reactive.in_where_laboratory.location if hasattr(reactive.in_where_laboratory, 'location') else ""
        physical_status = reactive.get_physical_status_display() if reactive.physical_status else ""
        data_column = {
            'name': reactive.object.name,
            'cas_id': cas_id,
            'location': location,
            'physical_status': physical_status,
            'physical': physical,
            'health': health,
            'environment': enviroment,
            'concentration': reactive.concentration,
            'quantity': reactive.quantity,
            'measurement_unit': reactive.get_measurement_unit_display()
        }
        obj_item = list(data_column.values())

        if column_list:
            obj_item = load_dataset_by_column(column_list, data_column)
        dataset.append(obj_item)
    return dataset

def report_reactive_html(report):
    columns_fields = [
        {'name': 'name', 'title': _("Name")},{'name': 'cas_id', 'title': _("CAS")},
        {'name': 'location', 'title': _("Location")},
        {'name': 'physical_status', 'title': _("Physical Status")},
        {'name': 'physical', 'title': _("Physical Hazard Category (Code H)")},
        {'name': 'health', 'title': _("Health Hazard Category (Code H)")},
        {'name': 'environment', 'title': _("Environmental Hazard Category (Code H)")},
        {'name': 'concentration', 'title': _("Concentration")},
        {'name': 'quantity', 'title': _("Quantity")},
        {'name': 'measurement_unit', 'title': _("Measurement Unit")}

    ]
    columns_fields = set_format_table_columns(columns_fields)
    column_list = list(map(lambda x: x['name'], columns_fields))
    report.table_content = {
        'columns': columns_fields,
        'dataset': get_dataset_report_reactive(report, column_list)
    }
    report.save()
    return len(report.table_content['dataset'])


def report_reactive_list_doc(report):
    builder = ExcelGraphBuilder()
    content = [[_('Name'), _('CAS'), _('Location'), _('Physical Status'),
                _('Physical Hazard Category (Code H)'), _('Health Hazard Category (Code H)'),
                _('Environmental Hazard Category (Code H)'), _('Concentration'),
                _('Quantity'), _('Measurement Unit')]]

    content = content + get_dataset_report_reactive(report, None)

    record_total = len(content)-1
    report_name = get_report_name(report)
    content.insert(0, [report_name])
    file = builder.save_ods(content, format_type=report.file_type)

    file_name = f'{report_name}.{report.file_type}'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.save()
    file.close()
    return record_total
