from datetime import datetime

from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import permission_required, login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import get_template
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from weasyprint import HTML

from academic.models import SubstanceObservation
from academic.substance.forms import DangerIndicationForm, \
    WarningWordForm, PrudenceAdviceForm, ObservacionForm, SecurityLeafForm
from laboratory.utils import organilab_logentry
from sga.forms import BuilderInformationForm, SGAComplementsForm, ProviderSGAForm, PersonalSGAAddForm, \
    PersonalEditorForm
from sga.models import Substance, WarningWord, DangerIndication, PrudenceAdvice, PersonalTemplateSGA, SGAComplement, \
    SecurityLeaf


@login_required
def add_sga_complements(request, *args, **kwargs):
    org_pk= int(kwargs.get('org_pk'))
    element= str(kwargs.get('element'))

    form = None
    urls = {'warning': 'academic:add_warning_word',
            'danger': 'academic:add_danger_indication',
            'prudence': 'academic:add_prudence_advice',
            }
    view_urls = {'warning': 'academic:warning_words',
                 'danger': 'academic:danger_indications',
                 'prudence': 'academic:prudence_advices',
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
        'form':form,
        'url': reverse(urls[element], kwargs={'org_pk':org_pk}),
        'view_url': reverse(view_urls[element], kwargs={'org_pk':org_pk}),
        'title': titles[element]
    }

    return render(request, 'academic/substance/sga_components.html', context=context)


@login_required
@permission_required('sga.view_dangerindication')
def view_danger_indications(request, *args, **kwargs):
    org = int(kwargs.get('org_pk'))
    listado = list(DangerIndication.objects.all())
    return render(request, 'academic/substance/danger_indication.html', context={'listado': listado,'org_pk':org})
@login_required
@permission_required('sga.view_warningword')
def view_warning_words(request, org_pk):
    listado = list(WarningWord.objects.all())
    return render(request, 'academic/substance/warning_words.html', context={'listado': listado, 'org_pk': org_pk})
@login_required
@permission_required('sga.view_prudenceadvice')
def view_prudence_advices(request, *args, **kwargs):
    org = int(kwargs.get('org_pk'))
    listado = list(PrudenceAdvice.objects.all())
    return render(request, 'academic/substance/prudence_advice.html', context={'listado': listado,'org_pk':org})

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
def change_prudence_advice(request, *args, **kwargs):
    pk= int(kwargs.get('pk'))
    org_pk=int(kwargs.get('org_pk'))
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