
from djgentelella.models import ChunkedUpload
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, get_object_or_404, redirect
from academic.models import SubstanceSGA, SubstanceObservation
from django.contrib.auth.models import User
from academic.substance.forms import SustanceObjectForm, SustanceCharacteristicsForm, DangerIndicationForm, \
    WarningWordForm, PrudenceAdviceForm, ObservacionForm, SecurityLeafForm
from laboratory.validators import isValidate_molecular_formula
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from sga.decorators import organilab_context_decorator
from sga.forms import SGAEditorForm, PersonalForm, PersonalFormAcademic, PersonalSGAForm, LabelForm, \
    BuilderInformationForm, SGAComplementsForm, ProviderSGAForm
from sga.models import Substance, WarningWord, DangerIndication, PrudenceAdvice, SubstanceCharacteristics, \
    TemplateSGA, Label, PersonalTemplateSGA, SGAComplement, SecurityLeaf

from django.template.loader import get_template
from weasyprint import HTML
from datetime import datetime


@login_required
@permission_required('laboratory.change_object')
@organilab_context_decorator
def create_edit_sustance(request, organilabcontext, pk=None):

    instance = Substance.objects.filter(pk=pk).first()

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
            return redirect(reverse('step_two', kwargs={'organilabcontext':organilabcontext, 'pk':complement.pk}))

    elif instance == None and request.method=='GET':

            substance = Substance.objects.create(organilab_context=organilabcontext, creator=request.user)
            SubstanceCharacteristics.objects.create(substance=substance)

            return redirect(reverse('step_one', kwargs={'organilabcontext':organilabcontext,'pk':substance.pk}))


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
        'pk':instance.pk
    })

@login_required
@permission_required('sga.view_substance')
@organilab_context_decorator
def get_substances(request, organilabcontext):
    substances=None

    if request.user:
        substances = Substance.objects.filter(creator=request.user)
    context = {
        'substances':substances,
        'organilabcontext': organilabcontext
    }

    return render(request, 'academic/substance/list_substance.html', context=context)


@login_required
@permission_required('sga.view_substance')
@organilab_context_decorator
def get_list_substances(request,organilabcontext):
    substances=None

    if request.user:
        substances = Substance.objects.all().order_by('-id')

    context = {
        'substances':substances,
        'organilabcontext': organilabcontext
    }

    return render(request, 'academic/substance/check_substances.html', context=context)

@login_required
@permission_required('sga.view_substance')
@organilab_context_decorator
def check_list_substances(request,organilabcontext):
    substances=None

    if request.user:
        substances = Substance.objects.filter(is_approved=False).order_by('--pk')

    context = {
        'substances':substances,
        'organilabcontext': organilabcontext
    }

    return render(request, 'academic/substance/check_substances.html', context=context)
@login_required
@permission_required('sga.change_substance')
@organilab_context_decorator
def approve_substances(request,organilabcontext,pk):
    substances=Substance.objects.filter(pk=pk).first()
    if substances:
        substances.is_approved=True
        substances.save()
        return redirect('approved_substance')
    return redirect('approved_substance')

@login_required
@permission_required('sga.delete_substance')
@organilab_context_decorator
def delete_substance(request,organilabcontext,pk):
    substances=Substance.objects.filter(pk=pk).first()
    if substances:
        messages.success(request, _("The substance is removed successfully"))
        substances.delete()

        return redirect(reverse("get_substance", kwargs={'organilabcontext':organilabcontext}))
    return redirect(reverse("get_substance", kwargs={'organilabcontext':organilabcontext}))

@login_required
@permission_required('sga.change_substance')
@organilab_context_decorator
def detail_substance(request, organilabcontext, pk):
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
        'url': reverse('add_observation',kwargs={'organilabcontext':organilabcontext, 'substance':pk})
    }
    return render(request, "academic/substance/detail.html",context=context)

