from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import permission_required, login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import get_template
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from weasyprint import HTML

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import OrganizationStructure
from laboratory.utils import organilab_logentry
from sga.forms import BuilderInformationForm, SGAComplementsForm, ProviderSGAForm, \
    PersonalSGAAddForm, \
    PersonalEditorForm
from sga.models import Substance, DisplayLabel, SGAComplement, \
    SecurityLeaf
from sga.models import SubstanceCharacteristics, \
    TemplateSGA, Label, ReviewSubstance
from sga.models import SubstanceObservation
from sga.models import WarningWord, DangerIndication, PrudenceAdvice
from .forms import DangerIndicationForm, \
    WarningWordForm, PrudenceAdviceForm
from .forms import ObservationForm, SecurityLeafForm, SustanceObjectForm, \
    SustanceCharacteristicsForm, \
    ReviewSubstanceForm


@login_required
@permission_required('laboratory.change_object')
def create_edit_sustance(request, org_pk, pk=None):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    instance = None
    suscharobj = None
    postdata = None

    if pk:
        instance = Substance.objects.filter(pk=pk, organization=organization).first()

    if instance:
        suscharobj = instance.substancecharacteristics

    if request.method == 'POST':
        postdata = request.POST

    objform = SustanceObjectForm(postdata, instance=instance)
    suschacform = SustanceCharacteristicsForm(postdata, instance=suscharobj)

    if request.method == 'POST':

        if objform.is_valid() and suschacform.is_valid():
            obj = objform.save(commit=False)
            obj.created_by = request.user
            obj.save()
            objform.save_m2m()
            suscharinst = suschacform.save(commit=False)
            suscharinst.substance = obj
            label, created = Label.objects.get_or_create(substance=obj)
            complement, complement_created = SGAComplement.objects.get_or_create(
                substance=obj)
            leaf, leaf_created = SecurityLeaf.objects.get_or_create(substance=obj)
            template = TemplateSGA.objects.filter(is_default=True).first()
            personal, created = DisplayLabel.objects.get_or_create(label=label,
                                                                          template=template,
                                                                          user=request.user)

            molecular_formula = suschacform.cleaned_data["molecular_formula"]
            # if isValidate_molecular_formula(molecular_formula):
            # #suscharinst.valid_molecular_formula = True

            suscharinst.save()
            suschacform.save_m2m()
            organilab_logentry(request.user, obj, CHANGE, "substance",
                               changed_data=objform.changed_data)
            organilab_logentry(request.user, suscharinst, CHANGE,
                               "substance characteristics",
                               changed_data=suschacform.changed_data)

            return redirect(
                reverse('sga:step_two', kwargs={'org_pk': org_pk, 'pk': complement.pk}))

    elif instance is None and request.method == 'GET':
        substance = Substance.objects.create(created_by=request.user,
                                             organization=organization)
        rev_sub = ReviewSubstance.objects.create(substance=substance)
        charac = SubstanceCharacteristics.objects.create(substance=substance)
        organilab_logentry(request.user, substance, ADDITION, "substance")
        organilab_logentry(request.user, charac, ADDITION, "substance characteristics")
        organilab_logentry(request.user, rev_sub, ADDITION, "review substance",
                           changed_data=['substance'])
        return redirect(
            reverse('sga:step_one', kwargs={'org_pk': org_pk, 'pk': substance.pk}))

    label, created_label = Label.objects.get_or_create(substance=instance)
    template = TemplateSGA.objects.get(is_default=True)
    personal, created = DisplayLabel.objects.get_or_create(label=label,
                                                                  template=template,
                                                                  user=request.user)
    complement, sga_created = SGAComplement.objects.get_or_create(substance=instance)
    leaf, leaf_created = SecurityLeaf.objects.get_or_create(substance=instance)

    return render(request, 'sga/substance/create_sustance.html', {
        'objform': objform,
        'suschacform': suschacform,
        'instance': instance,
        'step': 1,
        'template': personal.pk,
        'substance': instance.pk,
        'complement': complement.pk,
        'pk': instance.pk,
        'org_pk': org_pk
    })


