from datetime import datetime

from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import get_template
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from weasyprint import HTML

from academic.models import SubstanceObservation
from academic.substance.forms import SustanceObjectForm, SustanceCharacteristicsForm, DangerIndicationForm, \
    WarningWordForm, PrudenceAdviceForm, ObservacionForm, SecurityLeafForm, ReviewSubstanceForm
from laboratory.models import OrganizationStructure
from laboratory.utils import organilab_logentry
from sga.decorators import organilab_context_decorator
from sga.forms import SGAEditorForm, BuilderInformationForm, SGAComplementsForm, ProviderSGAForm, PersonalSGAAddForm, \
    EditorForm
from sga.models import Substance, WarningWord, DangerIndication, PrudenceAdvice, SubstanceCharacteristics, \
    TemplateSGA, Label, PersonalTemplateSGA, SGAComplement, SecurityLeaf, ReviewSubstance


@login_required
@permission_required('laboratory.change_object')
@organilab_context_decorator
def create_edit_sustance(request, org_pk, organilabcontext, pk=None):
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
            obj.organilab_context=organilabcontext
            obj.save()
            objform.save_m2m()
            suscharinst = suschacform.save(commit=False)
            suscharinst.substance = obj
            suscharinst.organilab_context=organilabcontext
            label, created= Label.objects.get_or_create(substance= obj)
            complement, complement_created= SGAComplement.objects.get_or_create(substance= obj)
            leaf, leaf_created= SecurityLeaf.objects.get_or_create(substance= obj)
            template= TemplateSGA.objects.filter(is_default=True).first()
            personal,created = PersonalTemplateSGA.objects.get_or_create(label=label, template=template, user= request.user,organilab_context=organilabcontext)

            molecular_formula = suschacform.cleaned_data["molecular_formula"]
            #if isValidate_molecular_formula(molecular_formula):
            # #suscharinst.valid_molecular_formula = True

            suscharinst.save()
            suschacform.save_m2m()
            organilab_logentry(request.user, obj, CHANGE, "substance", changed_data=objform.changed_data)
            organilab_logentry(request.user, suscharinst, CHANGE, "substance characteristics", changed_data=suschacform.changed_data)

            return redirect(reverse('academic:step_two', kwargs={'organilabcontext':organilabcontext, 'org_pk': org_pk, 'pk':complement.pk}))

    elif instance == None and request.method=='GET':
        substance = Substance.objects.create(organilab_context=organilabcontext, creator=request.user, organization=organization)
        rev_sub = ReviewSubstance.objects.create(substance=substance)
        charac = SubstanceCharacteristics.objects.create(substance=substance)
        organilab_logentry(request.user, substance, ADDITION, "substance")
        organilab_logentry(request.user, charac, ADDITION, "substance characteristics")
        organilab_logentry(request.user, rev_sub, ADDITION, "review substance", changed_data=['substance'])
        return redirect(reverse('academic:step_one', kwargs={'org_pk': org_pk, 'organilabcontext': organilabcontext, 'pk':substance.pk}))


    label, created_label= Label.objects.get_or_create(substance= instance)
    template= TemplateSGA.objects.get(is_default=True)
    personal, created = PersonalTemplateSGA.objects.get_or_create(label=label, template=template, user= request.user,organilab_context=organilabcontext)
    complement, sga_created = SGAComplement.objects.get_or_create(substance = instance)
    leaf, leaf_created = SecurityLeaf.objects.get_or_create(substance=instance)

    return render(request, 'academic/substance/create_sustance.html', {
        'objform': objform,
        'suschacform': suschacform,
        'instance': instance,
        'organilabcontext':organilabcontext,
        'step':1,
        'template':personal.pk,
        'substance':instance.pk,
        'complement':complement.pk,
        'pk':instance.pk,
        'org_pk': org_pk
    })

@login_required
@permission_required('sga.view_substance')
@organilab_context_decorator
def get_substances(request, org_pk, organilabcontext):
    substances=None

    if request.user:
        substances = Substance.objects.filter(creator=request.user)
    if substances:
        substances = substances.filter(organization__pk=org_pk)
    context = {
        'substances':substances,
        'organilabcontext': organilabcontext,
        'org_pk': org_pk
    }

    return render(request, 'academic/substance/list_substance.html', context=context)

