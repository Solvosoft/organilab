from django.core.files.base import ContentFile
from django.db.models import Sum, Min
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _

from auth_and_perms.models import Profile
from laboratory.models import Object, ObjectLogChange, ShelfObject, Laboratory, OrganizationStructure, \
    SustanceCharacteristics
from laboratory.report_utils import ExcelGraphBuilder
from laboratory.utils import get_user_laboratories, get_cas, get_molecular_formula, get_pk_org_ancestors, get_imdg
from laboratory.views.djgeneric import ResultQueryElement
from report.utils import filter_period, set_format_table_columns, get_report_name


#report_objectlogchange
def resume_queryset(queryset):
    objects = set(queryset.values_list('object', flat=True))
    list_obj = []
    user=""
    for obj in objects:
        obj_check = Object.objects.filter(pk=obj)
        if obj_check.exists():
            ini = queryset.filter(object=obj).values('old_value')[0]['old_value']
            end = queryset.filter(object=obj).last()
            diff = queryset.filter(object=obj).aggregate(balance=Sum('diff_value'))['balance']
            try:
                user = end.user.get_full_name()
            except Exception as e:
                user = ""

            list_obj.append(ResultQueryElement({'user': user,
                                                'laboratory': end.laboratory,
                                                'object': end.object,
                                                'update_time': end.update_time,
                                                'old_value': ini,
                                                'new_value': end.new_value,
                                                'diff_value': diff,
                                                'measurement_unit': end.measurement_unit
                                                })
                            )
    return list_obj

def get_queryset(report):
    query = ObjectLogChange.objects.all().order_by('update_time')
    if 'period' in report.data:
        query = filter_period(report.data['period'], query)
    if 'precursor' in report.data:
        query = query.filter(precursor=True)
    if 'all_labs_org' in report.data:
        query = query.filter(laboratory__in=get_user_laboratories(report.creator))
    else:
        query = query.filter(laboratory__pk=report.data['lab_pk'])
    if 'resume' in report.data:
        query = query
    return query

def get_dataset_objectlogchange(report):
    dataset = []
    queryset = get_queryset(report)
    object_list = resume_queryset(queryset)
    for obj in object_list:
        dataset.append([obj.user, str(obj.laboratory), str(obj.object), obj.update_time.strftime("%m/%d/%Y, %H:%M:%S"),
                                       obj.old_value,  obj.new_value, obj.diff_value, str(obj.measurement_unit)])
    return dataset

def report_objectlogchange_html(report):
    columns_fields = [
        {'name': 'user', 'title':_("User")}, {'name': 'laboratory', 'title': _("Laboratory")},
        {'name': 'object', 'title':_("Object")}, {'name': 'update_time', 'title':_("Day"), 'type': 'date'},
        {'name': 'old_value', 'title':_("Old")}, {'name': 'new_value', 'title':_("New")},
        {'name': 'diff_value', 'title':_("Difference")},{'name': 'measurement_unit', 'title':_("Unit")}
    ]
    report.table_content = {
        'columns': set_format_table_columns(columns_fields),
        'dataset': get_dataset_objectlogchange(report)
    }
    report.save()

def report_objectlogchange_doc(report):
    builder = ExcelGraphBuilder()
    content = [[_("User"), _("Laboratory"), _("Object"), _("Day"), _('Old'), _('New'), _("Difference"), _("Unit")]]
    content = content + get_dataset_objectlogchange(report)
    report_name = get_report_name(report)
    builder.add_table(content, report_name)
    file=builder.save()
    file_name = f'{report_name}.{report.file_type}'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.save()
    file.close()

#report_reactive_precursor
def get_dataset_reactive_precursor(report):
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
            obj_item = [laboratory.name] if general else []
            obj_item = obj_item + [
                object.code, object.name, object.get_type_display(),
                object.quantity_total, ShelfObject.get_units(object.measurement_unit),
                str(get_molecular_formula(object)), str(get_cas(object, "")), precursor, str(get_imdg(object, ""))
            ]
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

    report.table_content = {
        'columns': set_format_table_columns(columns_fields),
        'dataset': get_dataset_reactive_precursor(report)
    }
    report.save()

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

    content = content + get_dataset_reactive_precursor(report)
    report_name = get_report_name(report)
    builder.add_table(content, report_name)
    file=builder.save()
    file_name = f'{report_name}.{report.file_type}'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.save()
    file.close()

