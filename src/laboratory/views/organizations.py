# encoding: utf-8
"""
Created on 26/12/2016

@author: luisza
"""
from __future__ import unicode_literals

from django.contrib.admin.models import DELETION, ADDITION, CHANGE
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView, CreateView, UpdateView, FormView

from auth_and_perms.forms import (
    OrganizationActions,
    OrganizationActionsClone,
    OrganizationActionsWithoutInactive,
)
from auth_and_perms.models import Rol
from auth_and_perms.node_tree import get_descendants_by_org
from auth_and_perms.organization_utils import user_is_allowed_on_organization
from auth_and_perms.views.user_org_creation import set_rol_administrator_on_org
from laboratory.models import (
    Laboratory,
    OrganizationStructure,
    OrganizationStructureRelations,
    UserOrganization,
)
from ..forms import AddOrganizationForm, ChangeOrganizationParentForm
from ..utils import organilab_logentry


@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required(
        "laboratory.delete_organizationstructure", raise_exception=True
    ),
    name="dispatch",
)
class OrganizationDeleteView(DeleteView):
    model = OrganizationStructure
    success_url = reverse_lazy("auth_and_perms:organizationManager")

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
        organilab_logentry(
            self.request.user,
            self.object,
            DELETION,
            "organization structure",
            changed_data=["name"],
            change_message=_("Deleted organization '%(name)s'")
            % {"name": self.object.name},
        )
        self.object.delete()
        return HttpResponseRedirect(success_url)


@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("laboratory.add_organizationstructure", raise_exception=True),
    name="dispatch",
)
class OrganizationCreateView(CreateView):
    model = OrganizationStructure
    success_url = reverse_lazy("auth_and_perms:organizationManager")
    form_class = AddOrganizationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.parent:
            self.object.position = self.object.parent.last_child_position + 1
            self.object.save()
        set_rol_administrator_on_org(self.request.user.profile, self.object)
        organilab_logentry(
            self.request.user,
            self.object,
            ADDITION,
            "organization structure",
            changed_data=["organization", "users"],
            change_message=_("Created organization '%(name)s'")
            % {"name": self.object.name},
        )
        return response


@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required(
        "laboratory.change_organizationstructure", raise_exception=True
    ),
    name="dispatch",
)
class OrganizationActionsFormview(FormView):
    form_class = OrganizationActions

    def get_form(self):
        if self.request.method == "POST":
            prefix = self.request.POST.get("prefix")
            if prefix == "clone":
                self.form_class = OrganizationActionsClone
            if prefix == "wi":
                self.form_class = OrganizationActionsWithoutInactive
        return super().get_form(form_class=self.form_class)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == "POST":
            prefix = self.request.POST.get("prefix")
            kwargs["prefix"] = prefix
        return kwargs

    def inactive_organization(self, form):
        self.org.active = False
        if self.org.parent:
            self.org.position = self.org.parent.min_child_position - 1
        self.org.save()
        organilab_logentry(
            self.request.user,
            self.org,
            CHANGE,
            "inactive organization",
            changed_data=["active"],
            change_message=_("Deactivated organization '%(name)s'")
            % {"name": self.org.name},
        )

    def active_organization(self, form):
        self.org.active = True
        if self.org.parent:
            self.org.position = self.org.parent.last_child_position + 1
        self.org.save()
        organilab_logentry(
            self.request.user,
            self.org,
            CHANGE,
            "active organization",
            changed_data=["active"],
            change_message=_("Activated organization '%(name)s'")
            % {"name": self.org.name},
        )

    def clone_organization(self, form):
        newinstance = OrganizationStructure.objects.create(
            name=self.org.name + "-clone",
            position=self.org.position,
            level=self.org.level,
            active=True,
            parent=self.org.parent,
        )
        newinstance.users.add(self.request.user)
        organilab_logentry(
            self.request.user,
            newinstance,
            ADDITION,
            "clone organization structure",
            changed_data=["name", "position", "level", "active", "parent", "users"],
            change_message=_("Cloned organization '%(original)s' to '%(clone)s'")
            % {"original": self.org.name, "clone": newinstance.name},
        )

        for orgrel in OrganizationStructureRelations.objects.filter(
            organization=self.org
        ):
            org_relation = OrganizationStructureRelations.objects.create(
                organization=newinstance,
                content_type=orgrel.content_type,
                object_id=orgrel.object_id,
            )
            organilab_logentry(
                self.request.user,
                org_relation,
                ADDITION,
                "organization structure relations",
                changed_data=["organization", "content_type", "object_id"],
                change_message=_("Created organization relation for '%(org)s'")
                % {"org": newinstance.name},
                relobj=newinstance,
            )

        for role in self.org.root.rol.prefetch_related("permissions"):
            new_role = Rol.objects.create(name=role.name, color=role.color)
            new_role.permissions.add(*role.permissions.all())
            newinstance.rol.add(new_role)
            organilab_logentry(
                self.request.user,
                new_role,
                ADDITION,
                "rol",
                changed_data=["name", "color", "permissions"],
                change_message=_("Created role '%(name)s' for organization '%(org)s'")
                % {"name": new_role.name, "org": newinstance.name},
                relobj=newinstance,
            )

        for user in UserOrganization.objects.filter(
            organization=self.org,
            type_in_organization__in=[
                UserOrganization.ADMINISTRATOR,
                UserOrganization.LABORATORY_MANAGER,
                UserOrganization.LABORATORY_USER,
            ],
        ).select_related("user"):
            user_org = UserOrganization.objects.create(
                organization=newinstance,
                type_in_organization=user.type_in_organization,
                user=user.user,
                status=user.status,
            )

            organilab_logentry(
                self.request.user,
                user_org,
                ADDITION,
                "user organization",
                changed_data=["organization", "type_in_organization", "user", "status"],
                change_message=_("Added user '%(user)s' to cloned organization '%(org)s'")
                % {"user": user.user.username, "org": newinstance.name},
                relobj=newinstance,
            )

            newinstance.users.add(user.user)

    def change_name_organization(self, form):
        self.org.name = form.cleaned_data["name"]
        self.org.save()
        organilab_logentry(
            self.request.user,
            self.org,
            CHANGE,
            "change name organization",
            changed_data=["name"],
            change_message=_("Changed organization name to '%(name)s'")
            % {"name": self.org.name},
        )

    def form_valid(self, form):
        self.org = form.cleaned_data["action_organization"]
        user_is_allowed_on_organization(self.request.user, self.org)

        if form.cleaned_data["actions"] == "1":
            self.inactive_organization(form)
        elif form.cleaned_data["actions"] == "2":
            self.clone_organization(form)
        elif form.cleaned_data["actions"] == "3":
            self.change_name_organization(form)
        elif form.cleaned_data["actions"] == "4":
            self.active_organization(form)
        return redirect(reverse_lazy("auth_and_perms:organizationManager"))

    def form_invalid(self, form):

        return redirect(reverse_lazy("auth_and_perms:organizationManager"))


