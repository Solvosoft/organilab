from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE
from django.contrib.auth.decorators import permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from laboratory.models import Object, Laboratory, OrganizationStructure
from laboratory.sustance.forms import SustanceObjectForm, SustanceCharacteristicsForm
from laboratory.utils import organilab_logentry
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

