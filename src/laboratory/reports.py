from django.core.files.base import ContentFile
from django.db.models import Sum, Min
from django.template.loader import  render_to_string

from laboratory.models import TaskReport, Object, CLInventory, ShelfObject
from laboratory.report_utils import ExcelGraphBuilder
from laboratory.utils import get_cas, get_molecular_formula, get_imdg
from django.utils.translation import gettext as _
from io import BytesIO
from weasyprint import HTML


def report_reactive_precursor_objects(report):
    lab = report.data['laboratory']
    builder =None
    if lab:
        rpo = Object.objects.filter(
            shelfobject__shelf__furniture__labroom__laboratory__pk__in=lab)
    else:
        rpo = Object.objects.all()

    rpo = rpo.filter(type=Object.REACTIVE, sustancecharacteristics__is_precursor=True)

    for obj in rpo:
        clentry = CLInventory.objects.filter(
            cas_id_number=get_cas(obj, 0)).first()
        setattr(obj, 'clinventory_entry', clentry)
    content = []
    fileformat = "xlsx"
    builder = ExcelGraphBuilder()

    if fileformat in ['xls', 'xlsx', 'ods']:
        content.append([
            _("Code"), _("Name"), _("Type"), _("Quantity total"), _('Measurement units'),_("Molecular formula"),
                _("CAS id number"),
                _("Is precursor?"),
                _("IMDG type")
            ])
        objects = rpo.annotate(quantity_total=Sum('shelfobject__quantity'),
                                   measurement_unit=Min('shelfobject__measurement_unit'))

        for object in objects:
            obj_info = [
                object.code,
                object.name,
                object.get_type_display(),
                object.quantity_total,
                ShelfObject.get_units(object.measurement_unit)]

            obj_info += [
                    get_molecular_formula(object),
                    get_cas(object, ''),
                    _("Yes") if object.is_precursor else "No",
                    str(get_imdg(object, ''))]

            content.append(obj_info)

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

def report_reactive_precursor_objects_html(report):
    lab = report.data['laboratory']
    builder =None
    if lab:
        rpo = Object.objects.filter(
            shelfobject__shelf__furniture__labroom__laboratory__pk__in=lab)
    else:
        rpo = Object.objects.all()

    rpo = rpo.filter(type=Object.REACTIVE, sustancecharacteristics__is_precursor=True)

    table = f'<thead><tr><th>{_("Code")}</th><th>{_("Name")}</th><th>{_("Type")}</th>' \
            f'<th>{_("Quantity total")}</th><th>{_("Measurement units")}</th><th>{_("Molecular formula")}</th>' \
            f'<th>{_("CAS id number")}</th><th>{("Is precursor?")}</th><th>{("IMDG type")}</th></tr></thead>'
    objects = rpo.annotate(quantity_total=Sum('shelfobject__quantity'),
                           measurement_unit=Min('shelfobject__measurement_unit'))
    table+='<tbody>'
    for object in objects:
        precursor = _('Yes') if object.is_precursor else 'No'
        table += f'<tr><td>{object.code}</td><td>{object.name}</td><td>{object.get_type_display()}</td><td>{object.quantity_total}</td>' \
                 f'<td>{ShelfObject.get_units(object.measurement_unit)}</td><td>{get_molecular_formula(object)}</td><td>{get_cas(object, "")}</td>' \
                 f'<td>{precursor}</td><td>{str(get_imdg(object, ""))}</td></tr>'
    table+='</tbody>'
    report.table_content = table
    report.status = _('Generated')
    report.save()
    return rpo
def report_reactive_precursor_objects_pdf(report):

    report_reactive_precursor_objects_html(report)
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

