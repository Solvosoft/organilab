import json

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from academic.forms import ProcedureForm, ProcedureStepForm, ObjectForm, ObservationForm, StepForm, ReservationForm
from academic.models import Procedure, ProcedureStep, ProcedureRequiredObject, ProcedureObservations
from laboratory.models import Object, Catalog, Furniture, ShelfObject
from laboratory.utils import organilab_logentry
from laboratory.views.djgeneric import (
    ListView as DJListView,
    CreateView as DJCreateView,
    UpdateView as DJUpdateView
)
from reservations_management.models import ReservedProducts
from . import convertions


@login_required
@permission_required('academic.add_procedurestep')
def add_steps_wrapper(request, *args, **kwargs):
    procedure = get_object_or_404(Procedure, pk=kwargs['pk'])
    procstep = ProcedureStep.objects.create(procedure=procedure)
    organilab_logentry(request.user, procstep, ADDITION, relobj=kwargs['lab_pk'])
    return redirect(reverse('academic:update_step', kwargs={'pk': procstep.pk, 'lab_pk': kwargs['lab_pk'],'org_pk':kwargs['org_pk']}))


@method_decorator(permission_required('academic.view_procedure'), name='dispatch')
class ProcedureListView(DJListView):
    model = Procedure
    queryset = Procedure.objects.all()
    template_name = 'academic/list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        content_type = ContentType.objects.get(app_label='laboratory', model="laboratory")
        queryset = queryset.filter(content_type=content_type, object_id=self.lab)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ProcedureListView, self).get_context_data()
        context['reservation_form'] = ReservationForm
        return context

class ProcedureCreateView(DJCreateView):
    model = Procedure
    form_class = ProcedureForm
    template_name = 'academic/procedure_create.html'

    def get_context_data(self, **kwargs):
        context = super(ProcedureCreateView, self).get_context_data()
        return context

    def get_success_url(self, **kwargs):
        success_url = reverse_lazy('academic:procedure_list', kwargs={'org_pk':self.org, 'lab_pk': self.lab,})
        return success_url

    def form_valid(self, form):
        procedure = form.save(commit=False)
        content_type = ContentType.objects.get(app_label='laboratory', model="laboratory")
        procedure.content_type = content_type
        procedure.object_id = self.lab
        procedure.save()
        organilab_logentry(self.request.user, procedure, ADDITION, changed_data=form.changed_data,
                           relobj=self.lab)
        return super(ProcedureCreateView, self).form_valid(form)


@method_decorator(permission_required('academic.change_procedure'), name='dispatch')
class ProcedureUpdateView(DJUpdateView):
    model = Procedure
    form_class = ProcedureForm
    template_name = 'academic/procedure_create.html'

    def get_context_data(self, **kwargs):
        context = super(ProcedureUpdateView, self).get_context_data()
        return context

    def get_success_url(self, **kwargs):
        success_url = reverse_lazy('academic:procedure_list', kwargs={'org_pk':self.org, 'lab_pk': self.lab,})
        return success_url

    def form_valid(self, form):
        procedure = form.save()
        organilab_logentry(self.request.user, procedure, CHANGE, changed_data=form.changed_data,
                           relobj=self.lab)
        return super(ProcedureUpdateView, self).form_valid(form)

@login_required
@permission_required('academic.view_procedure')
def procedureStepDetail(request, *args, **kwargs):
    pk= kwargs['pk']
    lab_pk=kwargs['lab_pk']
    org_pk=kwargs['org_pk']
    steps = Procedure.objects.filter(pk=pk).first()
    return render(request, 'academic/detail.html',
                  {'object': steps, 'procedure': pk, 'laboratory': lab_pk, 'org_pk':org_pk, 'reservation_form': ReservationForm})


@method_decorator(permission_required('academic.add_procedurestep'), name='dispatch')
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
        organilab_logentry(self.request.user, step, ADDITION, changed_data=form.changed_data,
                           relobj=procedure.content_object)

        return response

    def get_success_url(self):
        lab_pk = self.kwargs['lab_pk']
        org = self.kwargs['org_pk']
        success_url = reverse_lazy('academic:procedure_list', kwargs={'org_pk':org, 'pk': lab_pk,})
        return success_url

@method_decorator(permission_required('academic.change_procedurestep'), name='dispatch')
class ProcedureStepUpdateView(DJUpdateView):
    model = ProcedureStep
    form_class = ProcedureStepForm
    template_name = 'academic/procedure_steps.html'

    def get_context_data(self, **kwargs):
        context = super(ProcedureStepUpdateView, self).get_context_data()
        context['object_form'] = ObjectForm
        context['observation_form'] = ObservationForm
        context['step'] = ProcedureStep.objects.get(pk=int(self.kwargs['pk']))
        return context

    def get_success_url(self, **kwargs):
        success_url = reverse_lazy('academic:procedure_list', kwargs={'org_pk':self.org, 'lab_pk': self.lab,})
        return success_url

    def form_valid(self, form):
        procedurestep = form.save()
        organilab_logentry(self.request.user, procedurestep, CHANGE, changed_data=form.changed_data,
                           relobj=self.lab)
        return super(ProcedureStepUpdateView, self).form_valid(form)

