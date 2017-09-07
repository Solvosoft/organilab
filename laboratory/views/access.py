# encoding: utf-8
from __future__ import unicode_literals

from django import forms
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

from laboratory.models import Laboratory
from laboratory.forms import UserCreate, UserSearchForm, UserAccessForm

from django.views.generic import ListView

from django.utils.translation import ugettext_lazy as _
from django.db.models.query_utils import Q

from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

class AccessListLabAdminsView(ListView):
    model = User
    template_name = 'laboratory/access_list.html'
    lab_pk = None
    #queryset = User.objects.filter(groups__name='laboratory_admin')
    user_form = UserCreate()

    def dispatch(self, request, *args, **kwargs):
        self.lab_pk = kwargs.get('lab_pk')
        return super(AccessListLabAdminsView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('access_list_lab_admins', kwargs={'pk': self.lab_pk})

    def get_context_data(self, **kwargs):
        context = super(AccessListLabAdminsView, self).get_context_data(**kwargs)
        context['lab_pk'] = self.lab_pk
        context['laboratory'] = self.lab_pk
        context['role'] = 1
        context['user_create'] = self.user_form
        context['user_search'] = UserSearchForm()
        context['user_access'] = UserAccessForm()
        return context

    def post(self, request, *args, **kwargs):
        form = self.user_form(request.POST)
        if form.is_valid():
            form.save()
            form.cleaned_data()

class AccessListLaboratoritsView(ListView):
    model = User
    template_name = 'laboratory/access_list.html'
    lab_pk = None
    #queryset = User.objects.filter(groups__name='laboratory_professor')

    def dispatch(self, request, *args, **kwargs):
        self.lab_pk = kwargs.get('lab_pk')
        return super(AccessListLaboratoritsView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('access_list_laboratorits', kwargs={'pk': self.lab_pk})

    def get_context_data(self, **kwargs):
        context = super(AccessListLaboratoritsView, self).get_context_data(**kwargs)
        context['lab_pk'] = self.lab_pk
        context['laboratory'] = self.lab_pk
        context['role'] = 2
        context['user_create'] = UserCreate()
        context['user_search'] = UserSearchForm()
        context['user_access'] = UserAccessForm()
        return context

    def post(self, request, *args, **kwargs):
        form = self.user_form(request.POST)
        if form.is_valid():
            form.save()
            form.cleaned_data()

class AccessListStudentsView(ListView):
    model = User
    template_name = 'laboratory/access_list.html'
    lab_pk = None
    paginate_by = 10
    #queryset = User.objects.filter(groups__name='laboratory_student')

    def dispatch(self, request, *args, **kwargs):
        self.lab_pk = kwargs.get('lab_pk')
        return super(AccessListStudentsView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('access_list_students', kwargs={'pk': self.lab_pk})

    def get_context_data(self, **kwargs):
        context = super(AccessListStudentsView, self).get_context_data(**kwargs)
        context['lab_pk'] = self.lab_pk
        context['laboratory'] = self.lab_pk
        context['role'] = 3
        context['user_create'] = UserCreate()
        context['user_search'] = UserSearchForm()
        context['user_access'] = UserAccessForm()
        return context

    def post(self, request, *args, **kwargs):
        form = self.user_form(request.POST)
        if form.is_valid():
            form.save()
            form.cleaned_data()
