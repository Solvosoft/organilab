from django.conf import settings
from django.db.models import Sum
from django.utils.translation import gettext as _
from laboratory.models import Object, ObjectLogChange, Laboratory, Catalog
from laboratory.utils import get_user_laboratories
from report.models import ObjectChangeLogReport, ObjectChangeLogReportBuilder
from report.utils import filter_period


def resume_queryset(report,queryset):

    laboratories = set(queryset.values_list('laboratory__pk', flat=True))
    builder = []
    total = 0
    doc_list=[]

    for laboratory in laboratories:
        lab = Laboratory.objects.get(pk=laboratory)
        query = queryset.filter(laboratory=lab)
        objects = set(query.values_list('object', 'measurement_unit'))

        for obj in objects:
            object_log = None
            obj_using = Object.objects.filter(pk=obj[0]).first()
            catalog = Catalog.objects.get(pk=obj[1])
            query_values = query.filter(object=obj_using, measurement_unit__pk=obj[1])
            object_diff = queryset.filter(laboratory=lab,
                                          object=obj_using,
                                          measurement_unit__pk=obj[1]
                                          ).aggregate(total=Sum('diff_value'))['total']
            if query_values:

                object_log = ObjectChangeLogReport.objects.create(
                    task_report=report,
                    laboratory=lab,
                    object=obj_using,
                    unit=catalog,
                    diff_value=object_diff)

            for values in query_values:

                object_builder = ObjectChangeLogReportBuilder(
                    report=object_log,
                    user=values.user,
                    old_value=values.old_value,
                    new_value=values.new_value,
                    diff_value=values.diff_value,
                    update_time=values.update_time
                )

                builder.append(object_builder)

                total += 1
            if object_log:
                ObjectChangeLogReportBuilder.objects.bulk_create(
                    builder
                )
            builder.clear()
    return total

def resume_queryset_doc(report,queryset):

    laboratories = set(queryset.values_list('laboratory__pk', flat=True))
    builder = []
    total = 0
    doc_list=[]

    for laboratory in laboratories:
        object_log = None
        lab = Laboratory.objects.get(pk=laboratory)
        query = queryset.filter(laboratory=lab)
        objects = set(query.values_list('object', 'measurement_unit'))

        for obj in objects:

            object_log = None
            obj_using = Object.objects.filter(pk=obj[0]).first()
            catalog = Catalog.objects.get(pk=obj[1])
            query_values = query.filter(object=obj_using, measurement_unit__pk=obj[1])
            object_diff = queryset.filter(laboratory=lab,
                                          object=obj_using,
                                          measurement_unit__pk=obj[1]
                                          ).aggregate(total=Sum('diff_value'))['total']
            if query_values:
                object_log=True
            for values in query_values:

                try:
                    user = values.user.get_full_name()
                    if not user:
                        user = values.user.username
                except Exception as e:
                    user = ""
                builder.append([user, values.update_time.strftime("%m/%d/%Y, %H:%M:%S"),
                                values.old_value, values.new_value, values.diff_value])
                total += 1

            if object_log:
                doc_list.append([f'{lab.name} | {obj_using.name}'])
                doc_list.append([_('Difference')+f': {object_diff} {catalog.description}'])
                doc_list.append(
                        [_("User"), _("Day"), _('Old'), _('New'), _("Difference")])
                doc_list.extend(builder)
                doc_list.append([])
                doc_list.append([])
            builder = []

    return {'record': total, 'content': doc_list}

def get_queryset(report):
    query = ObjectLogChange.objects.all().using(settings.READONLY_DATABASE).order_by('update_time')
    if 'period' in report.data:
        if report.data['period']:
            query = filter_period(report.data['period'], query)
    if 'precursor' in report.data:
        if report.data['precursor']:
            query = query.filter(precursor=True)
    if 'all_labs_org' in report.data:
        if report.data['all_labs_org']:
            query = query.filter(laboratory__in=get_user_laboratories(report.creator))
        else:
            query = query.filter(laboratory__pk=report.data['lab_pk'])
    else:
        query = query.filter(laboratory__pk=report.data['lab_pk'])

    return query


def get_dataset_objectlogchanges(report,is_doc=False,column_list=None):
    queryset = get_queryset(report)
    object_list = None
    if is_doc:
        object_list = resume_queryset_doc(report,queryset)
    else:
        object_list = resume_queryset(report,queryset)
    return object_list
