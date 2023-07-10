from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db.models import Sum, Min, Count
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from auth_and_perms.models import Profile
from laboratory.models import Object, ObjectLogChange, ShelfObject, Laboratory, OrganizationStructure, \
    SustanceCharacteristics
from laboratory.report_utils import ExcelGraphBuilder
from laboratory.utils import get_user_laboratories, get_cas, get_molecular_formula, get_pk_org_ancestors, get_imdg, \
    get_users_from_organization
from laboratory.views.djgeneric import ResultQueryElement
from report.models import ObjectChangeLogReportBuilder
from report.utils import filter_period, set_format_table_columns, get_report_name, load_dataset_by_column
from report.views.object_changes import  get_dataset_objectlogchanges


#report_objectlogchange
def resume_queryset(queryset):
    laboratories = set(queryset.values_list('laboratory__pk',flat=True))
    objectchange_list= []
    result=[]
    for laboratory in laboratories:
        lab= Laboratory.objects.get(pk=laboratory)
        query = queryset.filter(laboratory=lab)
        objects = set(query.values_list('object','measurement_unit'))
        for obj in objects:
            query_values=query.filter(object__pk=obj[0],measurement_unit__pk=obj[1])
            objectchange_list.append({'lab':lab.name,"values":query_values,
                                      'diff':query_values.aggregate(total=Sum('diff_value'))['total']})

    list_obj=[]
    i=0
    for obj in objectchange_list:
        for ob in obj['values']:
            try:
                user = ob.user.get_full_name()
                if not user:
                    user = ob.user.username
            except Exception as e:
                user = ""

            object_list=ResultQueryElement({'user': user,
                         #'laboratory': ob.laboratory,
                         'pk':ob.pk,
                         'object': ob.object,
                         'update_time': ob.update_time,
                         'old_value': ob.old_value,
                         'new_value': ob.new_value,
                         'diff_value': ob.diff_value,
                         'measurement_unit': ob.measurement_unit
                                                })
            list_obj.append(object_list)

    return list_obj
def get_queryset(report):
    query = ObjectLogChange.objects.all().order_by('update_time')
    if 'period' in report.data:
        query = filter_period(report.data['period'], query)
    if 'precursor' in report.data:
        query = query.filter(precursor=True)
    if 'all_labs_org' in report.data:
        query = query.filter(laboratory__in=get_user_laboratories(report.created_by))
    else:
        query = query.filter(laboratory__pk=report.data['lab_pk'])
    if 'resume' in report.data:
        query = query
    return query

def get_dataset_objectlogchange(report, column_list=None):
    dataset = []
    queryset = get_queryset(report)
    object_list = resume_queryset(queryset)
    for obj in object_list:
        data_column = {
            'user': obj.user,
            'laboratory': str(obj.laboratory),
            'object': str(obj.object),
            'update_time': obj.update_time.strftime("%m/%d/%Y, %H:%M:%S"),
            'old_value': obj.old_value,
            'new_value': obj.new_value,
            'diff_value': obj.diff_value,
            'measurement_unit': str(obj.measurement_unit)
        }
        obj_item = list(data_column.values())

        if column_list:
            obj_item = load_dataset_by_column(column_list, data_column)
        dataset.append(obj_item)
    return dataset

def report_objectlogchange_html(report):
    get_dataset_objectlogchanges(report)
    record = ObjectChangeLogReportBuilder.objects.filter(report__task_report=report).\
        count()
    return record

def report_objectlogchange_pdf(report):
    get_dataset_objectlogchanges(report)
    record = ObjectChangeLogReportBuilder.objects.filter(report__task_report=report).\
        count()
    return record

def report_objectlogchange_doc(report):
    builder = ExcelGraphBuilder()
    content = get_dataset_objectlogchanges(report,True, None)
    record_total=content['record']
    file=None
    report_name = get_report_name(report)

    file=builder.save_ods(content['content'], format_type=report.file_type)
    file_name = f'{report_name}.{report.file_type}'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.save()
    file.close()
    return record_total