#report_objects
def get_object_elements(obj):
    features=""
    shelfobjects=""
    danger = ""
    for feature in obj.features.all():
        features+=f"{feature.name} "

    if hasattr(obj, 'sustancecharacteristics'):

        for h_code in obj.sustancecharacteristics.h_code.all():
            danger+=f"{h_code} "


    for shelfobject in obj.shelfobject_set.all():
        shelfobjects += f'{shelfobject.shelf}: {shelfobject.quantity} {shelfobject.get_measurement_unit_display()}'

    return [features,danger,shelfobjects]

def get_dataset_objects(report):
    dataset, labs = [], []
    filters = {'is_public': True}
    general = True if 'all_labs_org' in report.data else False
    if 'organization' in report.data:
        org = report.data['organization']
        filters['organization__in'] = get_pk_org_ancestors(org)

    if 'laboratory' in report.data:
        labs = report.data['laboratory']

    if 'object_type' in report.data:
        filters['type'] = report.data['object_type']

    objects = Object.objects.filter(**filters)

    for lab_pk in labs:
        lab = Laboratory.objects.filter(pk=lab_pk).first()
        for obj in objects:
            formula = "-"
            features, danger, shelfobjects = get_object_elements(obj)

            if hasattr(obj, 'sustancecharacteristics'):
                formula = obj.sustancecharacteristics.molecular_formula if obj.sustancecharacteristics.molecular_formula else '-'
            cas = get_cas(obj, "") if get_cas(obj, "") else ""

            obj_item = [lab.name] if general else []
            obj_item = obj_item + [
                obj.code, obj.name, obj.get_type_display(),
                features, danger,
                shelfobjects, formula, cas
            ]
            dataset.append(obj_item)
    return dataset

def report_objects_html(report):
    general = True if 'all_labs_org' in report.data else False
    columns = [{'name': 'laboratory', 'title': _("Laboratory")}] if general else []
    columns_fields = columns + [
        {'name': 'code', 'title': _("Code")}, {'name': 'name', 'title': _("Name")},
        {'name': 'type', 'title': _("Type")}, {'name': 'features', 'title': _("Features")},
        {'name': 'danger_indication', 'title': _("Danger indication")}, {'name': 'quantity', 'title': _("Quantity")},
        {'name': 'molecular_formula', 'title': _("Molecular formula")}, {'name': 'cas_id_number', 'title': _("CAS id number")}
    ]
    report.table_content = {
        'columns': set_format_table_columns(columns_fields),
        'dataset': get_dataset_objects(report)
    }
    report.save()

def report_object_doc(report):
    builder = ExcelGraphBuilder()
    content = [[
        _("Code"), _("Name"), _("Type"), _("Features"), _('Danger indication'),
        _('Quantity'), _("Molecular formula"), _("CAS id number")
    ]]
    if 'laboratory' in report.data:
        labs = report.data['laboratory']
        if len(labs) > 1:
            content[0].insert(0,_('Laboratory'))

    content = content + get_dataset_limit_objects(report)
    report_name = get_report_name(report)
    builder.add_table(content, report_name)
    file=builder.save()
    file_name = f'{report_name}.{report.file_type}'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.save()
    file.close()

#report_limit_object
def get_dataset_limit_objects(report):
    dataset = []
    if 'laboratory' in report.data:
        labs = Laboratory.objects.filter(pk__in=report.data['laboratory'])
        for lab in labs:
            shelf_objects = ShelfObject.objects.filter(
                        shelf__furniture__labroom__laboratory=lab)

            shelf_objects = get_limited_shelf_objects(shelf_objects)
            for shelfobj in shelf_objects:
                obj_item = [lab.name] if len(labs) > 1 else []
                obj_item = obj_item + [
                    shelfobj.shelf.name, shelfobj.object.code, shelfobj.object.name, f'{shelfobj.quantity} {shelfobj.get_measurement_unit_display()}',
                    f'{shelfobj.limit_quantity} {shelfobj.get_measurement_unit_display()}'
                ]
                dataset.append(obj_item)
    return dataset

def get_limited_shelf_objects(query):
    for shelf_object in query:
        if shelf_object.limit_reached:
            yield shelf_object

