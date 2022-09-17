from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, get_object_or_404, redirect
from academic.models import SubstanceSGA, SubstanceObservation
from django.contrib.auth.models import User
from academic.substance.forms import SustanceObjectForm, SustanceCharacteristicsForm, DangerIndicationForm, \
    WarningWordForm, PrudenceAdviceForm, ObservacionForm
from laboratory.validators import isValidate_molecular_formula
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from sga.decorators import organilab_context_decorator
from sga.forms import SGAEditorForm, PersonalForm
from sga.models import Substance, WarningWord, DangerIndication, PrudenceAdvice


@login_required
@permission_required('laboratory.change_object')
@organilab_context_decorator
def create_edit_sustance(request, organilabcontext, pk=None):
    instance = Substance.objects.filter(pk=pk).first()

    suscharobj=None

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

            molecular_formula = suschacform.cleaned_data["molecular_formula"]
            if isValidate_molecular_formula(molecular_formula):
                suscharinst.valid_molecular_formula = True

            suscharinst.save()
            suschacform.save_m2m()
            return redirect(reverse('step_two', kwargs={'organilabcontext':organilabcontext}))


    return render(request, 'academic/substance/create_sustance.html', {
        'objform': objform,
        'suschacform': suschacform,
        'instance': instance,
        'organilabcontext':organilabcontext,
        'step':1
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
        substances = SubstanceSGA.objects.filter(is_approved=False).order_by('--pk')

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
@organilab_context_decorator
def step_two(request, organilabcontext):
    context = {
        'form': SGAEditorForm(),
        'warningwords': WarningWord.objects.all(),
        'generalform': PersonalForm(user=request.user),
        'organilabcontext': organilabcontext,
        'step':2,
        'form_url': reverse('sga:add_personal', kwargs={'organilabcontext': organilabcontext})
    }
    return render(request, 'academic/substance/step_two.html', context)\

@login_required
@organilab_context_decorator
def add_sga_complements(request, organilabcontext,element):

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
            obj = form.save(commit=False)
            obj.organilab_context='academic'
            obj.save()
            return redirect(reverse(view_urls[element], kwargs={'organilabcontext':organilabcontext}))

    else:
        form = forms[element]

    context = {
        'form':form,
        'organilabcontext':organilabcontext,
        'url': reverse(urls[element], kwargs={'organilabcontext':organilabcontext}),
        'view_url': reverse(view_urls[element], kwargs={'organilabcontext':organilabcontext}),
        'title': titles[element]
    }

    return render(request, 'academic/substance/sga_components.html', context=context)

@organilab_context_decorator
def view_danger_indications(request, organilabcontext):
    listado = list(DangerIndication.objects.all())
    return render(request, 'academic/substance/danger_indication.html', context={'listado': listado, 'organilabcontext': organilabcontext})
@organilab_context_decorator
def view_warning_words(request, organilabcontext):
    listado = list(WarningWord.objects.all())
    return render(request, 'academic/substance/warning_words.html', context={'listado': listado, 'organilabcontext': organilabcontext})
@organilab_context_decorator
def view_prudence_advices(request, organilabcontext):
    listado = list(PrudenceAdvice.objects.all())
    return render(request, 'academic/substance/prudence_advice.html', context={'listado': listado, 'organilabcontext': organilabcontext})

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
@organilab_context_decorator
def change_warning_word(request,organilabcontext,pk):
    instance = get_object_or_404(WarningWord, pk=pk)
    form = None
    context ={}

    if request.method =='POST':
        form = WarningWordForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect(reverse('warning_words', kwargs={'organilabcontext':organilabcontext}))
    else:
        form = WarningWordForm(instance=instance)
        context = {
            'form':form,
            'view_url':reverse('warning_words', kwargs={'organilabcontext':organilabcontext}),
            'title':_('Update the Warning Word')+" "+instance.name,
            'url':reverse('update_warning_word', kwargs={'organilabcontext':organilabcontext,'pk':instance.pk})
        }
    return render(request, 'academic/substance/sga_components.html', context=context)
@login_required
@organilab_context_decorator
def change_prudence_advice(request,organilabcontext,pk):
    instance = get_object_or_404(PrudenceAdvice, pk=pk)
    form = None
    context ={}

    if request.method =='POST':
        form = PrudenceAdviceForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect(reverse('prudence_advices', kwargs={'organilabcontext':organilabcontext}))
    else:
        form = PrudenceAdviceForm(instance=instance)
        context = {
            'form':form,
            'view_url':reverse('prudence_advices', kwargs={'organilabcontext':organilabcontext}),
            'title':_('Update the Prudence Advice')+" "+instance.name,
            'url':reverse('update_prudence_advice', kwargs={'organilabcontext':organilabcontext,'pk':instance.pk})
        }
    return render(request, 'academic/substance/sga_components.html', context=context)
@login_required
@organilab_context_decorator
def change_danger_indication(request,organilabcontext,pk):
    instance = get_object_or_404(DangerIndication, pk=pk)
    form = None
    context ={}

    if request.method =='POST':
        form = DangerIndicationForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect(reverse('danger_indications', kwargs={'organilabcontext':organilabcontext}))
    else:
        form = DangerIndicationForm(instance=instance)
        context = {
            'form':form,
            'view_url':reverse('danger_indications', kwargs={'organilabcontext':organilabcontext}),
            'title':_('Update the Danger indication')+" "+instance.code,
            'url':reverse('update_danger_indication', kwargs={'organilabcontext':organilabcontext,'pk':instance.pk})
        }
    return render(request, 'academic/substance/sga_components.html', context=context)

