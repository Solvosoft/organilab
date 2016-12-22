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


class ObjectView(object):
    model = Object
    template_name_base = "laboratory/objectview"

    def __init__(self):
        class ObjectCreateView(CreateView):

            def get_context_data(self, **kwargs):
                context = super(ObjectCreateView, self).get_context_data(**kwargs)
                if 'lab_pk' in self.kwargs:
                    context['lab_pk'] = self.kwargs.get('lab_pk')
                return context

            def get_success_url(self):
                if 'lab_pk' in self.kwargs:
                    return reverse_lazy('laboratory:objectview_list', kwargs={'lab_pk': self.kwargs.get('lab_pk')})


        self.create = login_required(ObjectCreateView.as_view(
            model=self.model,
            fields="__all__",
            success_url=reverse_lazy('laboratory:objectview_list'),
            template_name=self.template_name_base + "_form.html"
        ))

        class ObjectUpdateView(UpdateView):

            def get_context_data(self, **kwargs):
                context = super(ObjectUpdateView, self).get_context_data(**kwargs)
                if 'lab_pk' in self.kwargs:
                    context['lab_pk'] = self.kwargs.get('lab_pk')
                return context

            def get_success_url(self):
                if 'lab_pk' in self.kwargs:
                    return reverse_lazy('laboratory:objectview_list', kwargs={'lab_pk': self.kwargs.get('lab_pk')})

        self.edit = login_required(ObjectUpdateView.as_view(
            model=self.model,
            fields="__all__",
            success_url=reverse_lazy('laboratory:objectview_list'),
            template_name=self.template_name_base + "_form.html"
        ))

        class ObjectDeleteView(DeleteView):
            def get_success_url(self):
                if 'lab_pk' in self.kwargs:
                    return reverse_lazy('laboratory:objectview_list', kwargs={'lab_pk': self.kwargs.get('lab_pk')})

        self.delete = login_required(ObjectDeleteView.as_view(
            model=self.model,
            success_url=reverse_lazy('laboratory:objectview_list'),
            template_name=self.template_name_base + "_delete.html"
        ))

        class ObjectListView(ListView):

            def get_context_data(self, **kwargs):
                context = super(ObjectListView, self).get_context_data(**kwargs)
                if 'lab_pk' in self.kwargs:
                    context['lab_pk'] = self.kwargs.get('lab_pk')
                return context


            def get_queryset(self):
                lab_pk = self.kwargs.get('lab_pk')
                if lab_pk is not None:
                    return Object.objects.filter(shelfobject__shelf__furniture__labroom__laboratory=lab_pk)
                return super(ObjectListView, self).get_queryset()


        self.list = login_required(ObjectListView.as_view(
            model=self.model,
            paginate_by=10,
            ordering=['code'],
            template_name=self.template_name_base + "_list.html"
        ))

    def get_urls(self):
        return [
            url(r"^list$", self.list,
                name="objectview_list"),
            url(r"^create$", self.create,
                name="objectview_create"),
            url(r"^edit/(?P<pk>\d+)$", self.edit,
                name="objectview_update"),
            url(r"^delete/(?P<pk>\d+)$", self.delete,
                name="objectview_delete"),

        ]