#report_reactive_precursor
def get_dataset_reactive_precursor(report, column_list=None):
    general = True if 'all_labs_org' in report.data else False
    dataset = []
    lab = []

    if 'laboratory' in report.data:
        lab = report.data['laboratory']

    for lab_pk in lab:
        if lab:
            rpo = Object.objects.filter(
                shelfobject__shelf__furniture__labroom__laboratory__pk=lab_pk)
        else:
            rpo = Object.objects.all()

        rpo = rpo.filter(type=Object.REACTIVE, sustancecharacteristics__is_precursor=True)
        objects = rpo.annotate(quantity_total=Sum('shelfobject__quantity'),
                               measurement_unit=Min('shelfobject__measurement_unit'))
        laboratory = Laboratory.objects.filter(pk=lab_pk).first()

        for object in objects:
            precursor = _('Yes') if object.is_precursor else 'No'
            data_column = {
                'laboratory': laboratory.name,
                'code': object.code,
                'name': object.name,
                'type': object.get_type_display(),
                'quantity_total': object.quantity_total,
                'measurement_unit': ShelfObject.get_units(object.measurement_unit),
                'molecular_formula': str(get_molecular_formula(object)),
                'cas_id_number': str(get_cas(object, "")),
                'precursor': precursor,
                'imdg_type': str(get_imdg(object, "")),
            }
            obj_item = list(data_column.values())

            if column_list:
                obj_item = load_dataset_by_column(column_list, data_column)
            elif not general:
                del obj_item[0]
            dataset.append(obj_item)
    return dataset

def report_reactive_precursor_html(report):
    general = True if 'all_labs_org' in report.data else False
    columns = [{'name': 'laboratory', 'title': _("Laboratory")}] if general else []
    columns_fields = columns + [
        {'name': 'code', 'title': _("Code")},{'name': 'name', 'title': _("Name")},
        {'name': 'type', 'title': _("Type")}, {'name': 'quantity_total', 'title': _("Quantity total")},
        {'name': 'measurement_unit', 'title': _("Measurement units")}, {'name': 'molecular_formula', 'title': _("Molecular formula")},
        {'name': 'cas_id_number', 'title': _("CAS id number")}, {'name': 'precursor', 'title': _("Is precursor?")},
        {'name': 'imdg_type', 'title': _("IMDG type")}
        ]
    columns_fields = set_format_table_columns(columns_fields)
    column_list = list(map(lambda x: x['name'], columns_fields))
    report.table_content = {
        'columns': columns_fields,
        'dataset': get_dataset_reactive_precursor(report, column_list)
    }
    report.save()
    return len(report.table_content['dataset'])

def report_reactive_precursor_doc(report):
    builder = ExcelGraphBuilder()
    content = [[
        _("Code"), _("Name"), _("Type"), _("Quantity total"), _('Measurement units'), _("Molecular formula"),
        _("CAS id number"), _("Is precursor?"), _("IMDG type")
    ]]
    if 'laboratory' in report.data:
        labs = report.data['laboratory']
        if len(labs) > 1:
            content[0].insert(0, _('Laboratory'))

    content = content + get_dataset_reactive_precursor(report, None)
    record_total=len(content)-1

    report_name = get_report_name(report)
    builder.add_table(content, report_name)
    file=None
    if report.file_type!= 'ods':
        builder.add_table(content, report_name)
        file=builder.save()
    else:
        content.insert(0,[report_name])
        file=builder.save_ods(content)
    file_name = f'{report_name}.{report.file_type}'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.save()
    file.close()
    return record_total

#report_objects
def get_object_elements(obj):
    features=""
    danger = ""
    all_features = obj.features.all()

    for x, feature in enumerate(all_features):
        features += f"{feature.name}"
        if not(x + 1 == len(all_features)):
            features += ", "

    if hasattr(obj, 'sustancecharacteristics'):
        all_hcode = obj.sustancecharacteristics.h_code.all()
        for x, h_code in enumerate(all_hcode):
            danger += f"{h_code}"
            if not(x + 1 == len(all_hcode)):
                danger += ", "

    return [features, danger]

def get_objects(report):
    filters = {'object__is_public': True}

    if 'organization' in report.data:
        org = report.data['organization']
        filters['object__organization__in'] = get_pk_org_ancestors(org)

    if 'laboratory' in report.data:
        filters['in_where_laboratory__pk__in']=report.data['laboratory']

    if 'object_type' in report.data:
        if report.data['object_type'] in dict(Object.TYPE_CHOICES).keys():
            filters['object__type'] = report.data['object_type']

    objects = ShelfObject.objects.filter(**filters).distinct('pk')
    return objects