@login_required
@permission_required('sga.view_substance')
@organilab_context_decorator
def get_list_substances(request,organilabcontext, org_pk):
    showapprove = True if request.GET.get('showapprove') else False
    form = ReviewSubstanceForm()
    context = {
        'organilabcontext': organilabcontext,
        'form':form,
        'org_pk': org_pk,
        'showapprove': showapprove
    }
    return render(request, 'academic/substance/check_substances.html', context=context)

@login_required
@permission_required('sga.change_substance')
@organilab_context_decorator
def approve_substances(request, org_pk, organilabcontext, pk):
    review_subs = get_object_or_404(ReviewSubstance, pk=pk)
    review_subs.is_approved=True
    review_subs.save()
    organilab_logentry(request.user, review_subs, CHANGE, "review substance", changed_data=['is_approved'])
    return redirect(reverse('academic:approved_substance', kwargs={'organilabcontext':organilabcontext, 'org_pk':org_pk}))


@login_required
@permission_required('sga.delete_substance')
@organilab_context_decorator
def delete_substance(request, org_pk, organilabcontext, pk):
    substances=Substance.objects.filter(pk=pk).first()
    if substances:
        messages.success(request, _("The substance is removed successfully"))
        organilab_logentry(request.user, substances, DELETION, "substance")
        Label.objects.filter(substance=substances).delete()
        substances.delete()
        return redirect(reverse("academic:get_substance", kwargs={'organilabcontext':organilabcontext, 'org_pk': org_pk}))
    return redirect(reverse("academic:get_substance", kwargs={'organilabcontext':organilabcontext, 'org_pk': org_pk}))

@login_required
@permission_required('sga.change_substance')
@organilab_context_decorator
def detail_substance(request, org_pk, organilabcontext, pk):
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
        'organilabcontext': organilabcontext,
        'observationForm':ObservacionForm(),
        'step':step,
        'url': reverse('academic:add_observation',kwargs={'organilabcontext':organilabcontext, 'org_pk': org_pk, 'substance':pk}),
        'org_pk': org_pk
    }
    return render(request, "academic/substance/detail.html",context=context)

