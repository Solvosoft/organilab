from django.conf import settings
from django.db.models import Sum
from django.utils.translation import gettext as _
from laboratory.models import Object, ObjectLogChange, Laboratory
from laboratory.utils import get_user_laboratories
from report.utils import filter_period


def resume_queryset(queryset):

    laboratories = set(queryset.values_list('laboratory__pk', flat=True))
    list_obj = []
    result = []
    total_record=0
    doc_list= []
    doc_elements=[]
    for laboratory in laboratories:
        object_diff = 0
        lab = Laboratory.objects.get(pk=laboratory)
        query = queryset.filter(laboratory=lab)
        objects = set(query.values_list('object', 'measurement_unit'))

        for obj in objects:
            ob= Object.objects.filter(pk=obj[0]).first()
            query_values = query.filter(object=ob, measurement_unit__pk=obj[1])
            object_diff = queryset.filter(laboratory=lab,object=ob, measurement_unit__pk=obj[1]).aggregate(total=Sum('diff_value'))['total']
            for values in query_values:

                try:
                    user = values.user.get_full_name()
                    if not user:
                        user = values.user.username
                except Exception as e:
                    user = ""

                object_list =\
                    {'user': user,
                     'update_time': values.update_time.strftime("%m/%d/%Y, %H:%M:%S"),
                     'old_value': values.old_value,
                     'new_value': values.new_value,
                     'diff_value': values.diff_value,
                     'measurement_unit': str(values.measurement_unit),
                     }
                total_record+=1

                list_obj.append(list(object_list.values()))
                doc_elements.append(list(object_list.values()))
            if ob:
                doc_list.append([f'{lab.name} | {str(ob)} {object_diff}'])
                doc_list.append([_("User"), _("Day"), _('Old'), _('New'), _("Difference"), _("Unit")])
                doc_list.extend(doc_elements)
                doc_list.append([])
                doc_list.append([])
                result.append({'lab': lab.name,'lab_id': lab.id,'obj': str(ob),
                               'obj_id': ob.id, 'unit': obj[1],
                               'values': list_obj,'diff': object_diff})
            list_obj = []
            doc_elements=[]
    return {'record': total_record, 'content': result,'doc_elements':doc_list}


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


def get_dataset_objectlogchanges(report,column_list=None):
    queryset = get_queryset(report)
    object_list = resume_queryset(queryset)
    return object_list
