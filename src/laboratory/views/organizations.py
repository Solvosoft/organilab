# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django import forms
from mptt.forms import TreeNodeChoiceField
from laboratory.models import Laboratory, OrganizationStructure, Profile
#from laboratory.decorators import check_lab_permissions, user_lab_perms

from .djgeneric import ListView

from laboratory.decorators import user_group_perms


class OrganizationSelectableForm(forms.Form):
    organizations = OrganizationStructure.objects.none()
    filter_organization = TreeNodeChoiceField(queryset=organizations)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(OrganizationSelectableForm, self).__init__(*args, **kwargs)
        organizations = OrganizationStructure.os_manager.filter_user(self.user)
        if organizations:
            self.fields['filter_organization'].queryset = organizations.distinct()
        elif self.user.is_superuser:
            self.fields['filter_organization'].queryset = OrganizationStructure.objects.all(
            )


@method_decorator(login_required, name='dispatch')
@method_decorator(user_group_perms(perm='laboratory.view_report'), name='dispatch')
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
                    organizations_child = self.organization.get_descendants(
                        include_self=True)
                    labs = Laboratory.objects.filter(
                        organization__in=organizations_child)
                else:
                    labs = Laboratory.objects.none()
            else:  # filter all of technician
                organizations_child = OrganizationStructure.os_manager.filter_user(
                    self.user)
                if organizations_child:      # show organizations laboratories
                    labs = Laboratory.objects.filter(
                        organization__in=organizations_child)
                else:    # show only assign laboratory
                    labs = Profile.objects.filter(user=self.user).first().laboratories.all()
        #  when have nothing assign
        else:
            # Show all to admin user
            if self.user.is_superuser:
                if self.organization:
                    organizations_child = self.organization.get_descendants(
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