def report_limit_object_html(report):
    columns_fields = [
        {'name': 'shelf', 'title': _("Shelf")}, {'name': 'code', 'title': _("Code")},
        {'name': 'object', 'title': _("Object")}, {'name': 'quantity', 'title': _("Quantity")},
        {'name': 'limit_quantity', 'title': _("Limit quantity")}, {'name': 'measurement_unit', 'title': _("Measurement Unit")}
    ]
    report.table_content = {
        'columns': set_format_table_columns(columns_fields),
        'dataset': get_dataset_limit_objects(report)
    }
    report.save()

def report_limit_object_doc(report):
    builder = ExcelGraphBuilder()
    content = [[
        _("Shelf"), _("Code"), _("Object"), _("Quantity"), _('Limit quantity'), _("Measurement Unit")
    ]]
    if 'laboratory' in report.data:
        labs = report.data['laboratory']
        if len(labs) > 1:
            content[0].insert(0,_('Laboratory'))

    content =  content + get_dataset_limit_objects(report)
    report_name = get_report_name(report)
    builder.add_table(content, report_name)
    file=builder.save()
    file_name = f'{report_name}.{report.file_type}'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.save()
    file.close()

#report_organization_reactive
def get_dataset_report_organization_reactive(report):
    dataset = []
    if 'organization' in report.data:
        org_pk = report.data['organization']
        organization = get_object_or_404(OrganizationStructure, pk=org_pk)

        if 'laboratory' in report.data:
            laboratories = organization.laboratory_set.filter(
                profile__user=report.creator, pk__in=report.data['laboratory']).\
                values('name', 'laboratoryroom__furniture')
        else:
            laboratories = organization.laboratory_set.filter(profile__user=report.creator).\
                values('name', 'laboratoryroom__furniture')

        if 'users' in report.data:
            usermanagement = organization.users.filter(pk__in=report.data['users']).values('first_name', 'last_name', 'id')
        else:
            usermanagement = organization.users.values('first_name', 'last_name', 'id')

        for lab in laboratories:
            reactives = SustanceCharacteristics.objects.filter(obj__in=list(ShelfObject.objects.filter(
                shelf__furniture=lab['laboratoryroom__furniture']
            ).values_list('object', flat=True))).exclude(cas_id_number=None).distinct()

            for user in usermanagement:

                try:
                    profile = Profile.objects.get(user__id=user['id'])
                except Profile.DoesNotExist as error:
                    profile = None

                for reactive in reactives:
                    obj_item = [
                        lab["name"], user["first_name"], user["last_name"], reactive.obj.code, reactive.obj.name,
                        reactive.cas_id_number,
                        ", ".join(reactive.white_organ.all().values_list("description", flat=True)),
                        str(reactive.iarc) if reactive.iarc else ""
                    ]

                    if profile:
                        obj_item = obj_item + [profile.id_card, profile.job_position]
                    else:
                        obj_item = obj_item + ["", ""]

                    dataset.append(obj_item)
    return dataset

def report_organization_reactive_list_html(report):
    columns_fields = [
        {'name': 'laboratory_name', 'title': _("Laboratory name")}, {'name': 'first_name', 'title': _("First Name")},
        {'name': 'last_name', 'title': _("Last Name")}, {'name': 'code', 'title': _("Code")},
        {'name': 'substance', 'title': _("Substance")}, {'name': 'cas', 'title': _("CAS")},
        {'name': 'white_organ', 'title': _("White Organ")}, {'name': 'carcinogenic', 'title': _("Carcinogenic")},
        {'name': 'id_card', 'title': _("ID Card")}, {'name': 'job_position', 'title': _("Job Position")}
    ]
    report.table_content = {
        'columns': set_format_table_columns(columns_fields),
        'dataset': get_dataset_report_organization_reactive(report)
    }
    report.save()

def report_organization_reactive_list_doc(report):
    builder = ExcelGraphBuilder()
    content = [[_('Laboratory name'), _('First Name'), _('Last Name'), _('Code'), _('Sustance'), _('CAS'),
                    _('White Organ'), _('Carcinogenic'), _('ID Card'), _('Job Position')]]
    content = content + get_dataset_report_organization_reactive(report)
    report_name = get_report_name(report)
    builder.add_table(content, report_name)
    file=builder.save()
    file_name = f'{report_name}.{report.file_type}'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.save()
    file.close()