def get_dataset_objects(report, column_list=None):
    dataset = []
    objects = get_objects(report)
    general = True if 'all_labs_org' in report.data else False

    for obj in objects:
        formula = "-"
        features, danger = get_object_elements(obj.object)
        if hasattr(obj.object, 'sustancecharacteristics'):
            formula = obj.object.sustancecharacteristics.molecular_formula if obj.object.sustancecharacteristics.molecular_formula else '-'
        cas = get_cas(obj.object, "") if get_cas(obj.object, "") else ""
        data_column = {
            'laboratory': obj.in_where_laboratory.name,
            'code': obj.object.code,
            'name': obj.object.name,
            'type': obj.object.get_type_display(),
            'features': features,
            'danger_indication': danger,
            'molecular_formula': formula,
            'cas_id_number': cas
        }
        obj_item = list(data_column.values())

        if column_list:
            obj_item = load_dataset_by_column(column_list, data_column)
        elif not general:
            del obj_item[0]
        dataset.append(obj_item)
    return dataset

def report_objects_html(report):
    general = True if 'all_labs_org' in report.data else False
    columns = [{'name': 'laboratory', 'title': _("Laboratory")}] if general else []
    columns_fields = columns + [
        {'name': 'code', 'title': _("Code")}, {'name': 'name', 'title': _("Name")},
        {'name': 'type', 'title': _("Type")}, {'name': 'features', 'title': _("Features")},
        {'name': 'danger_indication', 'title': _("Danger indication")},
        {'name': 'molecular_formula', 'title': _("Molecular formula")},
        {'name': 'cas_id_number', 'title': _("CAS id number")}
    ]
    columns_fields = set_format_table_columns(columns_fields)
    column_list = list(map(lambda x: x['name'], columns_fields))
    report.table_content = {
        'columns': columns_fields,
        'dataset': get_dataset_objects(report, column_list)
    }
    report.save()
    return len(report.table_content['dataset'])

def report_objects_doc(report):
    builder = ExcelGraphBuilder()
    content = [[
        _("Code"), _("Name"), _("Type"), _("Features"), _('Danger indication'),
        _("Molecular formula"), _("CAS id number")
    ]]
    if 'laboratory' in report.data:
        labs = report.data['laboratory']
        if len(labs) > 1:
            content[0].insert(0,_('Laboratory'))

    content = content + get_dataset_objects(report, None)
    record_total =len(content)-1
    report_name = get_report_name(report)
    builder.add_table(content, report_name)
    file=None
    if report.file_type!= 'ods':
        builder.add_table(content, report_name)
        file=builder.save()
    else:
        content.insert(0,[report_name])
        file=builder.save_ods(content)
    file_name = f'{report_name}.{report.file_type}'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.save()
    file.close()
    return record_total

#report_limit_object
def get_limited_shelf_objects(query):
    for shelf_object in query:
        if shelf_object.limit_reached:
            yield shelf_object

def get_dataset_limit_objects(report, column_list=None):
    dataset = []
    if 'laboratory' in report.data:
        labs = Laboratory.objects.filter(pk__in=report.data['laboratory'])
        for lab in labs:
            shelf_objects = ShelfObject.objects.filter(
                        shelf__furniture__labroom__laboratory=lab)

            shelf_objects = get_limited_shelf_objects(shelf_objects)
            for shelfobj in shelf_objects:
                data_column = {
                    'laboratory': lab.name,
                    'shelf': shelfobj.shelf.name,
                    'code': shelfobj.object.code,
                    'object': shelfobj.object.name,
                    'quantity': shelfobj.quantity,
                    'limit_quantity': shelfobj.limit_quantity,
                    'measurement_unit': shelfobj.get_measurement_unit_display()
                }
                obj_item = list(data_column.values())

                if column_list:
                    obj_item = load_dataset_by_column(column_list, data_column)
                elif not len(labs) > 1:
                    del obj_item[0]
                dataset.append(obj_item)
    return dataset

def report_limit_object_html(report):
    general = True if 'all_labs_org' in report.data else False
    columns = [{'name': 'laboratory', 'title': _("Laboratory")}] if general else []
    columns_fields = columns + [
        {'name': 'shelf', 'title': _("Shelf")}, {'name': 'code', 'title': _("Code")},
        {'name': 'object', 'title': _("Object")}, {'name': 'quantity', 'title': _("Quantity")},
        {'name': 'limit_quantity', 'title': _("Limit quantity")},{'name': 'measurement_unit', 'title':_("Unit")}
    ]
    columns_fields = set_format_table_columns(columns_fields)
    column_list = list(map(lambda x: x['name'], columns_fields))
    report.table_content = {
        'columns': columns_fields,
        'dataset': get_dataset_limit_objects(report, column_list)
    }
    report.save()
    return len(report.table_content['dataset'])
