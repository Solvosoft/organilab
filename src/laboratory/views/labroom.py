# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''

from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator
from laboratory.models import LaboratoryRoom, Laboratory
from .djgeneric import CreateView, DeleteView, ListView, UpdateView
from laboratory.views.furniture import FurnitureCreateForm
from laboratory.forms import ReservationModalForm,AddObjectForm,TransferObjectForm,SubtractObjectForm
from laboratory.decorators import has_lab_assigned


@method_decorator(has_lab_assigned(), name='dispatch')
@method_decorator(permission_required('laboratory.view_laboratoryroom'), name='dispatch')
class LaboratoryRoomsList(ListView):
    model = LaboratoryRoom

    def get_queryset(self):
        lab = get_object_or_404(
            Laboratory, pk=self.lab)
        self.request.session['search_lab'] = self.lab
        return lab.rooms.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modal_form_reservation'] = ReservationModalForm()
        context['tranfer_object_form'] = TransferObjectForm(users=self.request.user.profile.pk,lab_send=self.lab)
        context['add_object_form'] = AddObjectForm(lab=self.lab)
        context['subtract_object_form'] = SubtractObjectForm()
        context['options'] = ['Reservation','Add','Transfer','Subtract']
        context['user'] = self.request.user
        return context


@method_decorator(has_lab_assigned(), name='dispatch')
@method_decorator(permission_required('laboratory.add_laboratoryroom'), name='dispatch')
class LabroomCreate(CreateView):
    model = LaboratoryRoom
    fields = '__all__'
    success_url = "/"

    def get_context_data(self, **kwargs):
        context = CreateView.get_context_data(self, **kwargs)
        lab = get_object_or_404(Laboratory, pk=self.lab)
        context['object_list'] = lab.rooms.all()
        context['laboratory'] = self.lab
        context['furniture_form'] = FurnitureCreateForm
        return context

    def form_valid(self, form):
        room = form.save()
        lab = get_object_or_404(Laboratory, pk=self.lab)
        lab.rooms.add(room)
        lab.save()
        return super(LabroomCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('laboratory:rooms_create', args=(self.lab,))


@method_decorator(has_lab_assigned(), name='dispatch')
@method_decorator(permission_required('laboratory.change_laboratoryroom'), name='dispatch')
class LabroomUpdate(UpdateView):
    model = LaboratoryRoom
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = UpdateView.get_context_data(self, **kwargs)
        context['furniture_form'] = FurnitureCreateForm
        return context

    def get_success_url(self):
        return reverse_lazy('laboratory:rooms_create', args=(self.lab,))


@method_decorator(has_lab_assigned(), name='dispatch')
@method_decorator(permission_required('laboratory.delete_laboratoryroom'), name='dispatch')
class LaboratoryRoomDelete(DeleteView):
    model = LaboratoryRoom
    success_url = "/"

    def get_success_url(self):
        return reverse_lazy('laboratory:rooms_create', args=(
            self.kwargs.get('lab_pk'),))


@method_decorator(has_lab_assigned(), name='dispatch')
@method_decorator(permission_required('laboratory.view_report'), name='dispatch')
class LaboratoryRoomReportView(ListView):
    model = LaboratoryRoom
    template_name = "laboratory/report_laboratoryroom_list.html"

    def get_queryset(self):
        lab = get_object_or_404(Laboratory, pk=self.lab)
        return lab.rooms.all()
