# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''
from __future__ import unicode_literals
from django.contrib.auth.decorators import permission_required
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django import forms
from django.views.generic import DeleteView, CreateView, UpdateView
from djgentelella.forms.forms import GTForm
from tree_queries.forms import TreeNodeChoiceField
from djgentelella.widgets import core as genwidget
from laboratory.models import Laboratory, OrganizationStructure, OrganizationUserManagement
from auth_and_perms.models import Profile
from .djgeneric import ListView
from laboratory.decorators import has_lab_assigned
from djgentelella.widgets import core as genwidgets
from django.utils.translation import gettext_lazy as _

from ..forms import AddOrganizationForm


class OrganizationSelectableForm(GTForm, forms.Form):
    organizations = OrganizationStructure.objects.none()
    filter_organization = TreeNodeChoiceField(queryset=organizations, widget=genwidgets.Select, label=_("Filter Organization"))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(OrganizationSelectableForm, self).__init__(*args, **kwargs)
        organizations = OrganizationStructure.os_manager.filter_user(self.user)
        if organizations:
            self.fields['filter_organization'].queryset = organizations.distinct()
        elif self.user.is_superuser:
            self.fields['filter_organization'].queryset = OrganizationStructure.objects.all(
            )


@method_decorator(has_lab_assigned(), name='dispatch')
@method_decorator(permission_required('laboratory.view_report'), name='dispatch')
class OrganizationReportView(ListView):
    model = Laboratory
    template_name = "laboratory/report_organizationlaboratory_list.html"
    organization = None

    def get_context_data(self, **kwargs):
        context = super(OrganizationReportView,
                        self).get_context_data(**kwargs)
        context['form'] = self.form

        # start report checking  technician
        if self.profile:
            if self.organization:  # when a organizations is selected
                organizations_child = OrganizationStructure.os_manager.filter_user(
                    self.user)
                if self.organization in organizations_child:  # user have perm on that organization ?
                    organizations_child = self.organization.descendants(
                        include_self=True)
                    labs = Laboratory.objects.filter(
                        organization__in=organizations_child)
                else:
                    labs = Laboratory.objects.none()
            else:  # filter all of technician
                organizations_child = list(OrganizationStructure.os_manager.filter_user(
                    self.user).values_list('pk', flat=True))
                if organizations_child:  # show organizations laboratories
                    labs = Laboratory.objects.filter(
                        organization__in=organizations_child)
                else:  # show only assign laboratory
                    labs = Profile.objects.filter(user=self.user).first().laboratories.all()
        #  when have nothing assign
        else:
            # Show all to admin user
            if self.user.is_superuser:
                if self.organization:
                    organizations_child = self.organization.descendants(
                        include_self=True)
                    labs = Laboratory.objects.filter(
                        organization__in=organizations_child)
                else:
                    labs = Laboratory.objects.all()
            # Dont show if have nothing
            else:
                labs = Laboratory.objects.none()

        context['filter_organization'] = self.organization
        context['object_list'] = labs
        return context

    def get(self, request, *args, **kwargs):
        self.user = request.user
        self.profile = Profile.objects.filter(
            user=request.user)
        self.form = OrganizationSelectableForm(
            request.user, request.GET or None)

        return super(OrganizationReportView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.user = request.user
        self.profile = Profile.objects.filter(
            user=request.user)
        self.form = OrganizationSelectableForm(
            request.user, request.POST or None)

        if self.form.is_valid():
            self.organization = self.form.cleaned_data['filter_organization']

        return super(OrganizationReportView, self).get(request, *args, **kwargs)


@method_decorator(permission_required('laboratory.delete_organizationstructure'), name='dispatch')
class OrganizationDeleteView(DeleteView):
    model = OrganizationStructure
    success_url = reverse_lazy('auth_and_perms:organizationManager')

@method_decorator(permission_required('laboratory.add_organizationstructure'), name='dispatch')
class OrganizationCreateView(CreateView):
    model = OrganizationStructure
    success_url = reverse_lazy('auth_and_perms:organizationManager')
    form_class = AddOrganizationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        orguserman=OrganizationUserManagement.objects.create(
            organization=self.object
        )
        orguserman.users.add(self.request.user)
        return response


@method_decorator(permission_required('laboratory.change_organizationstructure'), name='dispatch')
class OrganizationUpdateView(UpdateView):
    model = OrganizationStructure
    success_url = reverse_lazy('auth_and_perms:organizationManager')
    form_class = AddOrganizationForm

