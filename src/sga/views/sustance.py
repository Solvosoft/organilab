from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from academic.models import SubstanceObservation
from academic.substance.forms import ObservacionForm, SecurityLeafForm
from academic.substance.forms import SustanceObjectForm, SustanceCharacteristicsForm, ReviewSubstanceForm
from laboratory.models import OrganizationStructure
from laboratory.utils import organilab_logentry
from sga.forms import BuilderInformationForm, SGAComplementsForm, ProviderSGAForm, PersonalSGAAddForm, \
    PersonalEditorForm
from sga.models import Substance, PersonalTemplateSGA, SGAComplement, \
    SecurityLeaf
from sga.models import SubstanceCharacteristics, \
    TemplateSGA, Label, ReviewSubstance


@login_required
@permission_required('laboratory.change_object')
def create_edit_sustance(request, org_pk, pk=None):
    instance = None
    organization = get_object_or_404(OrganizationStructure, pk=org_pk)

    if pk:
        instance = Substance.objects.filter(pk=pk, organization=organization).first()

    suscharobj=None
    template = None

    if instance:
        suscharobj = instance.substancecharacteristics

    postdata=None
    filesdata = None

    if request.method == 'POST':
        postdata = request.POST

    objform = SustanceObjectForm(postdata, instance=instance)
    suschacform = SustanceCharacteristicsForm(postdata, instance=suscharobj)

    if request.method == 'POST':

        if objform.is_valid() and suschacform.is_valid():
            obj = objform.save(commit=False)
            obj.creator=request.user
            obj.creator=request.user
            obj.save()
            objform.save_m2m()
            suscharinst = suschacform.save(commit=False)
            suscharinst.substance = obj
            label, created= Label.objects.get_or_create(substance= obj)
            complement, complement_created= SGAComplement.objects.get_or_create(substance= obj)
            leaf, leaf_created= SecurityLeaf.objects.get_or_create(substance= obj)
            template= TemplateSGA.objects.filter(is_default=True).first()
            personal,created = PersonalTemplateSGA.objects.get_or_create(label=label, template=template, user=request.user)

            molecular_formula = suschacform.cleaned_data["molecular_formula"]
            #if isValidate_molecular_formula(molecular_formula):
            # #suscharinst.valid_molecular_formula = True

            suscharinst.save()
            suschacform.save_m2m()
            organilab_logentry(request.user, obj, CHANGE, "substance", changed_data=objform.changed_data)
            organilab_logentry(request.user, suscharinst, CHANGE, "substance characteristics", changed_data=suschacform.changed_data)

            return redirect(reverse('academic:step_two', kwargs={'org_pk': org_pk, 'pk':complement.pk}))

    elif instance is None and request.method == 'GET':
        substance = Substance.objects.create(creator=request.user, organization=organization)
        rev_sub = ReviewSubstance.objects.create(substance=substance)
        charac = SubstanceCharacteristics.objects.create(substance=substance)
        organilab_logentry(request.user, substance, ADDITION, "substance")
        organilab_logentry(request.user, charac, ADDITION, "substance characteristics")
        organilab_logentry(request.user, rev_sub, ADDITION, "review substance", changed_data=['substance'])
        return redirect(reverse('academic:step_one', kwargs={'org_pk': org_pk, 'pk': substance.pk}))

    label, created_label= Label.objects.get_or_create(substance= instance)
    template= TemplateSGA.objects.get(is_default=True)
    personal, created = PersonalTemplateSGA.objects.get_or_create(label=label, template=template, user= request.user)
    complement, sga_created = SGAComplement.objects.get_or_create(substance=instance)
    leaf, leaf_created = SecurityLeaf.objects.get_or_create(substance=instance)

    return render(request, 'academic/substance/create_sustance.html', {
        'objform': objform,
        'suschacform': suschacform,
        'instance': instance,
        'step':1,
        'template':personal.pk,
        'substance':instance.pk,
        'complement':complement.pk,
        'pk':instance.pk,
        'org_pk': org_pk
    })

