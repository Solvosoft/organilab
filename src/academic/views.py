from django.shortcuts import get_object_or_404, redirect
from academic.models import Procedure, ProcedureStep, ProcedureRequiredObject, ProcedureObservations
from django.urls.base import reverse_lazy
from django.urls import reverse
from laboratory.decorators import has_lab_assigned
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required
from academic.forms import ProcedureForm, ProcedureStepForm, ObjectForm, ObservationForm, StepForm, ReservationForm
from django.views.generic import ListView, CreateView, UpdateView, FormView
from django.shortcuts import redirect, render
from django.http import JsonResponse
from laboratory.models import Object, Catalog, Furniture, ShelfObject
from reservations_management.models import ReservedProducts
from . import convertions
import json
from django.utils.translation import gettext_lazy as _


@permission_required('academic.add_procedurestep')
def add_steps_wrapper(request, pk, lab_pk=None):
    procedure = get_object_or_404(Procedure, pk=pk)
    procstep = ProcedureStep.objects.create(procedure=procedure)
    return redirect(reverse('update_step', kwargs={'pk': procstep.pk, 'lab_pk': lab_pk}))


class ProcedureListView(ListView):
    model = Procedure
    queryset = Procedure.objects.all()
    template_name = 'academic/list.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ProcedureListView, self).get_context_data()
        context['lab'] = self.kwargs['pk']
        context['reservation_form'] = ReservationForm
        return context


class ProcedureCreateView(CreateView):
    model = Procedure
    form_class = ProcedureForm
    template_name = 'academic/procedure_create.html'

    def get_context_data(self, **kwargs):
        context = super(ProcedureCreateView, self).get_context_data()
        context['lab_pk'] = self.kwargs['lab_pk']
        return context

    def get_success_url(self, **kwargs):
        lab_pk = self.kwargs['lab_pk']
        success_url = reverse_lazy('procedure_list', kwargs={'pk': lab_pk})
        return success_url


class ProcedureUpdateView(UpdateView):
    model = Procedure
    form_class = ProcedureForm
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
    return render(request, 'academic/detail.html',
                  {'object': steps, 'procedure': pk, 'lab_pk': lab_pk, 'reservation_form': ReservationForm})


