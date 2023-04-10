from django.core.files.base import ContentFile
from django.db.models import Sum, Min
from django.template.loader import render_to_string
from io import BytesIO
from django.utils.translation import gettext as _
from weasyprint import HTML

from laboratory.models import Object, ObjectLogChange, ShelfObject, Laboratory

from laboratory.report_utils import ExcelGraphBuilder
from laboratory.utils import get_user_laboratories, get_cas, get_molecular_formula, get_pk_org_ancestors, get_imdg
from laboratory.views.djgeneric import ResultQueryElement
from django.urls import reverse

from report.utils import filter_period


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



def report_objectlogchange_html(report):
    queryset = get_queryset(report)
    object_list=resume_queryset(queryset)

    table =f'<thead><tr><th>{_("User")}</th><th>{_("Laboratory")}</th>' \
           f'<th>{_("Object")}</th><th>{_("Day")}</th><th>{_("Old")}</th>' \
           f'<th>{_("New")}</th><th>{_("Difference")}</th>'\
           f'<th>{_("Unit")}</th></tr></thead>'

    table+="<tbody>"
    for obj in object_list:

        table+=f'<tr><td>{obj.user}</td><td>{str(obj.laboratory)}</td>' \
               f'<td>{str(obj.object)}</td><td>{obj.update_time.strftime("%m/%d/%Y, %H:%M:%S")}</td>' \
               f'<td>{obj.old_value}</td><td>{obj.new_value}</td>' \
               f'<td>{obj.diff_value}</td><td>{str(obj.measurement_unit)}</td></tr>'
    table+='</tbody>'
    report.table_content = table
    report.status = _('Generated')
    report.save()

def report_objectlogchange_pdf(report):

    report_objectlogchange_html(report)
    context = {
        'datalist': report.table_content,
        'laboratory': report.data['lab_pk'],
        'user': report.creator,
    }

    html = render_to_string('report/base_report_pdf.html', context=context)
    file = BytesIO()

    HTML(string=html, encoding='utf-8').write_pdf(file)

    file_name = f'{report.data["name"]}.pdf'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.status = _('Generated')
    report.save()
    file.close()