@login_required
@permission_required('sga.view_substance')
def get_substances(request, org_pk):
    substances=None

    if request.user:
        substances = Substance.objects.filter(creator=request.user)
    if substances:
        substances = substances.filter(organization__pk=org_pk)
    context = {
        'substances':substances,
        'org_pk': org_pk
    }

    return render(request, 'academic/substance/list_substance.html', context=context)

@login_required
@permission_required('sga.view_substance')
def get_list_substances(request, org_pk):
    showapprove = True if request.GET.get('showapprove') else False
    form = ReviewSubstanceForm()
    context = {
        'form':form,
        'org_pk': org_pk,
        'showapprove': showapprove
    }
    return render(request, 'academic/substance/check_substances.html', context=context)

@login_required
@permission_required('sga.change_substance')
def approve_substances(request, org_pk, pk):
    review_subs = get_object_or_404(ReviewSubstance, pk=pk)
    review_subs.is_approved=True
    review_subs.save()
    organilab_logentry(request.user, review_subs, CHANGE, "review substance", changed_data=['is_approved'])
    return redirect(reverse('academic:approved_substance', kwargs={'org_pk':org_pk}))

@login_required
@permission_required('sga.delete_substance')
def delete_substance(request, org_pk, pk):
    substances=Substance.objects.filter(pk=pk).first()
    if substances:
        messages.success(request, _("The substance is removed successfully"))
        organilab_logentry(request.user, substances, DELETION, "substance")
        Label.objects.filter(substance=substances).delete()
        substances.delete()
        return redirect(reverse("academic:get_substance", kwargs={'org_pk': org_pk}))
    return redirect(reverse("academic:get_substance", kwargs={'org_pk': org_pk}))

@login_required
@permission_required('sga.change_substance')
def detail_substance(request, org_pk, pk):
    detail = None
    observation = None
    step = 1
    if 'step' in request.session:
        step=request.session['step']
        del request.session['step']

    if pk:
        detail = get_object_or_404(Substance, pk=int(pk))
        observation = SubstanceObservation.objects.filter(substance =detail)
    context = {
        'object':detail,
        'observations': observation,
        'observationForm':ObservacionForm(),
        'step':step,
        'url': reverse('academic:add_observation',kwargs={'org_pk': org_pk, 'substance':pk}),
        'org_pk': org_pk
    }
    return render(request, "academic/substance/detail.html", context=context)

@login_required
@permission_required('sga.change_sgacomplement')
def step_two(request, org_pk, pk):
    complement = get_object_or_404(SGAComplement, pk=pk)
    personaltemplateSGA = PersonalTemplateSGA.objects.filter(user=request.user,
        label__substance__pk=complement.substance.pk).first()
    context ={}
    if request.method == 'POST':
        pesonalform = PersonalSGAAddForm(request.POST, request.FILES, instance=personaltemplateSGA)
        complementform = SGAComplementsForm(request.POST, instance=complement)
        builderinformationform=BuilderInformationForm(request.POST, instance=personaltemplateSGA.label.builderInformation)
        complementform_ok = complementform.is_valid()
        builderinformationform_ok = builderinformationform.is_valid()
        pesonalform_ok = pesonalform.is_valid()

        if complementform_ok:
            obj = complementform.save()
            organilab_logentry(request.user, obj, CHANGE, "sga complement", changed_data=complementform.changed_data)

        if builderinformationform_ok:
            instance = builderinformationform.save()
            organilab_logentry(request.user, instance, CHANGE, "builder information", changed_data=builderinformationform.changed_data)

            if personaltemplateSGA.label.builderInformation is None:
                personaltemplateSGA.label.builderInformation = instance
                personaltemplateSGA.label.save()

        if pesonalform_ok:
            personal_obj = pesonalform.save()
            organilab_logentry(request.user, personal_obj, CHANGE, "personal template sga",
                               changed_data=pesonalform.changed_data)

        if complementform_ok and builderinformationform_ok and pesonalform_ok:
            return redirect(reverse('academic:step_three', kwargs={'template': personaltemplateSGA.pk,
                                                          'substance': personaltemplateSGA.label.substance.pk,
                                                          'org_pk': org_pk}))
        else:
            messages.error(request, _("Invalid form"))
            context = {
                'form': SGAComplementsForm(instance=complement),
                'builderinformationform': builderinformationform,
                'pesonalform': pesonalform,
                'step': 2,
                'template': personaltemplateSGA.pk,
                'complement': complement.pk,
                'substance': complement.substance.pk,
                'org_pk': org_pk
            }
            return render(request, 'academic/substance/step_two.html', context)
    context = {
        'form': SGAComplementsForm(instance=complement),
        'builderinformationform': BuilderInformationForm(instance=personaltemplateSGA.label.builderInformation),
        'pesonalform': PersonalSGAAddForm(instance=personaltemplateSGA),
        'step': 2,
        'complement': complement.pk,
        'template': personaltemplateSGA.pk,
        'substance': complement.substance.pk,
        'org_pk': org_pk
    }
    return render(request, 'academic/substance/step_two.html', context)