@login_required
def add_sga_complements(request, element):

    form = None
    urls = {'warning': 'add_warning_word',
            'danger': 'add_danger_indication',
            'prudence': 'add_prudence_advice',
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
            return redirect(reverse(view_urls[element]))

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
def view_danger_indications(request):
    listado = list(DangerIndication.objects.all())
    return render(request, 'academic/substance/danger_indication.html', context={'listado': listado})
@login_required
def view_warning_words(request):
    listado = list(WarningWord.objects.all())
    return render(request, 'academic/substance/warning_words.html', context={'listado': listado})
@login_required
def view_prudence_advices(request):
    listado = list(PrudenceAdvice.objects.all())
    return render(request, 'academic/substance/prudence_advice.html', context={'listado': listado})

@login_required
@organilab_context_decorator
def add_observation(request, organilabcontext, substance):

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
            messages.success(request, 'Se Guardo correctamente')
            return redirect(reverse('detail_substance',kwargs={'organilabcontext':organilabcontext,'pk':substance}))
        else:
            request.session['step'] = 2
            messages.error(request, 'Datos invalidos')
            return redirect(reverse('detail_substance',kwargs={'organilabcontext':organilabcontext,'pk':substance}))
    else:
        request.session['step'] = 2
        return redirect(reverse('detail_substance', kwargs={'organilabcontext': organilabcontext, 'pk': substance}))
    return redirect(reverse('detail_substance', kwargs={'organilabcontext': organilabcontext, 'pk': substance}))

@login_required
def update_observation(request):

    if request.method == 'POST':

        substance_obj = get_object_or_404(SubstanceObservation, pk=int(request.POST.get('pk')))
        if substance_obj:
            substance_obj.description=request.POST.get('description','')
            substance_obj.save()
            request.session['step'] = 2

            return JsonResponse({'status':True})
        else:
            return JsonResponse({'status':False})
    return JsonResponse({'status': False})

@login_required
def delete_observation(request):

    if request.method == 'POST':

        substance_obj = get_object_or_404(SubstanceObservation, pk=int(request.POST.get('pk')))
        if substance_obj:
            substance_obj.delete()
            request.session['step'] = 2
            return JsonResponse({'status':True})
        else:
            return JsonResponse({'status':False})
    return JsonResponse({'status': False})

@login_required
def change_warning_word(request,pk):
    instance = get_object_or_404(WarningWord, pk=pk)
    form = None
    context ={}

    if request.method =='POST':
        form = WarningWordForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect(reverse('warning_words'))
    else:
        form = WarningWordForm(instance=instance)
        context = {
            'form':form,
            'view_url':reverse('warning_words'),
            'title':_('Update the Warning Word')+" "+instance.name,
            'url':reverse('update_warning_word', kwargs={'pk':instance.pk})
        }
    return render(request, 'academic/substance/sga_components.html', context=context)
@login_required
def change_prudence_advice(request, pk):
    instance = get_object_or_404(PrudenceAdvice, pk=pk)
    form = None
    context ={}

    if request.method =='POST':
        form = PrudenceAdviceForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect(reverse('prudence_advices'))
    else:
        form = PrudenceAdviceForm(instance=instance)
        context = {
            'form':form,
            'view_url':reverse('prudence_advices'),
            'title':_('Update the Prudence Advice')+" "+instance.name,
            'url':reverse('update_prudence_advice', kwargs={'pk':instance.pk})
        }
    return render(request, 'academic/substance/sga_components.html', context=context)
@login_required
def change_danger_indication(request, pk):
    instance = get_object_or_404(DangerIndication, pk=pk)
    form = None
    context ={}

    if request.method =='POST':
        form = DangerIndicationForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect(reverse('danger_indications'))
    else:
        form = DangerIndicationForm(instance=instance)
        context = {
            'form':form,
            'view_url':reverse('danger_indications'),
            'title':_('Update the Danger indication')+" "+instance.code,
            'url':reverse('update_danger_indication', kwargs={'pk':instance.pk})
        }
    return render(request, 'academic/substance/sga_components.html', context=context)

@permission_required('sga.change_personaltemplatesga')
@organilab_context_decorator
def step_three(request, organilabcontext, template, substance):
    personaltemplateSGA = get_object_or_404(PersonalTemplateSGA, pk=template)
    user = request.user
    complement =  get_object_or_404(SGAComplement, substance__pk=substance)
    if request.method == 'POST':

        form = PersonalSGAForm(request.POST, instance=personaltemplateSGA)
        label_form = LabelForm(request.POST, instance=personaltemplateSGA.label)

        builder_information_form = BuilderInformationForm(request.POST, instance=personaltemplateSGA.label.builderInformation)
        if form.is_valid() and builder_information_form.is_valid() and label_form.is_valid():
            instance = form.save(commit=False)
            upload_id = form.cleaned_data['logo_upload_id']

            if upload_id:
                tmpupload = get_object_or_404(ChunkedUpload, upload_id=upload_id)
                instance.logo = tmpupload.get_uploaded_file()

            instance.save()
            builder = builder_information_form.save(commit=False)
            builder.user=request.user
            builder.save()
            label = label_form.save(commit=False)
            label.builderInformation= builder
            label.save()
            return redirect(reverse('step_three',
                                    kwargs={'organilabcontext':organilabcontext, 'template':personaltemplateSGA.pk,
                                            'substance':personaltemplateSGA.label.substance.pk}))
        else:
            messages.error(request, _("Invalid form"))
            context = {
                'laboratory': None,
                'form': SGAEditorForm(),
                'warningwords': WarningWord.objects.all(),
                'generalform': PersonalFormAcademic(request.POST, user=user, substance=substance),
                'form_url': reverse('step_three',
                                    kwargs={'organilabcontext':organilabcontext, 'template':personaltemplateSGA.pk,
                                            'substance':personaltemplateSGA.label.substance.pk}),
                'organilabcontext': organilabcontext,
                'step': 3,
                'template': personaltemplateSGA.pk,
                'substance': personaltemplateSGA.label.substance.pk,
            }
            return render(request, 'academic/substance/step_three.html', context)

    initial = {'name': personaltemplateSGA.name, 'template': personaltemplateSGA.template,
               'barcode': personaltemplateSGA.barcode, 'json_representation': personaltemplateSGA.json_representation}

    if personaltemplateSGA.label:
        bi_info = personaltemplateSGA.label.builderInformation
        initial.update({'substance': personaltemplateSGA.label.substance.pk,
            'commercial_information': personaltemplateSGA.label.commercial_information})

        if bi_info:
            initial.update({'company_name': bi_info.name,
                            'phone': bi_info.phone,
                            'address': bi_info.address})

    context={
        'warningwords': WarningWord.objects.all(),
        'form': SGAEditorForm,
        "instance": personaltemplateSGA,
        'organilabcontext': organilabcontext,
        'complement': complement.pk,
        'sga_elements': complement,
        "generalform": PersonalFormAcademic(user=user, substance=substance, initial=initial),
        'step': 3,
        'template': personaltemplateSGA.pk,
        'substance': personaltemplateSGA.label.substance.pk,
    }
    return render(request, 'academic/substance/step_three.html', context)


def step_two(request, organilabcontext, pk):
    complement = get_object_or_404(SGAComplement, pk=pk)
    form= None
    context ={}
    personaltemplateSGA = PersonalTemplateSGA.objects.filter(label__substance__pk=complement.substance.pk).first()
    if request.method == 'POST':
        form = SGAComplementsForm(request.POST, instance=complement)
        if form.is_valid():
            obj = form.save()
            return  redirect(reverse('step_three', kwargs={'organilabcontext':organilabcontext, 'template':personaltemplateSGA.pk, 'substance':personaltemplateSGA.label.substance.pk}))
        else:
            messages.error(request, _("Invalid form"))
            context={
                'form': SGAComplementsForm(instance=complement),
                'organilabcontext': organilabcontext,
                'step': 2,
                'template': personaltemplateSGA.pk,
                'complement': complement.pk,
                'substance': complement.substance.pk,
            }
            return redirect(reverse('step_two', kwargs={'organilabcontext':organilabcontext,'complement':complement.pk, 'template':personaltemplateSGA.pk, 'substance':personaltemplateSGA.label.substance.pk}))
    context = {
        'form': SGAComplementsForm(instance=complement),
        'organilabcontext': organilabcontext,
        'step': 2,
        'complement': complement.pk,
        'template': personaltemplateSGA.pk,
        'substance': complement.substance.pk,
    }
    return render(request, 'academic/substance/step_two.html', context)

def step_four(request,organilabcontext, substance):
    security_leaf = get_object_or_404(SecurityLeaf, substance__pk=substance)
    personaltemplateSGA = PersonalTemplateSGA.objects.filter(label__substance__pk=substance).first()
    complement = SGAComplement.objects.filter(substance__pk=substance).first()
    context = {}
    if request.method == 'POST':
        form = SecurityLeafForm(request.POST, instance=security_leaf)
        if form.is_valid():
            form.save()
            return redirect(reverse('get_substance',kwargs={'organilabcontext':organilabcontext}))
    form = SecurityLeafForm(instance=security_leaf)
    context = {'step': 4,
               'organilabcontext': organilabcontext,
               'complement': complement.pk,
               'template': personaltemplateSGA.pk,
               'form':form,
               'provider_form': ProviderSGAForm(),
               'substance': substance}
    return render(request,'academic/substance/step_four.html',context=context)

def add_sga_provider(request):
    form = ProviderSGAForm(request.POST)

    if form.is_valid():
        provider=form.save(commit=False)
        provider.save()

        return JsonResponse({'result':True,'provider_pk':provider.pk,'provider':provider.name})
    else:
        return JsonResponse({'result':False})

def security_leaf_pdf(request, substance):
    leaf = get_object_or_404(SecurityLeaf, substance__pk=substance)
    component = SGAComplement.objects.filter(substance__pk=substance).first()
    date_print =datetime.today().strftime('%Y-%m-%d')
    if leaf:
        template = get_template('academic/substance/security_leaf_pdf.html')
        context = {'leaf':leaf,'substance':leaf.substance, 'provider':leaf.provider,'component':component,'date_print':date_print,'date_check':leaf.created_at.strftime('%Y-%m-%d')}
        html_template=template.render(context)
        pdf = HTML(string=html_template).write_pdf()
        return HttpResponse(pdf, content_type='application/pdf')