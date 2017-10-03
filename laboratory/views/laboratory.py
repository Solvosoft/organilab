# encoding: utf-8
from __future__ import unicode_literals

from django import forms
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404, render_to_response
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView
from django.utils.translation import ugettext_lazy as _
from django.db.models.query_utils import Q
from laboratory.models import Laboratory
from django.template.loader import render_to_string
from django_ajax.decorators import ajax
from laboratory.forms import UserCreate, UserSearchForm, LaboratoryCreate
from django.contrib.auth.models import User, Permission

def render_admins_lab(request, object_list, lab, message=None):
    return {
        'inner-fragments':{
            '#admin_lab_users':render_to_string(
            'ajax/lab_admins_list.html',
            context = {
                'object_list' : object_list,
                'lab': lab,
                'message':message
            },
            request = request,
            )
        }
    }

@ajax
def create_admins_user(request, pk):
    lab = get_object_or_404(Laboratory, pk=pk)
    message = None
    if request.method == 'POST':
        form = UserCreate(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                form.cleaned_data['username'],
                form.cleaned_data['email'],
                form.cleaned_data['password']
            )
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()
            lab.lab_admins.add()
            message = "User added successfully"
        else:
            message = "Something went wrong"
    else:
        message = "Sorry, wrong method"
    return render_admins_lab(request, lab.lab_admins.all(), lab, message=message)

@ajax
def get_create_admis_user(request,pk):
    lab = get_object_or_404(Laboratory, pk=pk)
    usersearchform = UserSearchForm()
    usercreateform = UserCreate()
    return {
        'inner-fragments':{
            '#admin_lab_users':render_to_string(
            'ajax/lab_admins_create.html',
            context = {
                'usersearchform' : usersearchform,
                'usercreateform' : usercreateform,
                'lab':lab
            },
            request = request,
            )
        }
    }

@ajax
def del_admins_user(request, pk, pk_user):
    lab = get_object_or_404(Laboratory, pk=pk)
    lab.lab_admins.filter(pk=pk_user).delete()
    return render_admins_lab(request, lab.lab_admins.all(), lab)

@ajax
def admin_users(request, pk):
    lab = get_object_or_404(Laboratory, pk=pk)
    return render_admins_lab(request, lab.lab_admins.all(), lab)

class LaboratoryEdit(UpdateView):
    model = Laboratory
    template_name = 'laboratory/edit.html'
    fields = ['name']

    def get_context_data(self, **kwargs):
        context = UpdateView.get_context_data(self, **kwargs)
        context['laboratory'] = self.object.pk
        return context


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
            url(r'^delete/(?P<pk>\d+)$', self.delete,
                name='laboratory_delete'),
        ]


class SelectLaboratoryForm(forms.Form):
    laboratory = forms.ModelChoiceField(label=_('Laboratory'),
                                        queryset=Laboratory.objects.all(), empty_label=None)

    def __init__(self, *args, **kwargs):
        lab_queryset = kwargs.pop('lab_queryset')
        super(SelectLaboratoryForm, self).__init__(*args, **kwargs)
        self.fields['laboratory'].queryset = lab_queryset



@method_decorator(login_required, name='dispatch')
class SelectLaboratoryView(FormView):
    template_name = 'laboratory/select_lab.html'
    form_class = SelectLaboratoryForm
    number_of_labs = 0
    create_lab_form = LaboratoryCreate
    success_url = '/'

    def get_laboratories(self, user):
        return Laboratory.objects.filter(Q(laboratorists__pk = user.pk) |  Q(students__pk = user.pk) | Q(lab_admins__pk = user.pk)).distinct()

    def get_form_kwargs(self):
        kwargs = super(SelectLaboratoryView, self).get_form_kwargs()
        user = self.request.user
        kwargs['lab_queryset'] = self.get_laboratories(user)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(SelectLaboratoryView, self).get_context_data(**kwargs)
        context['create_lab_form'] = self.create_lab_form()
        context['number_of_labs'] = self.number_of_labs
        return context

    def form_valid(self, form):
        lab_pk = form.cleaned_data.get('laboratory').pk
        request = self.request
        request.session['lab_pk'] = lab_pk
        return redirect('laboratory:index', lab_pk)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        create_lab_form = self.create_lab_form(request.POST)
        if user.has_perm('laboratory.add_laboratory'):
            if create_lab_form.is_valid():
                create_lab_form.save(user)
                return redirect(self.get_success_url())
        else:
            return redirect(self.get_success_url())

    def get(self, request, *args, **kwargs):
        labs = self.get_laboratories(request.user)
        self.number_of_labs = labs.count()
        if self.number_of_labs == 1:
            lab_pk = labs.first().pk
            request.session['lab_pk'] = lab_pk
            return redirect('laboratory:index', lab_pk)

        return FormView.get(self, request, *args, **kwargs)