@login_required
def add_sga_complements(request, org_pk, element):

    form = None
    urls = {'warning': 'academic:add_warning_word',
            'danger': 'academic:add_danger_indication',
            'prudence': 'academic:add_prudence_advice',
            }
    view_urls = {'warning': 'warning_words',
                 'danger': 'danger_indications',
                 'prudence': 'prudence_advices',
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
            organilab_logentry(request.user, obj, ADDITION, model_name[element], changed_data=form.changed_data)
            return redirect(reverse(view_urls[element], kwargs={'org_pk': org_pk}))

    else:
        form = forms[element]

    context = {
        'form':form,
        'url': reverse(urls[element]),
        'view_url': reverse(view_urls[element]),
        'title': titles[element]
    }

    return render(request, 'academic/substance/sga_components.html', context=context)


@login_required
@permission_required('sga.view_dangerindication')
def view_danger_indications(request):
    listado = list(DangerIndication.objects.all())
    return render(request, 'academic/substance/danger_indication.html', context={'listado': listado})
@login_required
@permission_required('sga.view_warningword')
def view_warning_words(request, org_pk):
    listado = list(WarningWord.objects.all())
    return render(request, 'academic/substance/warning_words.html', context={'listado': listado, 'org_pk': org_pk})
@login_required
@permission_required('sga.view_prudenceadvice')
def view_prudence_advices(request):
    listado = list(PrudenceAdvice.objects.all())
    return render(request, 'academic/substance/prudence_advice.html', context={'listado': listado})

@login_required
@permission_required('academic.view_substanceobservation')
@organilab_context_decorator
def add_observation(request, org_pk, organilabcontext, substance):

    obj = None
    form = None

    if substance and request.method == 'POST':
        substance_obj = get_object_or_404(Substance, pk=int(substance))

        form = ObservacionForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.substance=substance_obj
            obj.creator = request.user
            request.session['step'] = 2
            obj.save()
            organilab_logentry(request.user, obj, ADDITION, "substance observation", changed_data=form.changed_data)
            messages.success(request, 'Se Guardo correctamente')
            return redirect(reverse('academic:detail_substance',kwargs={'organilabcontext':organilabcontext, 'org_pk':org_pk, 'pk':substance}))
        else:
            request.session['step'] = 2
            messages.error(request, 'Datos invalidos')
            return redirect(reverse('academic:detail_substance',kwargs={'organilabcontext':organilabcontext, 'org_pk': org_pk, 'pk':substance}))
    else:
        request.session['step'] = 2
        return redirect(reverse('academic:detail_substance', kwargs={'organilabcontext': organilabcontext, 'org_pk': org_pk, 'pk': substance}))
    return redirect(reverse('academic:detail_substance', kwargs={'organilabcontext': organilabcontext, 'org_pk': org_pk, 'pk': substance}))

@login_required
@permission_required('academic.change_substanceobservation')
def update_observation(request, org_pk):

    if request.method == 'POST':

        substance_obj = get_object_or_404(SubstanceObservation, pk=int(request.POST.get('pk')))
        if substance_obj:
            substance_obj.description=request.POST.get('description','')
            substance_obj.save()
            organilab_logentry(request.user, substance_obj, CHANGE, "substance observation", changed_data=['description'])
            request.session['step'] = 2

            return JsonResponse({'status':True})
        else:
            return JsonResponse({'status':False})
    return JsonResponse({'status': False})

@login_required
@permission_required('academic.delete_substanceobservation')
def delete_observation(request, org_pk):

    if request.method == 'POST':

        substance_obj = get_object_or_404(SubstanceObservation, pk=int(request.POST.get('pk')))
        if substance_obj:
            organilab_logentry(request.user, substance_obj, DELETION, "substance observation")
            substance_obj.delete()
            request.session['step'] = 2
            return JsonResponse({'status':True})
        else:
            return JsonResponse({'status':False})
    return JsonResponse({'status': False})

@login_required
@permission_required('sga.change_warningword')
def change_warning_word(request, org_pk, pk):
    instance = get_object_or_404(WarningWord, pk=pk)
    form = None
    context ={}

    if request.method =='POST':
        form = WarningWordForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save()
            organilab_logentry(request.user, obj, CHANGE, "warning word", changed_data=form.changed_data)
            return redirect(reverse('academic:warning_words', kwargs={'org_pk': org_pk}))
    else:
        form = WarningWordForm(instance=instance)
        context = {
            'form':form,
            'view_url':reverse('academic:warning_words', kwargs={'org_pk': org_pk}),
            'title':_('Update the Warning Word')+" "+instance.name,
            'url':reverse('academic:update_warning_word', kwargs={'org_pk': org_pk, 'pk':instance.pk}),
            'org_pk': org_pk
        }
    return render(request, 'academic/substance/sga_components.html', context=context)

@login_required
@permission_required('sga.change_prudenceadvice')
def change_prudence_advice(request, org_pk, pk):
    instance = get_object_or_404(PrudenceAdvice, pk=pk)
    form = None
    context ={}

    if request.method =='POST':
        form = PrudenceAdviceForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save()
            organilab_logentry(request.user, obj, CHANGE, "prudence advice", changed_data=form.changed_data)
            return redirect(reverse('academic:prudence_advices', kwargs={'org_pk': org_pk,}))
    else:
        form = PrudenceAdviceForm(instance=instance)
        context = {
            'form':form,
            'view_url':reverse('academic:prudence_advices', kwargs={'org_pk': org_pk,}),
            'title':_('Update the Prudence Advice')+" "+instance.name,
            'url':reverse('academic:update_prudence_advice', kwargs={'org_pk': org_pk, 'pk':instance.pk})
        }
    return render(request, 'academic/substance/sga_components.html', context=context)

@login_required
@permission_required('sga.change_dangerindication')
def change_danger_indication(request, org_pk, pk):
    instance = get_object_or_404(DangerIndication, pk=pk)
    form = None
    context ={}

    if request.method =='POST':
        form = DangerIndicationForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save()
            organilab_logentry(request.user, obj, CHANGE, "danger indication", changed_data=form.changed_data)
            return redirect(reverse('academic:danger_indications', kwargs={'org_pk': org_pk}))
    else:
        form = DangerIndicationForm(instance=instance)
        context = {
            'form':form,
            'view_url':reverse('academic:danger_indications', kwargs={'org_pk': org_pk}),
            'title':_('Update the Danger indication')+" "+instance.code,
            'url':reverse('academic:update_danger_indication', kwargs={'org_pk': org_pk, 'pk':instance.pk}),
            'org_pk': org_pk
        }
    return render(request, 'academic/substance/sga_components.html', context=context)

@permission_required('sga.change_personaltemplatesga')
@organilab_context_decorator
def step_three(request, org_pk, organilabcontext, template, substance):
    personaltemplateSGA = get_object_or_404(PersonalTemplateSGA, pk=template)
    complement = get_object_or_404(SGAComplement, substance__pk=substance)
    user = request.user

    if request.method == 'POST':
        form = EditorForm(request.POST, instance=personaltemplateSGA.template)
        if form.is_valid():
            obj = form.save()
            organilab_logentry(request.user, obj, CHANGE, "template sga", changed_data=form.changed_data)
            return redirect(reverse('academic:step_four', kwargs={'organilabcontext':organilabcontext,
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
        'editorform': EditorForm(),
        'warningwords': WarningWord.objects.all(),
        'form': SGAEditorForm,
        "instance": personaltemplateSGA,
        "sgalabel": personaltemplateSGA,
        'organilabcontext': organilabcontext,
        'complement': complement.pk,
        'sga_elements': complement,
        'step': 3,
        'template': personaltemplateSGA.pk,
        'label': personaltemplateSGA.label,
        'substance': personaltemplateSGA.label.substance.pk,
        'org_pk': org_pk
    }
    return render(request, 'academic/substance/step_three.html', context)

@login_required
@permission_required('sga.change_sgacomplement')
def step_two(request, org_pk, organilabcontext, pk):
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
            return redirect(reverse('academic:step_three', kwargs={'organilabcontext':organilabcontext,
                                                          'template':personaltemplateSGA.pk,
                                                          'substance':personaltemplateSGA.label.substance.pk,
                                                          'org_pk': org_pk}))
        else:
            messages.error(request, _("Invalid form"))
            context = {
                'form': SGAComplementsForm(instance=complement),
                'builderinformationform': builderinformationform,
                'pesonalform': pesonalform,
                'organilabcontext': organilabcontext,
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
        'organilabcontext': organilabcontext,
        'step': 2,
        'complement': complement.pk,
        'template': personaltemplateSGA.pk,
        'substance': complement.substance.pk,
        'org_pk': org_pk
    }
    return render(request, 'academic/substance/step_two.html', context)

@login_required
@permission_required('sga.change_securityleaf')
def step_four(request, org_pk, organilabcontext, substance):
    security_leaf = get_object_or_404(SecurityLeaf, substance__pk=substance)
    personaltemplateSGA = PersonalTemplateSGA.objects.filter(label__substance__pk=substance).first()
    complement = SGAComplement.objects.filter(substance__pk=substance).first()
    context = {}
    if request.method == 'POST':
        form = SecurityLeafForm(request.POST, instance=security_leaf)
        if form.is_valid():
            obj = form.save()
            organilab_logentry(request.user, obj, CHANGE, "security leaf", changed_data=form.changed_data)
            return redirect(reverse('academic:get_substance',kwargs={'organilabcontext':organilabcontext,
                                                            'org_pk': org_pk
                                                            }))
    form = SecurityLeafForm(instance=security_leaf)
    context = {'step': 4,
               'organilabcontext': organilabcontext,
               'complement': complement.pk,
               'template': personaltemplateSGA.pk,
               'form':form,
               'provider_form': ProviderSGAForm(),
               'substance': substance,
               'org_pk': org_pk
               }
    return render(request,'academic/substance/step_four.html',context=context)

@login_required
@permission_required('sga.add_provider')
def add_sga_provider(request, org_pk):
    form = ProviderSGAForm(request.POST)

    if form.is_valid():
        provider=form.save(commit=False)
        provider.save()
        organilab_logentry(request.user, provider, ADDITION, "provider", changed_data=form.changed_data)
        return JsonResponse({'result':True,'provider_pk':provider.pk,'provider':provider.name})
    else:
        return JsonResponse({'result':False})

@login_required
def security_leaf_pdf(request, org_pk, substance):
    leaf = get_object_or_404(SecurityLeaf, substance__pk=substance)
    component = SGAComplement.objects.filter(substance__pk=substance).first()
    date_print =datetime.today().strftime('%Y-%m-%d')
    if leaf:
        template = get_template('academic/substance/security_leaf_pdf.html')
        context = {'leaf':leaf,
                   'substance':leaf.substance,
                   'provider':leaf.provider,
                   'component':component,
                   'date_print':date_print,
                   'date_check':leaf.created_at.strftime('%Y-%m-%d'),
                   'org_pk': org_pk}
        html_template=template.render(context)
        pdf = HTML(string=html_template, base_url=request.build_absolute_uri()).write_pdf()
        return HttpResponse(pdf, content_type='application/pdf')