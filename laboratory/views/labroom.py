# encoding: utf-8


'''
Created on 26/12/2016

@author: luisza
'''
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator

from laboratory.models import LaboratoryRoom, Laboratory

from .djgeneric import CreateView, DeleteView, ListView


@method_decorator(login_required, name='dispatch')
class LaboratoryRoomsList(ListView):
    model = LaboratoryRoom

    def get_queryset(self):
        lab = get_object_or_404(
            Laboratory, pk=self.lab)
        return lab.rooms.all()


@method_decorator(login_required, name='dispatch')
class LabroomCreate(CreateView):
    model = LaboratoryRoom
    fields = '__all__'
    success_url = "/"

    def get_context_data(self, **kwargs):
        context = CreateView.get_context_data(self, **kwargs)
        lab = get_object_or_404(Laboratory, pk=self.lab)
        context['object_list'] = lab.rooms.all()
        context['laboratory'] = self.lab
        return context

    def form_valid(self, form):
        room = form.save()
        lab = get_object_or_404(Laboratory, pk=self.lab)
        lab.rooms.add(room)
        lab.save()
        return super(LabroomCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('laboratory:rooms_create', args=(self.lab,))


@method_decorator(login_required, name='dispatch')
class LaboratoryRoomDelete(DeleteView):
    model = LaboratoryRoom
    success_url = "/"

    def get_success_url(self):
        return reverse_lazy('laboratory:rooms_create', args=(
            self.kwargs.get('lab_pk'), ))


@method_decorator(login_required, name='dispatch')
class LaboratoryRoomReportView(ListView):
    model = LaboratoryRoom
    template_name = "laboratory/report_laboratoryroom_list.html"

    def get_queryset(self):
        lab = get_object_or_404(Laboratory, pk=self.lab)
        return lab.rooms.all()