@login_required
@permission_required('academic.add_procedurerequiredobject')
def save_object(request, *args, **kwargs):
    """ Add a Required object """
    pk = kwargs['pk']
    lab_pk = kwargs['lab_pk']
    org_pk = kwargs['org_pk']
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
        str_obj = f'{objects.object} {objects.quantity} {str(objects.measurement_unit)}'
        change_message = str_obj + " procedure required object has been added"
        changed_data = ['object', 'quantity', 'unit']
        organilab_logentry(request.user, objects, ADDITION, changed_data=changed_data, change_message=change_message,
                           relobj=lab_pk)

    return JsonResponse({'data': get_objects(pk), 'status': status, 'msg': msg})


def validate_unit(lab, obj):
    """ Validate if the required object unit exist into the shelfobjects of the laboratory """
    shelf_obj = ShelfObject.objects.filter(shelf__furniture__labroom__laboratory__id=int(lab), object__id=obj.id)
    units = []
    for obj in shelf_obj:
        units.append(obj.measurement_unit.description)
    return set(units)

@login_required
@permission_required('academic.delete_procedurestep')
def delete_step(request, *args, **kwargs):
    step = ProcedureStep.objects.get(pk=int(request.POST['pk']))
    organilab_logentry(request.user, step, DELETION, relobj=step.procedure.content_object)
    step.delete()
    return JsonResponse({'data': True})

@permission_required('academic.delete_procedurerequiredobject')
def remove_object(request, *args, **kwargs):
    pk= kwargs['pk']
    obj = ProcedureRequiredObject.objects.get(pk=int(request.POST['pk']))
    obj.delete()
    organilab_logentry(request.user, obj, DELETION)
    return JsonResponse({'data': get_objects(pk)})


def get_objects(pk):
    objects_list = ProcedureRequiredObject.objects.filter(step__id=pk)
    aux = []
    for data in objects_list:
        aux.append(
            {'obj': str(data.object), 'unit': str(data.measurement_unit), 'id': data.pk, 'amount': data.quantity})
    result = json.dumps(aux)
    return result


@login_required
@permission_required('academic.add_procedureobservations')
def save_observation(request, *args, **kwargs):
    pk= kwargs['pk']

    step = get_object_or_404(ProcedureStep, pk=pk)

    objects = ProcedureObservations.objects.create(step=step, description=request.POST['description'])
    objects.save()
    organilab_logentry(request.user,  objects, ADDITION, changed_data=['description'])

    return JsonResponse({'data': get_observations(pk)})

def get_observations(pk):
    obsevations = ProcedureObservations.objects.filter(step__id=pk)
    aux = []
    for data in obsevations:
        aux.append({'description': data.description, 'id': data.pk})
    result = json.dumps(aux)
    return result

@login_required
@permission_required('academic.delete_procedureobservations')
def remove_observation(request, *args, **kwargs):
    pk= kwargs['pk']

    obj = ProcedureObservations.objects.get(pk=int(request.POST['pk']))
    obj.delete()
    organilab_logentry(request.user, obj, DELETION)
    return JsonResponse({'data': get_observations(pk)})

@login_required
@permission_required('academic.view_procedure')
def get_procedure(request, *args, **kwargs):
    procedure = get_object_or_404(Procedure, pk=int(request.POST['pk']))
    return JsonResponse({'data': {'title': procedure.title, 'pk': procedure.pk}})

@permission_required('academic.delete_procedure')
def delete_procedure(request, *args, **kwargs):
    procedure = get_object_or_404(Procedure, pk=int(request.POST['pk']))
    procedure.delete()
    organilab_logentry(request.user, procedure, DELETION)
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

@permission_required('reservations_management.add_reservedproducts')
def generate_reservation(request, *args, **kwargs):

    lab = kwargs.get('lab_pk')
    procedure = request.POST['procedure']
    objects_pk = list_step_objects(procedure)
    obj_find = 0
    state = False
    obj_unknown=[]
    for obj in objects_pk:

        objs = convert_to_general_unit(get_objects_list(lab, obj))
        step_objs = convert_to_general_unit(get_step_object(procedure, obj))

        if objs >= step_objs:
            obj_find += 1
        else:
            obj_unknown.append(Object.objects.get(pk=obj).__str__())


    if len(objects_pk) == obj_find:
        state = True
        for obj in objects_pk:
            add_reservation(request, get_objects_list(lab, obj),
                            get_step_object(procedure, obj))

    return JsonResponse({'state': state, 'errors':obj_unknown})


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
                form = ReservationForm(request.POST)
                if form.is_valid():
                    reserved = ReservedProducts.objects.create(shelf_object=obj,
                                                               user=request.user,
                                                               initial_date=form.cleaned_data['initial_date'],
                                                               final_date=form.cleaned_data['final_date'],
                                                               amount_required=result)
                    reserved.save()
                    organilab_logentry(request.user, reserved, ADDITION, changed_data=form.changed_data)

            if result == 0 or obj.quantity == 0:
                index+=1

    return result
