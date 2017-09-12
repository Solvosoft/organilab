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

from django.views.generic import ListView, FormView

from django.utils.translation import ugettext_lazy as _
from django.db.models.query_utils import Q

from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from django.contrib import messages
from django.core.urlresolvers import reverse

class AccessListLabAdminsView(FormView, ListView):
    model = User
    template_name = 'laboratory/access_list.html'
    lab_pk = None
    paginate_by = 10
    #user_form = UserCreate()
    form_class = UserSearchForm
    second_form_class = UserCreate
    queryset = User.objects.filter(groups__name = 'laboratory_admin')

    def dispatch(self, request, *args, **kwargs):
        self.lab_pk = kwargs.get('lab_pk')
        return super(AccessListLabAdminsView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('laboratory:access_list_lab_admins', kwargs={'lab_pk':self.lab_pk})

    def get_context_data(self, **kwargs):
        context = super(AccessListLabAdminsView, self).get_context_data(**kwargs)
        context['lab_pk'] = self.lab_pk
        context['laboratory'] = self.lab_pk
        context['role'] = 1
        context['user_search'] = self.form_class
        context['user_create'] = self.second_form_class
        context['user_access'] = UserAccessForm()
        return context

    def form_valid(self, form):
        admin_group = Group.objects.get(name='laboratory_admin')
        laboratory = get_object_or_404(Laboratory, pk=self.lab_pk)
        for user in form.cleaned_data['user']:
            userobj = User.objects.get(pk=user)
            userobj.groups.add(admin_group)
            if not laboratory.lab_admins.filter(id=user).exists():
                laboratory.lab_admins.add(user)
        messages.info(self.request, "User added successfully")
        return redirect(self.get_success_url())


class AccessListLaboratoritsView(FormView, ListView):
    model = User
    template_name = 'laboratory/access_list.html'
    lab_pk = None
    paginate_by = 10
    user_form = UserCreate()
    form_class = UserSearchForm
    queryset = User.objects.filter(groups__name = 'laboratory_professor')
    #Change to laboratorist

    def dispatch(self, request, *args, **kwargs):
        self.lab_pk = kwargs.get('lab_pk')
        return super(AccessListLaboratoritsView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('laboratory:access_list_laboratorits', kwargs = {'lab_pk':self.lab_pk})

    def get_context_data(self, **kwargs):
        context = super(AccessListLaboratoritsView, self).get_context_data(**kwargs)
        context['lab_pk'] = self.lab_pk
        context['laboratory'] = self.lab_pk
        context['role'] = 2
        context['user_create'] = self.user_form
        context['user_search'] = self.form_class
        context['user_access'] = UserAccessForm()
        return context

    def form_valid(self, form):
        laboratorist_group = Group.objects.get(name='laboratory_professor')
        laboratory = get_object_or_404(Laboratory, pk=self.lab_pk)
        for user in form.cleaned_data['user']:
            userobj = User.objects.get(pk=user)
            userobj.groups.add(laboratorist_group)
            if not laboratory.laboratorists.filter(id=user).exists():
                laboratory.laboratorists.add(user)
        messages.info(self.request, "User added successfully")
        return redirect(self.get_success_url())

class AccessListStudentsView(FormView, ListView):
    model = User
    template_name = 'laboratory/access_list.html'
    lab_pk = None
    paginate_by = 10
    user_form = UserCreate()
    form_class = UserSearchForm
    queryset = User.objects.filter(groups__name = 'laboratory_student')

    def dispatch(self, request, *args, **kwargs):
        self.lab_pk = kwargs.get('lab_pk')
        return super(AccessListStudentsView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('laboratory:access_list_students', kwargs = {'lab_pk':self.lab_pk})

    def get_context_data(self, **kwargs):
        context = super(AccessListStudentsView, self).get_context_data(**kwargs)
        context['lab_pk'] = self.lab_pk
        context['laboratory'] = self.lab_pk
        context['role'] = 3
        context['user_create'] = self.user_form
        context['user_search'] = self.form_class
        context['user_access'] = UserAccessForm()
        return context

    def form_valid(self, form):
        student_group = Group.objects.get(name='laboratory_student')
        laboratory = get_object_or_404(Laboratory, pk=self.lab_pk)
        for user in form.cleaned_data['user']:
            userobj = User.objects.get(pk=user)
            userobj.groups.add(student_group)
            if not laboratory.students.filter(id=user).exists():
                laboratory.students.add(user)
        messages.info(self.request, "User added successfully")
        return redirect(self.get_success_url())