@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required(
        "laboratory.change_organizationstructure", raise_exception=True
    ),
    name="dispatch",
)
class OrganizationUpdateView(UpdateView):
    model = OrganizationStructure
    success_url = reverse_lazy("auth_and_perms:organizationManager")
    form_class = ChangeOrganizationParentForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        user_is_allowed_on_organization(request.user, self.object)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.was_root = self.object.root.pk == self.object.pk
        self.old_root = self.object.root
        user_is_allowed_on_organization(request.user, self.object)
        return super().post(request, *args, **kwargs)

    def transfer_resources_to_new_root(self, old_org, new_root):
        """Transfiere users, roles y laboratorios al nuevo root."""
        for rol in old_org.rol.all():
            new_root.rol.add(rol)
            organilab_logentry(
                self.request.user,
                rol,
                CHANGE,
                "rol",
                changed_data=["organizationstructure"],
                change_message=_("Transferred role '%(role)s' to organization '%(org)s'")
                % {"role": rol.name, "org": new_root.name},
            )

        for user in old_org.users.all():
            new_root.users.add(user)
            UserOrganization.objects.get_or_create(
                user=user,
                organization=new_root,
                defaults={"type_in_organization": UserOrganization.LABORATORY_USER},
            )
            organilab_logentry(
                self.request.user,
                user,
                CHANGE,
                "user",
                changed_data=["organization"],
                change_message=_("Transferred user '%(user)s' to organization '%(org)s'")
                % {"user": user.username, "org": new_root.name},
            )

        lab_content_type = ContentType.objects.get_for_model(Laboratory)
        for lab in old_org.laboratory_set.all():
            OrganizationStructureRelations.objects.get_or_create(
                organization=new_root,
                content_type=lab_content_type,
                object_id=lab.pk,
            )
            organilab_logentry(
                self.request.user,
                lab,
                CHANGE,
                "laboratory",
                changed_data=["organization_relation"],
                change_message=_("Created lab relation for '%(lab)s' in '%(org)s'")
                % {"lab": lab.name, "org": new_root.name},
            )

    def form_valid(self, form):
        new_parent = form.cleaned_data.get("parent")

        response = super().form_valid(form)

        if self.was_root and new_parent is not None:
            new_root = new_parent.root
            self.transfer_resources_to_new_root(self.old_root, new_root)

        organilab_logentry(
            self.request.user,
            self.object,
            CHANGE,
            "organization structure",
            changed_data=form.changed_data,
            change_message=_("Updated organization '%(name)s'")
            % {"name": self.object.name},
        )
        return response