def report_objectlogchange_doc(report):
    queryset = get_queryset(report)
    object_list=resume_queryset(queryset)
    content = []
    builder = ExcelGraphBuilder()
    content.append([
        _("User"), _("Laboratory"), _("Object"), _("Day"), _('Old'),
        _('New'),_("Difference"),_("Unit")
    ])


    for obj in object_list:
        content.append([obj.user,
                        str(obj.laboratory),
                        str(obj.object),
                        obj.update_time.strftime("%m/%d/%Y, %H:%M:%S"),
                        obj.old_value,
                        obj.new_value,
                        obj.diff_value,
                        str(obj.measurement_unit)
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

def report_reactive_precursor_doc(report):

    lab = report.data['laboratory']
    builder = None

    content = []
    builder = ExcelGraphBuilder()
    content.append([
        _("Code"), _("Name"), _("Type"), _("Quantity total"), _('Measurement units'), _("Molecular formula"),
        _("CAS id number"),
        _("Is precursor?"),
        _("IMDG type")
    ])
    if len(lab)>1:
        content[0].insert(0,_('Laboratory'))
    for lab_pk in lab:
        if lab:
            rpo = Object.objects.filter(
                shelfobject__shelf__furniture__labroom__laboratory__pk=lab_pk)
        else:
            rpo = Object.objects.all()

        rpo = rpo.filter(type=Object.REACTIVE, sustancecharacteristics__is_precursor=True)
        laboratory = Laboratory.objects.filter(pk=lab_pk).first()

        objects = rpo.annotate(quantity_total=Sum('shelfobject__quantity'),
                                   measurement_unit=Min('shelfobject__measurement_unit'))

        for object in objects:
            obj_info = [
            ]
            if len(lab)>1:
                content.append([laboratory.name,
                                object.code,
                                object.name,
                                object.get_type_display(),
                                object.quantity_total,
                                ShelfObject.get_units(object.measurement_unit),
                                str(get_molecular_formula(object)),
                                str(get_cas(object, '')),
                                _("Yes") if object.is_precursor else "No",
                                str(get_imdg(object, ''))
                                ])
            else:
                content.append([object.code,
                                object.name,
                                object.get_type_display(),
                                object.quantity_total,
                                ShelfObject.get_units(object.measurement_unit),
                                str(get_molecular_formula(object)),
                                str(get_cas(object, '')),
                                _("Yes") if object.is_precursor else "No",
                                str(get_imdg(object, ''))
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

def report_reactive_precursor_html(report):

    lab = report.data['laboratory']
    builder =None
    org = True if len(lab)>1 else False

    table = f'<thead><tr>{"<th>"+_("Laboratory")+"</th>" if org else "" }<th>{_("Code")}</th><th>{_("Name")}</th><th>{_("Type")}</th>' \
            f'<th>{_("Quantity total")}</th><th>{_("Measurement units")}</th><th>{_("Molecular formula")}</th>' \
            f'<th>{_("CAS id number")}</th><th>{("Is precursor?")}</th><th>{("IMDG type")}</th></tr></thead>'
    table+='<tbody>'
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
            table += f'<tr>{"<td>"+laboratory.name+"</td>" if org else "" }<td>{object.code}</td><td>{object.name}</td><td>{object.get_type_display()}</td><td>{object.quantity_total}</td>' \
                     f'<td>{ShelfObject.get_units(object.measurement_unit)}</td><td>{str(get_molecular_formula(object))}</td><td>{str(get_cas(object, ""))}</td>' \
                     f'<td>{precursor}</td><td>{str(get_imdg(object, ""))}</td></tr>'
    table+='</tbody>'
    report.table_content = table
    report.status = _('Generated')
    report.save()
    return rpo

def report_reactive_precursor_pdf(report):

    report_reactive_precursor_html(report)
    context = {
        'datalist': report.table_content,
        'laboratory': report.data['laboratory'],
        'user': report.creator,
    }

    html = render_to_string('laboratory/reports/reactive_precursor_pdf.html', context=context)
    file = BytesIO()

    HTML(string=html, encoding='utf-8').write_pdf(file)

    file_name = f'{report.data["name"]}.pdf'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.status = _('Generated')
    report.save()
    file.close()


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

def report_objects_html(report):
    org = report.data['organization']
    labs = report.data['laboratory']
    general = True if 'all_labs_org' in report.data else False
    filters = {}

    type_id = report.data['object_type']
    filters['organization__in'] = get_pk_org_ancestors(org)
    filters['is_public'] = True
    filters['type'] = type_id

    objects = Object.objects.filter(**filters)
    table = f'<thead><tr>{"<th>" + _("Laboratory") + "</th>" if general else ""}<th>{_("Code")}</th><th>{_("Name")}</th><th>{_("Type")}</th>' \
            f'<th>{_("Features")}</th><th>{_("Danger indication")}</th><th>{_("Quantity")}</th>' \
            f'<th>{_("Molecular formula")}</th><th>{_("CAS ID Number")}</th><th>{_("Action")}</th></tr></thead>'
    table += '<tbody>'
    for lab_pk in labs:
        lab = Laboratory.objects.filter(pk=lab_pk).first()
        for obj in objects:
            formula="-"
            features,danger,shelfobjects = get_object_elements(obj)
            url = reverse("laboratory:reports_objects",kwargs={"lab_pk":lab_pk, "org_pk":org})

            if hasattr(obj, 'sustancecharacteristics'):
                formula = obj.sustancecharacteristics.molecular_formula if obj.sustancecharacteristics.molecular_formula else '-'
            cas = get_cas(obj, "") if get_cas(obj, "") else ""
            table += f'<tr>{"<td>" + lab.name + "</td>" if general else ""}<td>{obj.code}</td><td>{obj.name}</td><td>{obj.get_type_display()}</td><td>{features}</td>' \
                     f'<td>{danger}</td><td>{shelfobjects}</td><td>{ formula }</td>' \
                     f'<td>{cas}</td>' \
                     f'<td><a class="btn btn-sm btn-danger float-end" title="{{ obj.name }}"href="{url}?pk={ obj.pk }">' \
                     f'<i class="fa fa-download" aria-hidden="true"></i> PDF </a></td></tr>'
    table += '</tbody>'
    report.table_content = table
    report.status = _('Generated')
    report.save()

def report_objects_pdf(report):
    org = report.data['organization']
    labs = report.data['laboratory']
    general = True if 'all_labs_org' in report.data else False
    filters = {}

    type_id = report.data['object_type']
    filters['organization__in'] = get_pk_org_ancestors(org)
    filters['is_public'] = True
    filters['type'] = type_id

    objects = Object.objects.filter(**filters)
    table = f'<thead><tr>{"<th>" + _("Laboratory") + "</th>" if general else ""}<th>{_("Code")}</th><th>{_("Name")}</th><th>{_("Type")}</th>' \
            f'<th>{_("Features")}</th><th>{_("Danger indication")}</th><th>{_("Quantity")}</th>' \
            f'<th>{_("Molecular formula")}</th><th>{_("CAS ID Number")}</th></tr></thead>'
    table += '<tbody>'

    for lab_pk in labs:
        lab = Laboratory.objects.filter(pk=lab_pk).first()
        for obj in objects:
            formula="-"
            features,danger,shelfobjects = get_object_elements(obj)
            cas = get_cas(obj,"") if get_cas(obj,"") else ""
            if hasattr(obj, 'sustancecharacteristics'):
                formula = obj.sustancecharacteristics.molecular_formula if obj.sustancecharacteristics.molecular_formula else '-'
            table += f'<tr>{"<td>" + lab.name + "</td>" if general else ""}<td>{obj.code}</td><td>{obj.name}</td><td>{obj.get_type_display()}</td><td>{features}</td>' \
                     f'<td>{danger}</td><td>{shelfobjects}</td><td>{ formula }</td>' \
                     f'<td>{ cas }</td></tr>'
    table += '</tbody>'
    context = {
        'datalist': table,
        'laboratory': report.data['laboratory'],
        'user': report.creator,
    }
    report.table_content = table
    html = render_to_string('laboratory/reports/reactive_precursor_pdf.html', context=context)
    file = BytesIO()

    HTML(string=html, encoding='utf-8').write_pdf(file)

    file_name = f'{report.data["name"]}.pdf'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.status = _('Generated')
    report.save()
    file.close()


def report_object_doc(report):
    org = report.data['organization']
    labs = report.data['laboratory']
    filters = {}

    type_id = report.data['object_type']
    filters['organization__in'] = get_pk_org_ancestors(org)
    filters['is_public'] = True
    filters['type'] = type_id
    objects = Object.objects.filter(**filters)
    content = []
    builder = ExcelGraphBuilder()
    content.append([
        _("Code"), _("Name"), _("Type"), _("Features"), _('Danger indication'),
        _('Quantity'),_("Molecular formula"),_("CAS id number")
    ])
    if len(labs)>1:
        content[0].insert(0,_('Laboratory'))

    for lab_pk in labs:
        lab = Laboratory.objects.filter(pk=lab_pk).first()

        for obj in objects:
            formula = "-"
            features, danger, shelfobjects = get_object_elements(obj)

            if hasattr(obj, 'sustancecharacteristics'):
                formula = obj.sustancecharacteristics.molecular_formula if obj.sustancecharacteristics.molecular_formula else '-'
            cas = get_cas(obj, '') if get_cas(obj,"") else ""
            if len(labs)>1:
                content.append([lab.name,
                                obj.code,
                                obj.name,
                                obj.get_type_display(),
                                features,
                                danger,
                                shelfobjects,
                                formula,
                                cas
                                ])
            else:
                content.append([obj.code,
                                obj.name,
                                obj.get_type_display(),
                                features,
                                danger,
                                shelfobjects,
                                formula,
                                cas
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

def get_limited_shelf_objects(query):
    for shelf_object in query:
        if shelf_object.limit_reached:
            yield shelf_object

def report_limit_object_html(report):

    labs= report.data['laboratory']
    table=f'<thead><tr><th>{_("Shelf")}</th><th>{_("Object")}</th>' \
          f'<th>{_("Quantity")}</th><th>{_("Limit quantity")}</th></tr></thead>'
    table+="<tbody>"
    for lab in labs:
        shelf_objects = ShelfObject.objects.filter(
                    shelf__furniture__labroom__laboratory__pk=lab)

        shelf_objects = get_limited_shelf_objects(shelf_objects)
        for shelfobj in shelf_objects:
            table+=f'<tr><td>{shelfobj.shelf}</td>' \
                   f'<td>{shelfobj.object}</td>' \
                   f'<td>{shelfobj.quantity} {shelfobj.get_measurement_unit_display()}</td>' \
                   f'<td>{shelfobj.limit_quantity} {shelfobj.get_measurement_unit_display()}</td></tr>'

    table += '</tbody>'
    report.table_content = table
    report.status = _('Generated')
    report.save()

def report_limit_object_pdf(report):

    report_limit_object_html(report)
    context = {
        'datalist': report.table_content,
        'laboratory': report.data['laboratory'],
        'user': report.creator,
    }

    html = render_to_string('laboratory/reports/reactive_precursor_pdf.html', context=context)
    file = BytesIO()

    HTML(string=html, encoding='utf-8').write_pdf(file)

    file_name = f'{report.data["name"]}.pdf'
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name)
    report.file = content
    report.status = _('Generated')
    report.save()
    file.close()

def report_limit_object_doc(report):

    labs = report.data['laboratory']

    content = []
    builder = ExcelGraphBuilder()
    content.append([
        _("Shelf"), _("Object"), _("Quantity"), _('Limit quantity')
    ])
    if len(labs)>1:
        content[0].insert(0,_('Laboratory'))

    for lab_pk in labs:
        shelf_objects = ShelfObject.objects.filter(
                shelf__furniture__labroom__laboratory__pk=lab_pk)
        shelf_objects = get_limited_shelf_objects(shelf_objects)
        lab = Laboratory.objects.filter(pk=lab_pk).first()
        for obj in shelf_objects:

            if len(labs)>1:
                content.append([lab.name,
                                str(obj.shelf),
                                str(obj.object),
                                f'{obj.quantity} {obj.get_measurement_unit_display()}',
                                f'{obj.limit_quantity} {obj.get_measurement_unit_display()}'
                                ])
            else:
                content.append([str(obj.shelf),
                                str(obj.object),
                                f'{obj.quantity} {obj.get_measurement_unit_display()}',
                                f'{obj.limit_quantity} {obj.get_measurement_unit_display()}'
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