class ProcedureStepCreateView(FormView):
    form_class = StepForm
    template_name = 'academic/procedure_steps.html'

    def get_context_data(self, **kwargs):
        context = super(ProcedureStepCreateView, self).get_context_data()
        context['object_form'] = ObjectForm
        context['observation_form'] = ObservationForm
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        procedure = get_object_or_404(Procedure, pk=int(self.kwargs['pk']))
        step = ProcedureStep.objects.create(procedure=procedure, title=form.cleaned_data['title'],
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
        context['lab_pk'] = self.kwargs['lab_pk']
        return context

    def get_success_url(self, **kwargs):
        lab_pk = self.kwargs['lab_pk']
        success_url = reverse_lazy('procedure_list', kwargs={'pk': lab_pk})
        return success_url


def save_object(request, pk, lab_pk):
    """ Add a Required object """

    step = get_object_or_404(ProcedureStep, pk=pk)
    unit = get_object_or_404(Catalog, pk=int(request.POST['unit']))
    obj = Object.objects.get(pk=int(request.POST['object']))
    status = False
    msg = _('There is no object in the inventory with this unit of measurement')
    if unit.description in validate_unit(lab_pk, obj):
        objects = ProcedureRequiredObject.objects.create(step=step, object=obj,
                                                         quantity=request.POST['quantity'],
                                                         measurement_unit=unit)
        objects.save()
        status = True

    return JsonResponse({'data': get_objects(pk), 'status': status, 'msg': msg})


def validate_unit(lab, obj):
    """ Validate if the required object unit exist into the shelfobjects of the laboratory """
    shelf_obj = ShelfObject.objects.filter(shelf__furniture__labroom__laboratory__id=int(lab), object__id=obj.id)
    units = []
    for obj in shelf_obj:
        units.append(obj.measurement_unit.description)

    return set(units)


def delete_step(request):
    step = ProcedureStep.objects.get(pk=int(request.POST['pk']))
    step.delete()
    return JsonResponse({'data': True})


def remove_object(request, pk):
    obj = ProcedureRequiredObject.objects.get(pk=int(request.POST['pk']))
    obj.delete()

    return JsonResponse({'data': get_objects(pk)})


def get_objects(pk):
    objects_list = ProcedureRequiredObject.objects.filter(step__id=pk)
    aux = []
    for data in objects_list:
        aux.append(
            {'obj': str(data.object), 'unit': str(data.measurement_unit), 'id': data.pk, 'amount': data.quantity})
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


def remove_observation(request, pk):
    obj = ProcedureObservations.objects.get(pk=int(request.POST['pk']))
    obj.delete()

    return JsonResponse({'data': get_observations(pk)})


def get_procedure(request):
    procedure = get_object_or_404(Procedure, pk=int(request.POST['pk']))
    return JsonResponse({'data': {'title': procedure.title, 'pk': procedure.pk}})


def delete_procedure(request):
    procedure = get_object_or_404(Procedure, pk=int(request.POST['pk']))
    procedure.delete()
    return JsonResponse({'data': True})


def list_step_objects(id):
    """ Generate a list about the pk objects of required objects"""
    steps = ProcedureStep.objects.filter(procedure__id=int(id))
    objs = []

    for step in steps:
        for obj in step.procedurerequiredobject_set.all():
            objs.append(obj.object.id)
    return set(objs)


def get_objects_list(lab, pk):
    """Generate a list of the ShelfObjects in the laboratory"""

    furnitures = Furniture.objects.filter(labroom__laboratory__id=int(lab))
    obj_list = []
    for furniture in furnitures:
        for shelf in furniture.shelf_set.all():
            for obj in shelf.shelfobject_set.all():
                if obj.object.id == pk:
                    obj_list.append(obj)

    return obj_list


def get_step_object(procedure, pk):
    """Generate a list of required objects into the procedurestep """
    steps = ProcedureStep.objects.filter(procedure__id=int(procedure))
    object_list = []
    for step in steps:
        for obj in step.procedurerequiredobject_set.all():
            if obj.object.id == pk:
                object_list.append(obj)

    return object_list


def convert_to_general_unit(data):
    """" This method convert the objects quantity into specific unit for example meters, grams and liter"""
    result = 0.0

    mts = ['Centímetros', 'Metros', 'Milímetros']

    gr = ['Kilogramos', 'Miligramo', 'Gramos']

    lt = ['Litros', 'Mililitros']

    for obj in data:
        if obj.measurement_unit.description in mts:
            result += convertions.convert_meters(obj.quantity, obj.measurement_unit.description)

        elif obj.measurement_unit.description in gr:
            result += convertions.convert_grams(obj.quantity, obj.measurement_unit.description)

        elif obj.measurement_unit.description in lt:
            result += convertions.convert_lt(obj.quantity, obj.measurement_unit.description)

        else:
            result += obj.quantity

    return result


def generate_reservation(request):
    lab = request.POST['lab_pk']
    procedure = request.POST['procedure']
    objects_pk = list_step_objects(procedure)
    obj_find = 0
    state = False
    for obj in objects_pk:

        objs = convert_to_general_unit(get_objects_list(lab, obj))
        step_objs = convert_to_general_unit(get_step_object(procedure, obj))

        if objs >= step_objs:
            obj_find += 1

    if len(objects_pk) == obj_find:
        state = True
        for obj in objects_pk:
            add_reservation(request, get_objects_list(lab, obj),
                            get_step_object(procedure, obj))

    return JsonResponse({'state': state})


def add_reservation(request, data, data_step):
    """Generate the reservation and add the respective quantity of the object"""
    result = 0
    for obj in data:
        index = 0

        while index < len(data_step):

            result = convertions.convertion(data_step[index].quantity, obj.measurement_unit.description,
                                            data_step[index].measurement_unit.description)

            if obj.quantity >= result:
                obj.quantity -= result
                data_step[index].quantity = 0

            else:
                result = obj.quantity
                obj.quantity -= result
                data_step[index].quantity -= convertions.convertion(result,
                                                                   data_step[index].measurement_unit.description,
                                                                   obj.measurement_unit.description)

            if result > 0:
                reserved = ReservedProducts.objects.create(shelf_object=obj,
                                                           user=request.user,
                                                           initial_date=request.POST['initial_date'],
                                                           final_date=request.POST['final_date'],
                                                           amount_required=result)
                reserved.save()

            if result == 0 or obj.quantity == 0:
                index+=1

    return result
