from django.shortcuts import get_object_or_404, redirect
from academic.models import Procedure, ProcedureStep, ProcedureRequiredObject,ProcedureObservations
from django.urls.base import reverse_lazy
from django.urls import reverse
from laboratory.decorators import has_lab_assigned
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required
from academic.forms import ProcedureForm, ProcedureStepForm,ObjectForm,ObservationForm,StepForm,ReservationForm
from django.views.generic import ListView, CreateView, UpdateView,FormView
from django.shortcuts import redirect, render
from django.http import JsonResponse
from laboratory.models import Object, Catalog
from django.views.decorators.csrf import csrf_exempt
import json
from django.core import serializers


@permission_required('academic.add_procedurestep')
def add_steps_wrapper(request, pk,lab_pk=None):
    procedure = get_object_or_404(Procedure, pk=pk)
    procstep = ProcedureStep.objects.create(procedure=procedure)
    return redirect(reverse('update_step', kwargs={'pk':procstep.pk, 'lab_pk': lab_pk}))



class ProcedureListView(ListView):
    model = Procedure
    queryset = Procedure.objects.all()
    template_name = 'academic/list.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context= super(ProcedureListView, self).get_context_data()
        context['lab'] = self.kwargs['pk']
        context['reservation_form']=ReservationForm
        return context


class ProcedureCreateView(CreateView):
    model = Procedure
    form_class=ProcedureForm
    template_name = 'academic/procedure_create.html'

    def get_context_data(self, **kwargs):
        context = super(ProcedureCreateView, self).get_context_data()
        context['lab_pk']=self.kwargs['lab_pk']
        return context

    def get_success_url(self, **kwargs):
        lab_pk = self.kwargs['lab_pk']
        success_url = reverse_lazy('procedure_list', kwargs={'pk': lab_pk})
        return success_url

class ProcedureUpdateView(UpdateView):
    model = Procedure
    form_class= ProcedureForm
    template_name = 'academic/procedure_create.html'

    def get_context_data(self, **kwargs):
        context = super(ProcedureUpdateView, self).get_context_data()
        context['lab_pk'] = self.kwargs['lab_pk']
        return context

    def get_success_url(self, **kwargs):
        lab_pk = self.kwargs['lab_pk']
        success_url = reverse_lazy('procedure_list', kwargs={'pk': lab_pk})
        return success_url

def procedureStepDetail(request, pk, lab_pk):
    steps = Procedure.objects.filter(pk=pk).first()
    return render(request,'academic/detail.html', {'object':steps,'procedure':pk, 'lab_pk':lab_pk,'reservation_form':ReservationForm})


class ProcedureStepCreateView(FormView):
    form_class = StepForm
    template_name = 'academic/procedure_steps.html'

    def get_context_data(self, **kwargs):
        context = super(ProcedureStepCreateView, self).get_context_data()
        context['object_form']=ObjectForm
        context['observation_form']=ObservationForm
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        procedure = get_object_or_404(Procedure, pk=int(self.kwargs['pk']))
        step = ProcedureStep.objects.create(procedure=procedure,title=form.cleaned_data['title'],
                                         description=form.cleaned_data['description'])
        step.save()

        return response

    def get_success_url(self):
        lab_pk = self.kwargs['lab_pk']
        success_url = reverse_lazy('procedure_list', kwargs={'pk': lab_pk})
        return success_url

class ProcedureStepUpdateView(UpdateView):
    model = ProcedureStep
    form_class = ProcedureStepForm
    template_name = 'academic/procedure_steps.html'

    def get_context_data(self, **kwargs):
        context = super(ProcedureStepUpdateView, self).get_context_data()
        context['object_form'] = ObjectForm
        context['observation_form'] = ObservationForm
        context['step'] = ProcedureStep.objects.get(pk=int(self.kwargs['pk']))
        context['lab_pk']=self.kwargs['lab_pk']
        return context

    def get_success_url(self, **kwargs):
        lab_pk = self.kwargs['lab_pk']
        success_url = reverse_lazy('procedure_list', kwargs={'pk': lab_pk})
        return success_url


def save_object(request, pk):
    step = get_object_or_404(ProcedureStep, pk=pk)
    unit = get_object_or_404(Catalog, pk=int(request.POST['unit']))
    obj = get_object_or_404(Object, pk=int(request.POST['object']))

    objects = ProcedureRequiredObject.objects.create(step=step, object=obj,
                                          quantity=request.POST['quantity'],
                                          measurement_unit=unit)
    objects.save()
    return JsonResponse({'data': get_objects(pk)})


def delete_step(request):
    step = ProcedureStep.objects.get(pk=int(request.POST['pk']))
    step.delete()
    return JsonResponse({'data': True})


def remove_object(request,pk):
    obj = ProcedureRequiredObject.objects.get(pk=int(request.POST['pk']))
    obj.delete()

    return JsonResponse({'data': get_objects(pk)})


def get_objects(pk):
    objects_list = ProcedureRequiredObject.objects.filter(step__id=pk)
    aux = []
    for data in objects_list:
        aux.append({'obj': str(data.object), 'unit': str(data.measurement_unit), 'id': data.pk,'amount': data.quantity})
    result = json.dumps(aux)
    return result


def save_observation(request, pk):

    step = get_object_or_404(ProcedureStep, pk=pk)

    objects = ProcedureObservations.objects.create(step=step, description=request.POST['description'])
    objects.save()

    return JsonResponse({'data': get_observations(pk)})


def get_observations(pk):
    obsevations = ProcedureObservations.objects.filter(step__id=pk)
    aux = []
    for data in obsevations:
        aux.append({'description': data.description, 'id': data.pk})
    result = json.dumps(aux)
    return result


def remove_observation(request,pk):
    obj = ProcedureObservations.objects.get(pk=int(request.POST['pk']))
    obj.delete()

    return JsonResponse({'data': get_observations(pk)})


def get_procedure(request):
    procedure= get_object_or_404(Procedure, pk=int(request.POST['pk']))
    return JsonResponse({'data': {'title': procedure.title, 'pk': procedure.pk}})

def delete_procedure(request):
    procedure = get_object_or_404(Procedure, pk=int(request.POST['pk']))
    procedure.delete()
    return JsonResponse({'data': True})