@login_required
@permission_required('sga.view_substance')
def get_substances(request, org_pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    context = {'org_pk': org_pk}
    return render(request, 'sga/substance/list_substance.html', context=context)


@login_required
@permission_required('sga.view_substance')
def get_list_substances(request, org_pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    showapprove = True if request.GET.get('showapprove') else False
    form = ReviewSubstanceForm()
    context = {
        'form': form,
        'org_pk': org_pk,
        'showapprove': showapprove
    }
    return render(request, 'sga/substance/check_substances.html', context=context)


@login_required
@permission_required('sga.change_substance')
def approve_substances(request, org_pk, pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    review_subs = get_object_or_404(ReviewSubstance, pk=pk)
    review_subs.is_approved = True
    review_subs.save()
    organilab_logentry(request.user, review_subs, CHANGE, "review substance",
                       changed_data=['is_approved'])
    return redirect(reverse('sga:approved_substance', kwargs={'org_pk': org_pk}))


@login_required
@permission_required('sga.delete_substance')
def delete_substance(request, org_pk, pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    substances = Substance.objects.filter(pk=pk).first()
    if substances:
        messages.success(request, _("The substance is removed successfully"))
        organilab_logentry(request.user, substances, DELETION, "substance")
        Label.objects.filter(substance=substances).delete()
        substances.delete()
        return redirect(reverse("sga:get_substance", kwargs={'org_pk': org_pk}))
    return redirect(reverse("sga:get_substance", kwargs={'org_pk': org_pk}))


@login_required
@permission_required('sga.change_substance')
def detail_substance(request, org_pk, pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    detail = None
    observation = None
    step = 1
    if 'step' in request.session:
        step = request.session['step']
        del request.session['step']

    if pk:
        detail = get_object_or_404(Substance, pk=int(pk))
        observation = SubstanceObservation.objects.filter(substance=detail)
    context = {
        'object': detail,
        'observations': observation,
        'observationForm': ObservationForm(),
        'step': step,
        'url': reverse('sga:add_observation',
                       kwargs={'org_pk': org_pk, 'substance': pk}),
        'org_pk': org_pk
    }
    return render(request, "sga/substance/detail.html", context=context)


@login_required
@permission_required('sga.change_sgacomplement')
def step_two(request, org_pk, pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    complement = get_object_or_404(SGAComplement, pk=pk)
    display_label = DisplayLabel.objects.filter(user=request.user,
                                                             label__substance__pk=complement.substance.pk).first()
    context = {}
    if request.method == 'POST':
        pesonalform = PersonalSGAAddForm(request.POST, request.FILES,
                                         instance=display_label)
        complementform = SGAComplementsForm(request.POST, instance=complement)
        builderinformationform = BuilderInformationForm(request.POST,
                                                        instance=display_label.label.builderInformation)
        complementform_ok = complementform.is_valid()
        builderinformationform_ok = builderinformationform.is_valid()
        pesonalform_ok = pesonalform.is_valid()

        if complementform_ok:
            obj = complementform.save()
            organilab_logentry(request.user, obj, CHANGE, "sga complement",
                               changed_data=complementform.changed_data)

        if builderinformationform_ok:
            instance = builderinformationform.save()
            organilab_logentry(request.user, instance, CHANGE, "builder information",
                               changed_data=builderinformationform.changed_data)

            if display_label.label.builderInformation is None:
                display_label.label.builderInformation = instance
                display_label.label.save()

        if pesonalform_ok:
            personal_obj = pesonalform.save()
            organilab_logentry(request.user, personal_obj, CHANGE,
                               "personal template sga",
                               changed_data=pesonalform.changed_data)

        if complementform_ok and builderinformationform_ok and pesonalform_ok:
            return redirect(
                reverse('sga:step_three', kwargs={'template': display_label.pk,
                                                  'substance': display_label.label.substance.pk,
                                                  'org_pk': org_pk}))
        else:
            messages.error(request, _("Invalid form"))
            context = {
                'form': SGAComplementsForm(instance=complement),
                'builderinformationform': builderinformationform,
                'pesonalform': pesonalform,
                'step': 2,
                'template': display_label.pk,
                'complement': complement.pk,
                'substance': complement.substance.pk,
                'org_pk': org_pk
            }
            return render(request, 'sga/substance/step_two.html', context)
    context = {
        'form': SGAComplementsForm(instance=complement),
        'builderinformationform': BuilderInformationForm(
            instance=display_label.label.builderInformation),
        'pesonalform': PersonalSGAAddForm(instance=display_label),
        'step': 2,
        'complement': complement.pk,
        'template': display_label.pk,
        'substance': complement.substance.pk,
        'org_pk': org_pk
    }
    return render(request, 'sga/substance/step_two.html', context)


@login_required
@permission_required('sga.change_display_label')
def step_three(request, org_pk, template, substance):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    display_label = get_object_or_404(DisplayLabel, pk=template)
    complement = get_object_or_404(SGAComplement, substance__pk=substance)
    user = request.user

    if request.method == 'POST':
        form = PersonalEditorForm(request.POST, instance=display_label)
        if form.is_valid():
            obj = form.save()
            organilab_logentry(user, obj, CHANGE, "Personas template sga",
                               changed_data=form.changed_data)
            return redirect(reverse('sga:step_four', kwargs={
                'substance': display_label.label.substance.pk,
                'org_pk': org_pk}))

    initial = {'name': display_label.name,
               'template': display_label.template,
               'barcode': display_label.barcode,
               'json_representation': display_label.json_representation}

    if display_label.label:
        bi_info = display_label.label.builderInformation
        initial.update({'substance': display_label.label.substance.pk,
                        'commercial_information':
                            display_label.label.builderInformation.commercial_information if display_label.label.builderInformation else ''})

        if bi_info:
            initial.update({'company_name': bi_info.name,
                            'phone': bi_info.phone,
                            'address': bi_info.address})

    context = {
        'editorform': PersonalEditorForm(initial=initial, instance=display_label),
        "instance": display_label,
        "sgalabel": display_label,
        'complement': complement.pk,
        'sga_elements': complement,
        'step': 3,
        'templateinstance': display_label.template,
        'template': display_label.pk,
        'label': display_label.label,
        'substance': display_label.label.substance.pk,
        'org_pk': org_pk
    }
    return render(request, 'sga/substance/step_three.html', context)


@login_required
@permission_required('sga.change_securityleaf')
def step_four(request, org_pk, substance):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    security_leaf = get_object_or_404(SecurityLeaf, substance__pk=substance)
    display_label = DisplayLabel.objects.filter(
        label__substance__pk=substance).first()
    complement = SGAComplement.objects.filter(substance__pk=substance).first()
    context = {}
    if request.method == 'POST':
        form = SecurityLeafForm(request.POST, instance=security_leaf)
        if form.is_valid():
            obj = form.save()
            organilab_logentry(request.user, obj, CHANGE, "security leaf",
                               changed_data=form.changed_data)
            return redirect(reverse('sga:get_substance', kwargs={'org_pk': org_pk}))

    form = SecurityLeafForm(instance=security_leaf)
    context = {'step': 4,
               'complement': complement.pk,
               'template': display_label.pk,
               'form': form,
               'provider_form': ProviderSGAForm(),
               'substance': substance,
               'org_pk': org_pk
               }
    return render(request, 'sga/substance/step_four.html', context=context)


@login_required
def security_leaf_pdf(request, org_pk, substance):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    leaf = get_object_or_404(SecurityLeaf, substance__pk=substance)
    component = SGAComplement.objects.filter(substance__pk=substance).first()
    date_print = now().strftime('%Y-%m-%d')
    if leaf:
        template = get_template('sga/substance/security_leaf_pdf.html')
        context = {'leaf': leaf,
                   'substance': leaf.substance,
                   'provider': leaf.provider,
                   'component': component,
                   'date_print': date_print,
                   'date_check': leaf.created_at.strftime('%Y-%m-%d'),
                   'org_pk': org_pk}
        html_template = template.render(context)
        pdf = HTML(string=html_template,
                   base_url=request.build_absolute_uri()).write_pdf()
        return HttpResponse(pdf, content_type='application/pdf')


@login_required
def add_sga_complements(request, org_pk, *args, **kwargs):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    element = kwargs['element']
    form = None
    urls = {'warning': 'sga:add_warning_word',
            'danger': 'sga:add_danger_indication',
            'prudence': 'sga:add_prudence_advice',
            }
    view_urls = {'warning': 'sga:warning_words',
                 'danger': 'sga:danger_indications',
                 'prudence': 'sga:prudence_advices',
                 }
    titles = {'warning': _('Create Warning Word'),
              'danger': _('Create Danger Indication'),
              'prudence': _('Create Prudence Advice'),
              }

    forms = {'warning': WarningWordForm(),
             'danger': DangerIndicationForm(),
             'prudence': PrudenceAdviceForm(),
             }
    if request.method == 'POST':
        forms = {'warning': WarningWordForm(request.POST),
                 'danger': DangerIndicationForm(request.POST),
                 'prudence': PrudenceAdviceForm(request.POST),
                 }
        form = forms[element]

        if form.is_valid():
            obj = form.save()

            model_name = {
                'warning': 'warning word',
                'danger': 'danger indication',
                'prudence': 'prudence advice'
            }
            return redirect(reverse(view_urls[element], kwargs={'org_pk': org_pk}))

    else:
        form = forms[element]

    context = {
        'form': form,
        'url': reverse(urls[element], kwargs={'org_pk': org_pk}),
        'view_url': reverse(view_urls[element], kwargs={'org_pk': org_pk}),
        'title': titles[element]
    }

    return render(request, 'sga/substance/sga_components.html', context=context)


@login_required
@permission_required('sga.view_dangerindication')
def view_danger_indications(request, org_pk, *args, **kwargs):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    listado = list(DangerIndication.objects.all())
    return render(request, 'sga/substance/danger_indication.html',
                  context={'listado': listado, 'org_pk': org_pk})


@login_required
@permission_required('sga.view_warningword')
def view_warning_words(request, org_pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    listado = WarningWord.objects.all()
    return render(request, 'sga/substance/warning_words.html',
                  context={'listado': listado, 'org_pk': org_pk})


@login_required
@permission_required('sga.view_prudenceadvice')
def view_prudence_advices(request, org_pk, *args, **kwargs):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    listado = PrudenceAdvice.objects.all()
    return render(request, 'sga/substance/prudence_advice.html',
                  context={'listado': listado, 'org_pk': org_pk})


@login_required
@permission_required('sga.view_substanceobservation')
def add_observation(request, org_pk, substance):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    obj = None
    form = None

    if substance and request.method == 'POST':
        substance_obj = get_object_or_404(Substance, pk=int(substance))

        form = ObservationForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.substance = substance_obj
            obj.creator = request.user
            request.session['step'] = 2
            obj.save()
            organilab_logentry(request.user, obj, ADDITION, "substance observation",
                               changed_data=form.changed_data)
            messages.success(request, 'Se Guardo correctamente')
            return redirect(reverse('sga:detail_substance',
                                    kwargs={'org_pk': org_pk, 'pk': substance}))
        else:
            request.session['step'] = 2
            messages.error(request, 'Datos invalidos')
            return redirect(reverse('sga:detail_substance',
                                    kwargs={'org_pk': org_pk, 'pk': substance}))
    else:
        request.session['step'] = 2
        return redirect(
            reverse('sga:detail_substance', kwargs={'org_pk': org_pk, 'pk': substance}))
    return redirect(
        reverse('sga:detail_substance', kwargs={'org_pk': org_pk, 'pk': substance}))


@login_required
@permission_required('sga.change_substanceobservation')
def update_observation(request, org_pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    if request.method == 'POST':

        substance_obj = get_object_or_404(SubstanceObservation,
                                          pk=int(request.POST.get('pk')))
        if substance_obj:
            substance_obj.description = request.POST.get('description', '')
            substance_obj.save()
            organilab_logentry(request.user, substance_obj, CHANGE,
                               "substance observation", changed_data=['description'])
            request.session['step'] = 2

            return JsonResponse({'status': True})
        else:
            return JsonResponse({'status': False})
    return JsonResponse({'status': False})


@login_required
@permission_required('sga.delete_substanceobservation')
def delete_observation(request, org_pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    if request.method == 'POST':

        substance_obj = get_object_or_404(SubstanceObservation,
                                          pk=int(request.POST.get('pk')))
        if substance_obj:
            organilab_logentry(request.user, substance_obj, DELETION,
                               "substance observation")
            substance_obj.delete()
            request.session['step'] = 2
            return JsonResponse({'status': True})
        else:
            return JsonResponse({'status': False})
    return JsonResponse({'status': False})


@login_required
@permission_required('sga.change_warningword')
def change_warning_word(request, org_pk, pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    instance = get_object_or_404(WarningWord, pk=pk)
    form = None
    context = {}

    if request.method == 'POST':
        form = WarningWordForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save()
            organilab_logentry(request.user, obj, CHANGE, "warning word",
                               changed_data=form.changed_data)
            return redirect(reverse('sga:warning_words', kwargs={'org_pk': org_pk}))
    else:
        form = WarningWordForm(instance=instance)
        context = {
            'form': form,
            'view_url': reverse('sga:warning_words', kwargs={'org_pk': org_pk}),
            'title': _('Update the Warning Word') + " " + instance.name,
            'url': reverse('sga:update_warning_word',
                           kwargs={'org_pk': org_pk, 'pk': instance.pk}),
            'org_pk': org_pk
        }
    return render(request, 'sga/substance/sga_components.html', context=context)


@login_required
@permission_required('sga.change_prudenceadvice')
def change_prudence_advice(request, org_pk, pk, *args, **kwargs):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    instance = get_object_or_404(PrudenceAdvice, pk=pk)
    form = None
    context = {}

    if request.method == 'POST':
        form = PrudenceAdviceForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save()
            organilab_logentry(request.user, obj, CHANGE, "prudence advice",
                               changed_data=form.changed_data)
            return redirect(
                reverse('sga:prudence_advices', kwargs={'org_pk': org_pk, }))
    else:
        form = PrudenceAdviceForm(instance=instance)
        context = {
            'form': form,
            'view_url': reverse('sga:prudence_advices', kwargs={'org_pk': org_pk, }),
            'title': _('Update the Prudence Advice') + " " + instance.name,
            'url': reverse('sga:update_prudence_advice',
                           kwargs={'org_pk': org_pk, 'pk': instance.pk})
        }
    return render(request, 'sga/substance/sga_components.html', context=context)


@login_required
@permission_required('sga.change_dangerindication')
def change_danger_indication(request, org_pk, pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    instance = get_object_or_404(DangerIndication, pk=pk)
    form = None
    context = {}

    if request.method == 'POST':
        form = DangerIndicationForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save()
            organilab_logentry(request.user, obj, CHANGE, "danger indication",
                               changed_data=form.changed_data)
            return redirect(
                reverse('sga:danger_indications', kwargs={'org_pk': org_pk}))
    else:
        form = DangerIndicationForm(instance=instance)
        context = {
            'form': form,
            'view_url': reverse('sga:danger_indications', kwargs={'org_pk': org_pk}),
            'title': _('Update the Danger indication') + " " + instance.code,
            'url': reverse('sga:update_danger_indication',
                           kwargs={'org_pk': org_pk, 'pk': instance.pk}),
            'org_pk': org_pk
        }
    return render(request, 'sga/substance/sga_components.html', context=context)


@login_required
@permission_required('sga.add_provider')
def add_sga_provider(request, org_pk):
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    user_is_allowed_on_organization(request.user, organization)
    form = ProviderSGAForm(request.POST)

    if form.is_valid():
        provider = form.save(commit=False)
        provider.save()
        organilab_logentry(request.user, provider, ADDITION, "provider",
                           changed_data=form.changed_data)
        return JsonResponse(
            {'result': True, 'provider_pk': provider.pk, 'provider': provider.name})
    else:
        return JsonResponse({'result': False})
