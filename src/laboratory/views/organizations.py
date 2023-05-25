# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''
from __future__ import unicode_literals

from django.contrib.admin.models import DELETION, ADDITION, CHANGE
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import DeleteView, CreateView, UpdateView

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from auth_and_perms.views.user_org_creation import set_rol_administrator_on_org
from laboratory.models import OrganizationStructure
from ..forms import AddOrganizationForm
from ..utils import organilab_logentry


@method_decorator(permission_required('laboratory.delete_organizationstructure'), name='dispatch')
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
        organilab_logentry(self.request.user, self.object, DELETION, 'organization structure')
        self.object.delete()
        return HttpResponseRedirect(success_url)

@method_decorator(permission_required('laboratory.add_organizationstructure'), name='dispatch')
class OrganizationCreateView(CreateView):
    model = OrganizationStructure
    success_url = reverse_lazy('auth_and_perms:organizationManager')
    form_class = AddOrganizationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.parent:
            self.object.position=self.object.parent.position+1
            self.object.save()
        set_rol_administrator_on_org(self.request.user.profile, self.object)
        organilab_logentry(self.request.user, self.object, ADDITION, 'organization structure', changed_data=['organization', 'users'])
        return response


@method_decorator(permission_required('laboratory.change_organizationstructure'), name='dispatch')
class OrganizationUpdateView(UpdateView):
    model = OrganizationStructure
    success_url = reverse_lazy('auth_and_perms:organizationManager')
    form_class = AddOrganizationForm

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
        organilab_logentry(self.request.user, self.object, CHANGE, 'organization structure', changed_data=form.changed_data)
        return response