from django.contrib.auth.models import User
from djgentelella.groute import register_lookups
from djgentelella.views.select2autocomplete import BaseSelect2View, GPaginator
from rest_framework import generics
from rest_framework.generics import get_object_or_404

from auth_and_perms.models import Rol, ProfilePermission
from auth_and_perms.utils import get_roles_by_user
from laboratory.models import Laboratory, OrganizationStructure
from laboratory.utils import get_profile_by_organization, get_users_from_organization


def str2bool(v):
    v = v or ''
    return v.lower() in ("yes", "true", "t", "1")


class GPaginatorMoreElements(GPaginator):
    page_size = 50

@register_lookups(prefix="rolbase", basename="rolbase")
class RolS2OrgManagement(generics.RetrieveAPIView, BaseSelect2View):
    model = Rol
    fields = ['name']
    organization = None
    pagination_class = GPaginatorMoreElements

    def retrieve(self, request, pk, **kwargs):
        self.organization = pk
        return self.list(request, pk, **kwargs)

    def list(self, request, *args, **kwargs):
        if not args:
            raise
        if self.organization is None:
            raise
        return super().list(request, *args, **kwargs)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        queryset = queryset.filter(organizationstructure=self.organization)
        as_role = str2bool(self.request.GET.get('as_role'))
        if as_role:
            profilepermission = ProfilePermission.objects.filter(
                content_type__app_label=self.request.GET.get('contenttypeobj[appname]'),
                content_type__model=self.request.GET.get('contenttypeobj[model]'),
                object_id=self.request.GET.get('contenttypeobj[objectid]'),
                profile_id=self.request.GET.get('profile')
            ).first()
            if profilepermission:
                self.selected = [str(idpp) for idpp in profilepermission.rol.all().values_list('id', flat=True)]
        return queryset


@register_lookups(prefix="orguserbase", basename="orguserbase")
class UserS2OrgManagement(generics.RetrieveAPIView, BaseSelect2View):
    model = User
    fields = ['username']
    organization = None
    pagination_class = GPaginatorMoreElements

    def retrieve(self, request, pk, **kwargs):
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        return self.list(request, pk, **kwargs)

    def list(self, request, *args, **kwargs):
        if not args:
            raise
        if self.organization is None:
            raise
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        orgs = []
        orgByuser = OrganizationStructure.os_manager.filter_user(self.request.user)
        for org in orgByuser:
            orgs += list(org.descendants())

        users = []
        for org in set(orgs):
            users += list(get_users_from_organization(org.pk, org=org))
        return self.model.objects.filter(pk__in=set(users))

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        profiles = get_profile_by_organization(self.request.GET.get('contenttypeobj[objectid]'))
        #queryset = list(get_users_from_organization(org))
        if profiles:
            self.selected = [str(idpp) for idpp in profiles.values_list('user__id', flat=True)]
        return queryset

    def get_text_display(self, obj):
        return str(obj.profile)

@register_lookups(prefix="groupbase", basename="groupbase")
class GroupS2(BaseSelect2View):
    model = Rol
    fields = ['name']

    def get_queryset(self):
        user = self.request.user
        return get_roles_by_user(user)


@register_lookups(prefix="relorgbase", basename="relorgbase")
class RelOrgBaseS2(generics.RetrieveAPIView, BaseSelect2View):
    model = Laboratory
    fields = ['name']

    def get_queryset(self):
        super().get_queryset()
        ancestors = self.organization.ancestors()
        descendants = self.organization.descendants()
        orgs = [self.organization] + list(ancestors) + list(descendants)
        labs_pk = []
        for organization in orgs:
            labs_pk += list(organization.laboratory_set.all().values_list('pk', flat=True))
        return Laboratory.objects.filter(pk__in=set(labs_pk))

    def retrieve(self, request, pk, **kwargs):
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        return self.list(request, pk, **kwargs)

    def list(self, request, *args, **kwargs):
        if not args:
            raise
        if self.organization is None:
            raise
        return super().list(request, *args, **kwargs)