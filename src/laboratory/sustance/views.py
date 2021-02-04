from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DeleteView
from django_datatables_view.base_datatable_view import BaseDatatableView
from laboratory.models import Object
from laboratory.sustance.forms import SustanceObjectForm, SustanceCharacteristicsForm
from laboratory.utils import get_cas
from laboratory.validators import isValidate_molecular_formula


@permission_required('laboratory.edit_object')
def create_edit_sustance(request, pk=None):
    instance = Object.objects.filter(pk=pk).first()

    suscharobj=None
    if instance:
        suscharobj = instance.sustancecharacteristics
    postdata=None
    filesdata = None
    if request.method == 'POST':
        postdata = request.POST
        filesdata = request.FILES
    objform = SustanceObjectForm(postdata, instance=instance)
    suschacform = SustanceCharacteristicsForm(postdata, files=filesdata, instance=suscharobj)
    if request.method == 'POST':
        if objform.is_valid() and suschacform.is_valid():
            obj = objform.save(commit=False)
            obj.type = Object.REACTIVE
            obj.save()
            objform.save_m2m()
            suscharinst = suschacform.save(commit=False)
            suscharinst.obj = obj

            molecular_formula = suschacform.cleaned_data["molecular_formula"]
            if isValidate_molecular_formula(molecular_formula):
                suscharinst.valid_molecular_formula = True

            suscharinst.save()
            suschacform.save_m2m()
            messages.success(request, _("Sustance saved successfully"))
            return redirect(reverse('laboratory:sustance_list'))

        else:
            messages.warning(request, _("Pending information in form"))

    return render(request, 'laboratory/sustance/sustance_form.html', {
        'objform': objform,
        'suschacform': suschacform,
        'instance': instance
    })


@permission_required('laboratory.view_object')
def sustance_list(request):
    #object_list = Object.objects.filter(type=Object.REACTIVE)
    return render(request, 'laboratory/sustance/list.html', {
        'object_url': '#'
    })


@method_decorator(permission_required('laboratory.delete_object'), name='dispatch')
class SubstanceDelete(DeleteView):
    model = Object
    success_url = reverse_lazy('laboratory:sustance_list')
    template_name = 'laboratory/sustance/substance_deleteview.html'


@method_decorator(permission_required('laboratory.view_object'), name='dispatch')
class SustanceListJson(BaseDatatableView):
    model = Object
    columns = ['id','name','cas_code','action']
    max_display_length = 500

    def filter_queryset(self, qs):
        qs = qs.filter(type=Object.REACTIVE)
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(code__istartswith=search) |
                Q(name__istartswith=search) |
                Q(sustancecharacteristics__cas_id_number__istartswith=search) |
                Q(synonym__icontains=search)
         )
        # Delete duplicates from queryset
        return qs.distinct()

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            is_bioaccumulable = hasattr(item, 'sustancecharacteristics')\
                and item.sustancecharacteristics and item.sustancecharacteristics.bioaccumulable
            is_precursor = hasattr(item, 'sustancecharacteristics')\
                and item.sustancecharacteristics and item.sustancecharacteristics.is_precursor


            warning_precursor = 'fa fa-check-circle fa-fw text-success' if is_precursor else  \
                'fa fa-times-circle fa-fw text-warning'
            warning_bioaccumulable = 'fa fa-leaf fa-fw text-success' if is_bioaccumulable else \
                'fa fa-flask text-warning'
            warning_is_public = 'fa fa-users fa-fw text-success' if item.is_public \
                else 'fa fa-user-times fa-fw text-warning'

            precursor = '<i class="{0}" title="{1} {2}"></i>'.format(warning_precursor, _('Is precursor?'),
                                                                     _("Yes") if is_precursor else _("No") )
            bioaccumulable = '<i class="{0}" title="{1} {2}"></i>'.format(warning_bioaccumulable,
                            _('Is bioaccumulable?'), _("Yes") if is_bioaccumulable else _("No"))
            is_public = '<i class="{0}"  title="{1} {2}" aria-hidden="true"></i>'.format(
                warning_is_public, _('Is public?'), _("Yes") if item.is_public else _("No"))
            name_url = """<a href="{0}" title="{1}">{2}</a>""".format(
                reverse('laboratory:sustance_manage', kwargs={'pk': item.id}),
                item.synonym or item.name, item.name)
            delete = """<a href="{0}" title="{1}" class="pull-right"><i class="fa fa-trash-o" style="color:red"></i></a>"""\
                .format(reverse('laboratory:sustance_delete',
                                kwargs={'pk': item.id}), _('Delete sustance'))
            if hasattr(item, 'sustancecharacteristics') and item.sustancecharacteristics and \
                    item.sustancecharacteristics.security_sheet:
                download = """<a href="{0}" title="{1}"><i class="fa fa-download" ></i></a>""" \
                    .format(item.sustancecharacteristics.security_sheet.url, _("Download security sheet"))
                delete = download+delete

            json_data.append([
                is_public+precursor+bioaccumulable,
                name_url,
                get_cas(item, ''),
                delete
            ])
        return json_data
