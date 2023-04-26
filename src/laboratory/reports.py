from django.core.files.base import ContentFile
from django.db.models import Sum, Min
from django.template.loader import  render_to_string

from laboratory.models import Object, ShelfObject, Laboratory

from laboratory.report_utils import ExcelGraphBuilder
from laboratory.utils import get_cas, get_molecular_formula, get_imdg, get_pk_org_ancestors
from django.utils.translation import gettext as _
from io import BytesIO
from weasyprint import HTML
from django.urls import reverse



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
                                get_molecular_formula(object),
                                get_cas(object, ''),
                                _("Yes") if object.is_precursor else "No",
                                str(get_imdg(object, ''))
                                ])
            else:
                content.append([object.code,
                                object.name,
                                object.get_type_display(),
                                object.quantity_total,
                                ShelfObject.get_units(object.measurement_unit),
                                get_molecular_formula(object),
                                get_cas(object, ''),
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
                     f'<td>{ShelfObject.get_units(object.measurement_unit)}</td><td>{get_molecular_formula(object)}</td><td>{get_cas(object, "")}</td>' \
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
            table += f'<tr>{"<td>" + lab.name + "</td>" if general else ""}<td>{obj.code}</td><td>{obj.name}</td><td>{obj.get_type_display()}</td><td>{features}</td>' \
                     f'<td>{danger}</td><td>{shelfobjects}</td><td>{get_molecular_formula(obj, "")}</td>' \
                     f'<td>{get_cas(obj,"")}</td>' \
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
            url = reverse("laboratory:reports_objects",kwargs={"lab_pk":lab_pk, "org_pk":org})

            if hasattr(obj, 'sustancecharacteristics'):
                formula = obj.sustancecharacteristics.molecular_formula if obj.sustancecharacteristics.molecular_formula else '-'
            table += f'<tr>{"<td>" + lab.name + "</td>" if general else ""}<td>{obj.code}</td><td>{obj.name}</td><td>{obj.get_type_display()}</td><td>{features}</td>' \
                     f'<td>{danger}</td><td>{shelfobjects}</td><td>{get_molecular_formula(obj, "")}</td>' \
                     f'<td>{get_cas(obj,"")}</td></tr>'
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
        for obj in objects:
            lab = Laboratory.objects.filter(pk=lab_pk).first()
            formula = "-"
            features, danger, shelfobjects = get_object_elements(obj)
            url = reverse("laboratory:reports_objects", kwargs={"lab_pk": lab_pk, "org_pk": org})

            if hasattr(obj, 'sustancecharacteristics'):
                formula = obj.sustancecharacteristics.molecular_formula if obj.sustancecharacteristics.molecular_formula else '-'

            if len(labs)>1:
                content.append([lab.name,
                                obj.code,
                                obj.name,
                                obj.get_type_display(),
                                features,
                                danger,
                                shelfobjects,
                                get_molecular_formula(obj, ''),
                                get_cas(obj, '')
                                ])
            else:
                content.append([obj.code,
                                obj.name,
                                obj.get_type_display(),
                                features,
                                danger,
                                shelfobjects,
                                get_molecular_formula(obj, ''),
                                get_cas(obj, '')
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


    org = report.data['organization']
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
        for lab in labs:
            shelf_objects = ShelfObject.objects.filter(
                shelf__furniture__labroom__laboratory__pk=lab_pk)

            shelf_objects = get_limited_shelf_objects(shelf_objects)
        lab = Laboratory.objects.filter(pk=lab_pk).first()
        for obj in shelf_objects:

            if len(labs)>1:
                content.append([lab.name,
                                obj.shelf.__str__(),
                                obj.object.__str__(),
                                f'{obj.quantity} {obj.get_measurement_unit_display()}',
                                f'{obj.limit_quantity} {obj.get_measurement_unit_display()}'
                                ])
            else:
                content.append([obj.shelf.__str__(),
                                obj.object.__str__(),
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
