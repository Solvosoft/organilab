# encoding: utf-8

'''
Free as freedom will be 26/8/2016

@author: luisza
'''

from __future__ import unicode_literals
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from laboratory.models import Object
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator


class ObjectView(object):
    model = Object
    template_name_base = "laboratory/objectview"

    def __init__(self):
        self.create = login_required(CreateView.as_view(
            model=self.model,
            fields="__all__",
            success_url=reverse_lazy('laboratory:objectview_list'),
            template_name=self.template_name_base + "_form.html"
        ))

        self.edit = login_required(UpdateView.as_view(
            model=self.model,
            fields="__all__",
            success_url=reverse_lazy('laboratory:objectview_list'),
            template_name=self.template_name_base + "_form.html"
        ))

        self.delete = login_required(DeleteView.as_view(
            model=self.model,
            success_url=reverse_lazy('laboratory:objectview_list'),
            template_name=self.template_name_base + "_delete.html"
        ))

        self.list = login_required(ListView.as_view(
            model=self.model,
            paginate_by=10,
            ordering=['code'],
            template_name=self.template_name_base + "_list.html"
        ))

    def get_urls(self):
        return [
            url(r"^objectview/list$", self.list,
                name="objectview_list"),
            url(r"^objectview/create$", self.create,
                name="objectview_create"),
            url(r"^objectview/edit/(?P<pk>\d+)$", self.edit,
                name="objectview_update"),
            url(r"^objectview/delete/(?P<pk>\d+)$", self.delete,
                name="objectview_delete"),

        ]
