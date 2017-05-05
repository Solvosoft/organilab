from django.shortcuts import render, get_object_or_404, redirect
from cruds_adminlte.crud import CRUDView
from academic.models import Procedure, ProcedureStep, ProcedureRequiredObject,\
    ProcedureObservations
from cruds_adminlte.inline_crud import InlineAjaxCRUD
from django.urls.base import reverse_lazy

# Create your views here.

class ProcedureView(CRUDView):
    model = Procedure
    

class ProcedureRequiredObjectView(InlineAjaxCRUD):    
    base_model = ProcedureStep
    model = ProcedureRequiredObject
    inline_field = 'step'
    title = 'Objects required'
    fields = ['object', 'quantity', 'measurement_unit']
    list_fields = ['object', 'quantity', 'measurement_unit']

class ProcedureObservationsView(InlineAjaxCRUD):    
    base_model = ProcedureStep
    model = ProcedureObservations
    inline_field = 'step'
    title = 'Observation'
    fields=['description']
    list_fields = ['description']

class StepsView(CRUDView):
    model = ProcedureStep
    inlines=[ProcedureRequiredObjectView, ProcedureObservationsView ]
    list_fields = ['title']
    fields=['title', 'description']
    views_available = ['detail','update', 'delete']

    def get_update_view(self):
        crudU= CRUDView.get_update_view(self)
        class CSV(crudU):
            def get_success_url(self):
                return reverse_lazy('academic_procedure_list')
        return CSV
    
    def get_delete_view(self):
        Dview= CRUDView.get_delete_view(self)
        class CSV(Dview):
            def get_success_url(self):
                return reverse_lazy('academic_procedure_list')
        return CSV
def add_steps_wrapper(request, pk):
    procedure = get_object_or_404(Procedure, pk=pk)
    procstep = ProcedureStep.objects.create(procedure=procedure)
    return redirect('academic_procedurestep_update', pk=procstep.pk)