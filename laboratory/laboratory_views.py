# encoding: utf-8
from __future__ import unicode_literals

from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.views.generic import UpdateView
from django.views.generic.edit import DeleteView
from django.views.generic.list import ListView

from laboratory.models import Laboratory


class LaboratoryView(object):
    model = Laboratory
    template_name_base = 'laboratory/laboratory_'

    def __init__(self):
        self.create = login_required(CreateView.as_view(
            model=self.model,
            fields=('name',),
            success_url=reverse_lazy('laboratory:laboratory_list'),
            template_name=self.template_name_base + 'form.html'
        ))

        self.edit = login_required(UpdateView.as_view(
            model=self.model,
            fields=('name',),
            success_url=reverse_lazy('laboratory:laboratory_list'),
            template_name=self.template_name_base + 'form.html'
        ))

        self.delete = login_required(DeleteView.as_view(
            model=self.model,
            success_url=reverse_lazy('laboratory:laboratory_list'),
            template_name=self.template_name_base + 'delete.html'
        ))

        self.list = login_required(ListView.as_view(
            model=self.model,
            paginate_by=10,
            template_name=self.template_name_base + 'list.html'
        ))


    def get_urls(self):
        return [
            url(r'^list', self.list, name='laboratory_list'),
            url(r'^create', self.create, name='laboratory_create'),
            url(r'^edit/(?P<pk>\d+)$', self.edit, name='laboratory_update'),
            url(r'^delete/(?P<pk>\d+)$', self.delete, name='laboratory_delete'),
        ]