@login_required
@permission_required('sga.change_personaltemplatesga')
def step_three(request, org_pk, template, substance):
    personaltemplateSGA = get_object_or_404(PersonalTemplateSGA, pk=template)
    complement = get_object_or_404(SGAComplement, substance__pk=substance)
    user = request.user

    if request.method == 'POST':
        form = PersonalEditorForm(request.POST, instance=personaltemplateSGA)
        if form.is_valid():
            obj = form.save()
            organilab_logentry(user, obj, CHANGE, "Personas template sga", changed_data=form.changed_data)
            return redirect(reverse('academic:step_four', kwargs={
                                                          'substance': personaltemplateSGA.label.substance.pk,
                                                         'org_pk': org_pk}))

    initial = {'name': personaltemplateSGA.name, 'template': personaltemplateSGA.template,
               'barcode': personaltemplateSGA.barcode, 'json_representation': personaltemplateSGA.json_representation}

    if personaltemplateSGA.label:
        bi_info = personaltemplateSGA.label.builderInformation
        initial.update({'substance': personaltemplateSGA.label.substance.pk,
            'commercial_information':
                personaltemplateSGA.label.builderInformation.commercial_information if personaltemplateSGA.label.builderInformation else ''})

        if bi_info:
            initial.update({'company_name': bi_info.name,
                            'phone': bi_info.phone,
                            'address': bi_info.address})

    context={
        'editorform': PersonalEditorForm(initial=initial, instance=personaltemplateSGA),
        "instance": personaltemplateSGA,
        "sgalabel": personaltemplateSGA,
        'complement': complement.pk,
        'sga_elements': complement,
        'step': 3,
        'templateinstance': personaltemplateSGA.template,
        'template': personaltemplateSGA.pk,
        'label': personaltemplateSGA.label,
        'substance': personaltemplateSGA.label.substance.pk,
        'org_pk': org_pk
    }
    return render(request, 'academic/substance/step_three.html', context)

@login_required
@permission_required('sga.change_securityleaf')
def step_four(request, org_pk,  substance):
    security_leaf = get_object_or_404(SecurityLeaf, substance__pk=substance)
    personaltemplateSGA = PersonalTemplateSGA.objects.filter(label__substance__pk=substance).first()
    complement = SGAComplement.objects.filter(substance__pk=substance).first()
    context = {}
    if request.method == 'POST':
        form = SecurityLeafForm(request.POST, instance=security_leaf)
        if form.is_valid():
            obj = form.save()
            organilab_logentry(request.user, obj, CHANGE, "security leaf", changed_data=form.changed_data)
            return redirect(reverse('academic:get_substance',kwargs={'org_pk': org_pk }))

    form = SecurityLeafForm(instance=security_leaf)
    context = {'step': 4,
               'complement': complement.pk,
               'template': personaltemplateSGA.pk,
               'form':form,
               'provider_form': ProviderSGAForm(),
               'substance': substance,
               'org_pk': org_pk
               }
    return render(request,'academic/substance/step_four.html',context=context)
