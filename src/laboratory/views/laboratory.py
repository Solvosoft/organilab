# encoding: utf-8
from django import forms
from django.contrib import messages
from django.contrib.admin.models import CHANGE, ADDITION, DELETION
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models.query_utils import Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy, path
from django.urls.base import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from laboratory.views.djgeneric import CreateView, UpdateView,ListView,DeleteView
from django.views.generic.edit import FormView

from auth_and_perms.models import Profile
from laboratory.decorators import has_lab_assigned
from laboratory.forms import LaboratoryCreate, H_CodeForm, LaboratoryEdit, OrganizationUserManagementForm
from laboratory.models import Laboratory, OrganizationStructure
from laboratory.utils import organilab_logentry
from laboratory.views.laboratory_utils import filter_by_user_and_hcode


@method_decorator(has_lab_assigned(lab_pk='pk'), name='dispatch')
@method_decorator(permission_required('laboratory.change_laboratory'), name='dispatch')
class LaboratoryEdit(UpdateView):
    model = Laboratory
    template_name = 'laboratory/edit.html'
    lab_pk_field = 'pk'

    #fields = ['name', 'phone_number', 'location', 'geolocation']
    form_class = LaboratoryEdit

    def get_context_data(self, **kwargs):
        context = UpdateView.get_context_data(self, **kwargs)
        context['laboratory'] = self.object.pk
        return context

    def get_success_url(self):
        return reverse('laboratory:mylabs',kwargs={'org_pk':self.org})

    def form_valid(self,form):
        laboratory = form.save()
        organilab_logentry(self.request.user, laboratory, CHANGE, changed_data=form.changed_data,
                           relobj=self.object)
        return super(LaboratoryEdit, self).form_valid(form)


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
            path('list', self.list, name='laboratory_list'),
            path('create', self.create, name='laboratory_create'),
            path('edit/<int:pk>/', self.edit, name='laboratory_update'),
            path('delete/<int:pk>/', self.delete, name='laboratory_delete'),
        ]


class SelectLaboratoryForm(forms.Form):
    laboratory = forms.ModelChoiceField(label=_('Laboratory'),
                                        queryset=Laboratory.objects.none(), empty_label=None)

    def __init__(self, *args, **kwargs):
        lab_queryset = kwargs.pop('lab_queryset')
        super(SelectLaboratoryForm, self).__init__(*args, **kwargs)
        self.fields['laboratory'].queryset = lab_queryset


@method_decorator(permission_required('laboratory.view_laboratory'), name='dispatch')
class SelectLaboratoryView(FormView):
    template_name = 'laboratory/select_lab.html'
    form_class = SelectLaboratoryForm
    number_of_labs = 0
    success_url = '/'
    lab_pk_field = 'pk'

    def get_laboratories(self, user):
        organizations = OrganizationStructure.os_manager.filter_user(user)
        # user have perm on that organization ?  else Use assigned user with
        # direct relationship
        if not organizations:
            organizations = []
        labs = Laboratory.objects.filter(Q(profile__user=user) |
                                         Q(organization__in=organizations)
                                         ).distinct()
        return labs

    def get_form_kwargs(self):
        kwargs = super(SelectLaboratoryView, self).get_form_kwargs()
        user = self.request.user
        kwargs['lab_queryset'] = self.get_laboratories(user)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(SelectLaboratoryView, self).get_context_data(**kwargs)
        context['number_of_labs'] = self.number_of_labs
        return context

    def form_valid(self, form):
        lab_pk = form.cleaned_data.get('laboratory').pk
        return redirect('laboratory:labindex', lab_pk)

    def get(self, request, *args, **kwargs):
        labs = self.get_laboratories(request.user)
        self.number_of_labs = labs.count()
        if self.number_of_labs == 1:
            lab_pk = labs.first().pk
            return redirect('laboratory:labindex', lab_pk)
        return FormView.get(self, request, *args, **kwargs)