def report_limit_object_doc(report):
    builder = ExcelGraphBuilder()
    content = [[
        _("Shelf"), _("Code"), _("Object"), _("Quantity"), _('Limit quantity'), _("Measurement Unit")
    ]]
    if 'laboratory' in report.data:
        labs = report.data['laboratory']
        if len(labs) > 1:
            content[0].insert(0,_('Laboratory'))

    content =  content + get_dataset_limit_objects(report, None)
    record_total=len(content)-1
    report_name = get_report_name(report)
    builder.add_table(content, report_name)

    if report.file_type!= 'ods':
        builder.add_table(content, report_name)
        file=builder.save()
    else:
        content.insert(0,[report_name])
        file=builder.save_ods(content)
    file_name = f'{report_name}.{report.file_type}'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.save()
    file.close()
    return record_total

#report_organization_reactive
def get_dataset_report_organization_reactive(report, column_list=None):
    dataset = []
    filters = {"object__sustancecharacteristics__isnull":False}

    if 'organization' in report.data:
        org_pk = report.data['organization']
        organization = get_object_or_404(OrganizationStructure, pk=org_pk)
        filters['object__organization'] = organization
        users = get_users_from_organization(org_pk)

        if 'users' in report.data:
            users =  report.data['users']

        objs = ObjectLogChange.objects.filter(**filters, user__in=users).values('object','laboratory__name','object__code','object__name','user__pk','user__first_name','user__last_name').annotate(count=Count('object'))
        for reactive in objs:
            caracteristics = SustanceCharacteristics.objects.filter(obj__pk=reactive['object']).first()
            white_organ = ", ".join(caracteristics.white_organ.all().values_list("description", flat=True))
            iarc = str(caracteristics.iarc) if caracteristics.iarc else ""
            data_column = {
                'laboratory_name': reactive['laboratory__name'],
                'first_name': reactive['user__first_name'],
                'last_name': reactive['user__last_name'],
                'code': reactive["object__code"],
                'substance': reactive["object__name"],
                'cas': caracteristics.cas_id_number,
                'white_organ': white_organ,
                'carcinogenic': iarc,
                'id_card': "",
                'job_position': "",
                'amount': 1
            }

            try:
                profile = Profile.objects.get(user__pk=reactive['user__pk'])
                data_column.update({
                    'id_card': profile.id_card,
                    'job_position': profile.job_position,
                    'amount': reactive["count"]
                })
            except Profile.DoesNotExist as error:
                pass

            obj_item = list(data_column.values())

            if column_list:
                obj_item = load_dataset_by_column(column_list, data_column)
            dataset.append(obj_item)
    return dataset

def report_reactive_exposition_html(report):
    columns_fields = [
        {'name': 'laboratory_name', 'title': _("Laboratory name")},{'name': 'first_name', 'title': _("First Name")},
        {'name': 'last_name', 'title': _("Last Name")}, {'name': 'code', 'title': _("Code")},
        {'name': 'substance', 'title': _("Substance")}, {'name': 'cas', 'title': _("CAS")},
        {'name': 'white_organ', 'title': _("White Organ")}, {'name': 'carcinogenic', 'title': _("Carcinogenic")},
        {'name': 'id_card', 'title': _("ID Card")}, {'name': 'job_position', 'title': _("Job Position")},
        {'name': 'amount', 'title': "#" + _("Exposition")}
    ]
    columns_fields = set_format_table_columns(columns_fields)
    column_list = list(map(lambda x: x['name'], columns_fields))
    report.table_content = {
        'columns': columns_fields,
        'dataset': get_dataset_report_organization_reactive(report, column_list)
    }
    report.save()
    return len(report.table_content['dataset'])

def report_organization_reactive_list_doc(report):
    builder = ExcelGraphBuilder()
    content = [[_('Laboratory name'), _('First Name'), _('Last Name'), _('Code'), _('Sustance'), _('CAS'),
                _('White Organ'), _('Carcinogenic'), _('ID Card'), _('Job Position'), "#"+_("Exposition")]]
    content = content + get_dataset_report_organization_reactive(report, None)

    record_total=len(content)-1
    report_name = get_report_name(report)
    if report.file_type!= 'ods':
        builder.add_table(content, report_name)
        file=builder.save()
    else:
        content.insert(0,[report_name])
        file=builder.save_ods(content)
    file_name = f'{report_name}.{report.file_type}'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.save()
    file.close()
    return record_total
