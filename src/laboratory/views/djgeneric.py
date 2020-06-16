# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''

from django.utils import timezone
from django.views.generic import DetailView as djDetailView
from django.views.generic.edit import CreateView as djCreateView
from django.views.generic.edit import DeleteView as djDeleteView
from django.views.generic.edit import UpdateView as djUpdateView
from django.views.generic.list import ListView as djListView


class CreateView(djCreateView):
    def get(self, request, *args, **kwargs):
        self.lab = kwargs['lab_pk']
        return djCreateView.get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.lab = kwargs['lab_pk']
        return djCreateView.post(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = djCreateView.get_context_data(self, **kwargs)
        context['laboratory'] = int(self.lab)
        return context


class UpdateView(djUpdateView):
    def get(self, request, *args, **kwargs):
        self.lab = kwargs['lab_pk']
        return djUpdateView.get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.lab = kwargs['lab_pk']
        return djUpdateView.post(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = djUpdateView.get_context_data(self, **kwargs)
        context['laboratory'] = self.lab
        return context


class DeleteView(djDeleteView):
    def get(self, request, *args, **kwargs):
        self.lab = kwargs['lab_pk']
        return djDeleteView.get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.lab = kwargs['lab_pk']
        return djDeleteView.post(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = djDeleteView.get_context_data(self, **kwargs)
        context['laboratory'] = self.lab
        return context


class ListView(djListView):
    def get(self, request, *args, **kwargs):
        self.lab = kwargs['lab_pk']
        return djListView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = djListView.get_context_data(self, **kwargs)
        context['laboratory'] = self.lab
        context['datetime'] = timezone.now()
        return context

class DetailView(djDetailView):
    def get(self, request, *args, **kwargs):
        self.lab = kwargs['lab_pk']
        return djDetailView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = djDetailView.get_context_data(self, **kwargs)
        context['laboratory'] = self.lab
        context['datetime'] = timezone.now()
        return context