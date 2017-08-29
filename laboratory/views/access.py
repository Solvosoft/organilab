# encoding: utf-8
from __future__ import unicode_literals

from django import forms
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

from laboratory.models import Laboratory
from django.views.generic import ListView

from django.utils.translation import ugettext_lazy as _
from django.db.models.query_utils import Q

from django.contrib.auth.models import User

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

class AccessListLabAdminsView(ListView):
    model = User
    template_name = 'laboratory/access_list.html'
    lab_pk = None

    def dispatch(self, request, *args, **kwargs):
        self.lab_pk = kwargs.get('lab_pk')
        return super(AccessListLabAdminsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AccessListLabAdminsView, self).get_context_data(**kwargs)
        context['lab_pk'] = self.lab_pk
        context['laboratory'] = self.lab_pk
        context['active'] = 1
        return context

class AccessListLaboratoritsView(ListView):
    model = User
    template_name = 'laboratory/access_list.html'
    lab_pk = None

    def dispatch(self, request, *args, **kwargs):
        self.lab_pk = kwargs.get('lab_pk')
        return super(AccessListLaboratoritsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AccessListLaboratoritsView, self).get_context_data(**kwargs)
        context['lab_pk'] = self.lab_pk
        context['laboratory'] = self.lab_pk
        context['active'] = 2
        return context

class AccessListStudentsView(ListView):
    model = User
    template_name = 'laboratory/access_list.html'
    lab_pk = None
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        self.lab_pk = kwargs.get('lab_pk')
        return super(AccessListStudentsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AccessListStudentsView, self).get_context_data(**kwargs)
        context['lab_pk'] = self.lab_pk
        context['laboratory'] = self.lab_pk
        context['active'] = 3
        return context


class AccessListRelatedLabsView(ListView):
    model = Laboratory
    template_name = 'laboratory/access_list.html'
    lab_pk = None

    def dispatch(self, request, *args, **kwargs):
        self.lab_pk = kwargs.get('lab_pk')
        return super(AccessListRelatedLabsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AccessListRelatedLabsView, self).get_context_data(**kwargs)
        context['lab_pk'] = self.lab_pk
        context['laboratory'] = self.lab_pk
        context['active'] = 4
        return context