@method_decorator(permission_required('laboratory.add_laboratory'), name='dispatch')
class CreateLaboratoryFormView(FormView):
    template_name = 'laboratory/laboratory_create.html'
    form_class = LaboratoryCreate
    success_url = ''

 #   def dispatch(self, request, *args, **kwargs):
 #       if not self.request.user.has_perm('laboratory.add_laboratory'):
 #           return render(request, 'laboratory/laboratory_notperm.html')
 #       return super(CreateLaboratoryFormView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CreateLaboratoryFormView, self).get_form_kwargs()
        kwargs['initial'] = {'organization': self.kwargs['org_pk']}
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(CreateLaboratoryFormView, self).get_context_data(**kwargs)
        context['addorgform'] = OrganizationUserManagementForm(prefix='addorg')
        context['org_pk'] = self.kwargs['org_pk']
        return context

    def form_valid(self, form):
        self.object = form.save()
        organilab_logentry(self.request.user, self.object, ADDITION,  changed_data=form.changed_data,
                           relobj=self.object)

        user = self.request.user
        admins = User.objects.filter(is_superuser=True)
        # TODO: This is necesary ?  all user has to be profile
        user.profile.laboratories.add(self.object)
        for admin in admins: 
            if not hasattr(admin, 'profile'):
                admin.profile = Profile.objects.create(user=admin)
            admin.profile.laboratories.add(self.object)
        response = super(CreateLaboratoryFormView, self).form_valid(form)

        return response

    def get_success_url(self):
        messages.success(self.request, _('Laboratory was created successfully'))
        return reverse('auth_and_perms:organizationManager')


@method_decorator(permission_required('laboratory.add_laboratory'), name='dispatch')
class CreateLaboratoryView(CreateView):
    form_class = LaboratoryCreate
    success_url = '/'

    def post(self, request, *args, **kwargs):
        user = self.request.user
        form = self.get_form()
        if request.user.has_perm('laboratory.add_laboratory'):
            if form.is_valid():
                form.save(user)
                return redirect(self.success_url)
        else:
            messages.error(
                request,
                _("Sorry, there is not available laboratory, please contact the administrator and request a laboratory enrollment"))
            # Translate
            return redirect(self.success_url)


@method_decorator(permission_required('laboratory.view_laboratory'), name='dispatch')
class LaboratoryListView(ListView):
    model = Laboratory
    template_name= 'laboratory/laboratory_list.html'
    success_url = '/'
    paginate_by = 15
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(organization__pk=self.org, profile__user=self.request.user)
        q = self.request.GET.get('search_fil', '')
        if q != "":
            queryset = queryset.filter(name__icontains=q) 
        return queryset   


@method_decorator(has_lab_assigned(lab_pk='pk'), name='dispatch')
@method_decorator(permission_required('laboratory.delete_laboratory'), name='dispatch')
class LaboratoryDeleteView(DeleteView):
    model = Laboratory
    template_name= 'laboratory/laboratory_delete.html'
    lab_pk_field = 'pk'

    def get_success_url(self):
        return  "/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['laboratory'] = self.object.pk
        return context

    def form_valid(self, form):
        success_url = self.get_success_url()
        organilab_logentry(self.request.user, self.object, DELETION, relobj=self.object)
        self.object.delete()
        return HttpResponseRedirect(success_url)

@method_decorator(permission_required('laboratory.do_report'), name='dispatch')
class HCodeReports(ListView):
    paginate_by = 15
    template_name = 'laboratory/h_code_report.html'

    def get_queryset(self):
        q = None
        form = H_CodeForm(self.request.GET)
        if form.is_valid():
            q = form.cleaned_data['hcode']
        lista_reactivos = []
        if q:
            lista_reactivos= filter_by_user_and_hcode(self.request.user, q)
        return lista_reactivos

    def get_filter_params(self):
        dev = ''
        form = H_CodeForm(self.request.GET)
        if form.is_valid():
            for code in form.cleaned_data['hcode']:
                dev+='&hcode='+code.code
        return dev

    def get_context_data(self, **kwargs):
        context = super(HCodeReports, self).get_context_data(**kwargs)
        context['form'] = H_CodeForm(self.request.GET)
        context['params'] = self.get_filter_params()
        context['org_pk'] = self.org
        return context
