from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from laboratory.views.djgeneric import DeleteView
from django_datatables_view.base_datatable_view import BaseDatatableView
from laboratory.models import Object, Laboratory, OrganizationStructure
from laboratory.sustance.forms import SustanceObjectForm, SustanceCharacteristicsForm
from laboratory.utils import get_cas, organilab_logentry, get_pk_org_ancestors, \
    get_pk_org_ancestors_decendants
from laboratory.validators import isValidate_molecular_formula


@permission_required('laboratory.change_object')
def create_edit_sustance(request, org_pk, lab_pk, pk=None):
    organization = get_object_or_404(OrganizationStructure, pk=org_pk)
    instance = Object.objects.filter(pk=pk).first()
    laboratory = get_object_or_404(Laboratory, pk=lab_pk)
    suscharobj=None
    if instance:
        suscharobj = instance.sustancecharacteristics
    postdata=None
    filesdata = None
    if request.method == 'POST':
        postdata = request.POST
        filesdata = request.FILES

    objform = SustanceObjectForm(postdata, instance=instance)#, org_pk=org_pk)
    suschacform = SustanceCharacteristicsForm(postdata, files=filesdata, instance=suscharobj)
    if request.method == 'POST':
        if objform.is_valid() and suschacform.is_valid():
            obj = objform.save(commit=False)
            obj.type = Object.REACTIVE
            obj.organization = organization
            obj.save()
            objform.save_m2m()
            suscharinst = suschacform.save(commit=False)
            suscharinst.obj = obj

            molecular_formula = suschacform.cleaned_data["molecular_formula"]
            if isValidate_molecular_formula(molecular_formula):
                suscharinst.valid_molecular_formula = True

            suscharinst.save()
            suschacform.save_m2m()
            action = ADDITION
            if pk:
                action = CHANGE
            organilab_logentry(request.user, obj, action, 'object', changed_data=objform.changed_data, relobj=laboratory)
            organilab_logentry(request.user, suscharinst, action, 'sustance characteristics',
                               changed_data=suschacform.changed_data, relobj=laboratory)

            messages.success(request, _("Sustance saved successfully"))
            return redirect(reverse('laboratory:sustance_list',args=[org_pk, lab_pk]))

        else:
            messages.warning(request, _("Pending information in form"))

    return render(request, 'laboratory/sustance/sustance_form.html', {
        'objform': objform,
        'suschacform': suschacform,
        'instance': instance,
        'lab_pk': lab_pk,
        'org_pk':org_pk
    })


@permission_required('laboratory.view_object')
def sustance_list(request, org_pk, lab_pk):
    #object_list = Object.objects.filter(type=Object.REACTIVE)
    if request.method == 'POST':
        lab_pk = request.POST.get('lab_pk')
    return render(request, 'laboratory/sustance/list.html', {
        'object_url': '#',
        'laboratory': lab_pk,
        'org_pk': org_pk,
    })


@method_decorator(permission_required('laboratory.delete_object'), name='dispatch')
class SubstanceDelete(DeleteView):
    model = Object
    template_name = 'laboratory/sustance/substance_deleteview.html'

    def get_success_url(self, **kwargs):
        lab_pk = self.kwargs['lab_pk']
        success_url = reverse_lazy('laboratory:sustance_list', kwargs={'org_pk':self.org, 'lab_pk':lab_pk,})
        return success_url

    def form_valid(self, form):
        success_url = self.get_success_url()
        organilab_logentry(self.request.user, self.object, DELETION, relobj=self.kwargs['lab_pk'])
        self.object.delete()
        return HttpResponseRedirect(success_url)

@method_decorator(permission_required('laboratory.view_object'), name='dispatch')
class SustanceListJson(BaseDatatableView):
    model = Object
    columns = ['id','name','cas_code','action']
    max_display_length = 500
    lab_pk_field ='pk'

    def filter_queryset(self, qs):
        org_pk = self.kwargs['org_pk']
        filters = (Q(organization__in=get_pk_org_ancestors_decendants(self.request.user,
                                                                      org_pk),
                     is_public=True)
                   | Q(organization__pk=org_pk, is_public=False))
        qs = qs.filter(filters).filter(type=Object.REACTIVE)
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

            action_buttons = """<a href="{0}" title="{1}"><i class="fa fa-edit fa-fw text-warning"></i></a>"""\
                .format(reverse('laboratory:sustance_manage',
                                kwargs={'pk': item.id,'lab_pk':self.kwargs['lab_pk'], 'org_pk':self.kwargs['org_pk']}), _('Edit substance'))

            action_buttons += """<a href="{0}" title="{1}" class="float-end"><i class="fa fa-trash-o" style="color:red"></i></a>"""\
                .format(reverse('laboratory:sustance_delete',
                                kwargs={'pk': item.id, 'lab_pk':self.kwargs['lab_pk'], 'org_pk':self.kwargs['org_pk']}), _('Delete substance'))
            if hasattr(item, 'sustancecharacteristics') and item.sustancecharacteristics and \
                    item.sustancecharacteristics.security_sheet:
                download = """<a href="{0}" title="{1}"><i class="fa fa-download" ></i></a>""" \
                    .format(item.sustancecharacteristics.security_sheet.url, _("Download security sheet"))
                action_buttons = download + action_buttons

            json_data.append([
                is_public+precursor+bioaccumulable,
                item.name,
                get_cas(item, ''),
                action_buttons
            ])
        return json_data
