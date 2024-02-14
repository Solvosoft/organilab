# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''
from __future__ import unicode_literals

from django import forms
from django.contrib.admin.models import DELETION, ADDITION, CHANGE
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView, CreateView, UpdateView, FormView
from djgentelella.forms.forms import GTForm
from djgentelella.widgets import core as genwidgets
from tree_queries.forms import TreeNodeChoiceField

from auth_and_perms.forms import OrganizationActions, OrganizationActionsClone, \
    OrganizationActionsWithoutInactive
from auth_and_perms.models import Profile, Rol
from auth_and_perms.node_tree import get_descendants_by_org
from auth_and_perms.organization_utils import user_is_allowed_on_organization
from auth_and_perms.views.user_org_creation import set_rol_administrator_on_org
from laboratory.models import Laboratory, OrganizationStructure, \
    OrganizationStructureRelations, UserOrganization
from .djgeneric import ListView
from ..forms import AddOrganizationForm, ChangeOrganizationParentForm
from ..utils import organilab_logentry


class OrganizationSelectableForm(GTForm, forms.Form):
    organizations = OrganizationStructure.objects.none()
    filter_organization = TreeNodeChoiceField(queryset=organizations,
                                              widget=genwidgets.Select,
                                              label=_("Filter Organization"))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(OrganizationSelectableForm, self).__init__(*args, **kwargs)
        organizations = OrganizationStructure.os_manager.filter_user(self.user)
        if organizations:
            self.fields['filter_organization'].queryset = organizations.distinct()
        elif self.user.is_superuser:
            self.fields[
                'filter_organization'].queryset = OrganizationStructure.objects.all(
            )


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
                    labs = Profile.objects.filter(
                        user=self.user).first().laboratories.all()
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


@method_decorator(permission_required('laboratory.delete_organizationstructure'),
                  name='dispatch')
class OrganizationDeleteView(DeleteView):
    model = OrganizationStructure
    success_url = reverse_lazy('auth_and_perms:organizationManager')

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        user_is_allowed_on_organization(request.user, self.object)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        user_is_allowed_on_organization(request.user, self.object)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        success_url = self.get_success_url()
        organilab_logentry(self.request.user, self.object, DELETION,
                           'organization structure')
        self.object.delete()
        return HttpResponseRedirect(success_url)


@method_decorator(permission_required('laboratory.add_organizationstructure'),
                  name='dispatch')
class OrganizationCreateView(CreateView):
    model = OrganizationStructure
    success_url = reverse_lazy('auth_and_perms:organizationManager')
    form_class = AddOrganizationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.parent:
            self.object.position = self.object.parent.last_child_position + 1
            self.object.save()
        set_rol_administrator_on_org(self.request.user.profile, self.object)
        organilab_logentry(self.request.user, self.object, ADDITION,
                           'organization structure',
                           changed_data=['organization', 'users'])
        return response


@method_decorator(permission_required('laboratory.change_organizationstructure'),
                  name='dispatch')
class OrganizationActionsFormview(FormView):
    form_class = OrganizationActions

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if self.request.method == "POST":
            prefix = self.request.POST.get("prefix")
            kwargs["prefix"] = prefix

            if prefix == "clone":
                self.form_class = OrganizationActionsClone

            if prefix == "wi":
                self.form_class = OrganizationActionsWithoutInactive

        return kwargs

    def inactive_organization(self, form):
        self.org.active = False
        if self.org.parent:
            self.org.position = self.org.parent.min_child_position - 1
        self.org.save()
        organilab_logentry(self.request.user, self.org, CHANGE,
                           'inactive organization',
                           changed_data=['organization'])

    def clone_organization(self, form):
        newinstance = OrganizationStructure.objects.create(
            name=self.org.name + "-clone",
            position=self.org.position,
            level=self.org.level,
            active=True,
            parent=self.org.parent
        )
        newinstance.users.add(self.request.user)
        organilab_logentry(self.request.user, newinstance, ADDITION,
                           'clone organization structure',
                           changed_data=['name', 'position', 'level', 'active', 'parent', 'users'])

        for orgrel in OrganizationStructureRelations.objects.filter(
            organization=self.org):
            org_relation = OrganizationStructureRelations.objects.create(
                organization=newinstance,
                content_type=orgrel.content_type,
                object_id=orgrel.object_id
            )
            organilab_logentry(self.request.user, org_relation, ADDITION,
                               'organization structure relations',
                               changed_data=['organization', 'content_type', 'object_id'],
                               relobj=newinstance)

        for role in self.org.rol.all():
            new_role = Rol.objects.create(
                name=role.name,
                color=role.color
            )
            new_role.permissions.add(*role.permissions.all())
            newinstance.rol.add(new_role)
            organilab_logentry(self.request.user, new_role, ADDITION, 'rol',
                               changed_data=['name', 'color', 'permissions'],
                               relobj=newinstance)

        for user in UserOrganization.objects.filter(organization=self.org,
                                                    type_in_organization__in=[
                                                        UserOrganization.ADMINISTRATOR,
                                                        UserOrganization.LABORATORY_MANAGER]):
            user_org = UserOrganization.objects.create(
                organization=newinstance,
                type_in_organization=user.type_in_organization,
                user=user.user,
                status=user.status)

            organilab_logentry(self.request.user, user_org, ADDITION,
                               'user organization',
                               changed_data=['organization', 'type_in_organization',
                                             'user', 'status'],
                               relobj=newinstance)

            newinstance.users.add(user.user)

    def change_name_organization(self, form):
        self.org.name = form.cleaned_data['name']
        self.org.save()
        organilab_logentry(self.request.user, self.org, ADDITION,
                           'change name organization',
                           changed_data=['organization'])

    def form_valid(self, form):
        self.org = form.cleaned_data['action_organization']
        user_is_allowed_on_organization(self.request.user, self.org)

        if form.cleaned_data['actions'] == '1':
            self.inactive_organization(form)
        elif form.cleaned_data['actions'] == '2':
            self.clone_organization(form)
        elif form.cleaned_data['actions'] == '3':
            self.change_name_organization(form)

        return redirect(reverse_lazy('auth_and_perms:organizationManager'))


@method_decorator(permission_required('laboratory.change_organizationstructure'),
                  name='dispatch')
class OrganizationUpdateView(UpdateView):
    model = OrganizationStructure
    success_url = reverse_lazy('auth_and_perms:organizationManager')
    form_class = ChangeOrganizationParentForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        user_is_allowed_on_organization(request.user, self.object)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        user_is_allowed_on_organization(request.user, self.object)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        organilab_logentry(self.request.user, self.object, CHANGE,
                           'organization structure', changed_data=form.changed_data)
        return response
