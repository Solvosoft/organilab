from django.core.files.base import ContentFile
from django.utils.translation import gettext as _
from laboratory.models import ShelfObject, Object
from laboratory.report_utils import ExcelGraphBuilder
from report.utils import filter_period, set_format_table_columns, get_report_name, load_dataset_by_column
from risk_management.models import RiskZone


def get_dataset_report(report, column_list=None):
    dataset = []
    filters = {"object__type":0}
    risk_zones = RiskZone.objects.filter(organization__pk=report.data['organization'])
    if "riskzone" in report.data:
        risk_zones = risk_zones.filter(pk__in=report.data['riskzone'])
    laboratories = risk_zones.values_list('buildings__laboratories', flat=True)
    laboratories = laboratories.filter(pk__in=laboratories).distinct()
    filters.update({'in_where_laboratory__in': laboratories})
    objs = ShelfObject.objects.filter(**filters).values_list("object__pk", flat=True)
    objs = Object.objects.filter(pk__in=objs).distinct()
    for reactive in objs:
        cas_id = ""
        threshold = "NA"
        dangerous = reactive.is_dangerous
        third_square = False
        third_column = ""
        if dangerous:
            third_column = _("Square 3")+" "

        if hasattr(reactive.object, 'sustancecharacteristics'):
            physical = reactive.sustancecharacteristics.h_code.filter(category_h_code__danger_category="physical").values_list("description", flat=True)
            health = reactive.sustancecharacteristics.h_code.filter(category_h_code__danger_category="health").values_list("description", flat=True)
            enviroment = reactive.sustancecharacteristics.h_code.filter(category_h_code__danger_category="environment").values_list("description", flat=True)
            cas_id = reactive.object.cas_code

            if physical.exists() or health.exists() or enviroment.exists():
                third_square = True
                third_column += _("Square 4")

        if not dangerous and not third_square:
            third_column = _("None")


        data_column = {
            'name': reactive.object.name,
            'cas_id': cas_id,
            "square": third_column,
            'threshold': threshold,
        }
        obj_item = list(data_column.values())

        if column_list:
            obj_item = load_dataset_by_column(column_list, data_column)
        dataset.append(obj_item)
    return dataset

def report_risk_zone_html(report):
    columns_fields = [
        {'name': 'name', 'title': _("Substance")},
        {'name': 'cas_id', 'title': _("CAS")},
        {'name': 'square', 'title': _("Square 3")},
        {'name': 'threshold', 'title': _("Threshold")},
    ]

    columns_fields = set_format_table_columns(columns_fields)
    column_list = list(map(lambda x: x['name'], columns_fields))
    report.table_content = {
        'columns': columns_fields,
        'dataset': get_dataset_report(report, column_list)
    }
    report.save()
    return len(report.table_content['dataset'])


def report_risk_zone_list_doc(report):
    builder = ExcelGraphBuilder()
    content = [[_('Substance'), _('CAS'), _('Table 4, 3 or none'),
                _('Exceeds THRESHOLD OR NA, if the previous (column) is none'),]]

    content = content + get_dataset_report(report)

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
