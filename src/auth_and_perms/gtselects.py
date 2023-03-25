from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import Http404
from djgentelella.groute import register_lookups
from djgentelella.views.select2autocomplete import BaseSelect2View, GPaginator
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from auth_and_perms.models import Rol, ProfilePermission
from auth_and_perms.utils import get_roles_by_user
from laboratory.forms import  RelOrganizationPKIntForm
from laboratory.models import Laboratory, OrganizationStructure, OrganizationStructureRelations, \
    OrganizationUserManagement, UserOrganization
from laboratory.utils import get_profile_by_organization, get_users_from_organization, get_rols_from_organization


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
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk, **kwargs):
        self.organization = pk
        return self.list(request, pk, **kwargs)

    def list(self, request, *args, **kwargs):
        if self.organization is None:
            form = RelOrganizationPKIntForm(self.request.GET)
            if form.is_valid():
                self.organization = get_object_or_404(OrganizationStructure, pk=form.cleaned_data['organization'])

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


@register_lookups(prefix="laborguserbase", basename="laborguserbase")
class LabUserS2OrgManagement(generics.RetrieveAPIView, BaseSelect2View):
    model = User
    fields = ['username']
    organization = None
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    organization=None
    contenttypeobj=None

    def retrieve(self, request, pk, **kwargs):
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        return self.list(request, pk, **kwargs)

    def list(self, request, *args, **kwargs):
        if self.organization is None:
            form = RelOrganizationPKIntForm(self.request.GET)
            if form.is_valid():
                self.organization = get_object_or_404(OrganizationStructure, pk=form.cleaned_data['organization'])
                if form.cleaned_data['typeofcontenttype'] == 'laboratory':
                    if form.cleaned_data['laboratory']:
                        self.contenttypeobj = get_object_or_404(Laboratory, pk=form.cleaned_data['laboratory'])
                elif form.cleaned_data['typeofcontenttype'] == 'organization':
                        self.contenttypeobj = self.organization

        if self.organization is None:
            raise
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        orgByuser = OrganizationStructure.os_manager.organization_tree(self.organization.pk)
        users = list(OrganizationUserManagement.objects.filter(
            organization__in=orgByuser).values_list('users', flat=True))
        queryset = self.model.objects.filter(Q(userorganization__organization__in=orgByuser)|Q(pk__in=users))
        if self.contenttypeobj:
            profiles = get_profile_by_organization(self.organization.pk)
            profiles.filter(profilepermission__content_type__app_label= self.contenttypeobj._meta.app_label,
                            profilepermission__content_type__model= self.contenttypeobj._meta.model_name,
                            profilepermission__object_id=self.contenttypeobj.pk)
            queryset = queryset.exclude(profile__in=profiles).distinct()

        return queryset.order_by('first_name')

    def get_text_display(self, obj):
        if hasattr(obj, 'profile') and obj.profile:
            return str(obj.profile)
        return str(obj)

@register_lookups(prefix="orguserbase", basename="orguserbase")
class UserS2OrgManagement(generics.RetrieveAPIView, BaseSelect2View):
    model = User
    fields = ['username']
    organization = None
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    organization=None
    laboratory=None

    def retrieve(self, request, pk, **kwargs):
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        return self.list(request, pk, **kwargs)

    def list(self, request, *args, **kwargs):
        if self.organization is None:
            form = RelOrganizationPKIntForm(self.request.GET)
            if form.is_valid():
                if form.cleaned_data['laboratory']:
                    self.laboratory = get_object_or_404(Laboratory, pk=form.cleaned_data['laboratory'])
                self.organization = get_object_or_404(OrganizationStructure, pk=form.cleaned_data['organization'])

        if self.organization is None:
            raise
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        orgs = []
        orgByuser = OrganizationStructure.os_manager.filter_user_orgs(user=self.request.user, org=self.organization)
        for org in orgByuser:
            orgs += list(org.descendants())
            orgs += list(org.ancestors())
            orgs.append(org)

        users = []
        for org in set(orgs):
            users += list(get_users_from_organization(org.pk, org=org, userfilters={'users__isnull': False}))
        return self.model.objects.filter(pk__in=set(users)).order_by('pk')

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        profiles = get_profile_by_organization(self.organization.pk)
        #queryset = list(get_users_from_organization(org))
        if profiles:
            self.selected = [str(idpp) for idpp in profiles.values_list('user__id', flat=True)]
        return queryset

    def get_text_display(self, obj):
        if hasattr(obj, 'profile') and obj.profile:
            return str(obj.profile)
        return str(obj.pk)

@register_lookups(prefix="groupbase", basename="groupbase")
class GroupS2(BaseSelect2View):
    model = Rol
    fields = ['name']
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return get_roles_by_user(user)


@register_lookups(prefix="relorgbase", basename="relorgbase")
class RelOrgBaseS2(generics.RetrieveAPIView, BaseSelect2View):
    model = Laboratory
    fields = ['name']
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = GPaginatorMoreElements
    order_by = ['name']
    organization = None

    def get_queryset(self):
        labs = OrganizationStructure.os_manager.filter_labs_by_user(self.request.user, org_pk=self.organization.pk)
        # it's required than exclude labs that are part of the organization to prevent repeat labs
        exclude_labs = OrganizationStructureRelations.objects.filter(
            organization=self.organization.pk,
            content_type__app_label='laboratory', content_type__model='laboratory'
        ).values_list('object_id', flat=True)
        return labs.exclude(pk__in=exclude_labs).order_by(*self.order_by)

    def retrieve(self, request, pk, **kwargs):
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        return self.list(request, pk, **kwargs)

    def list(self, request, *args, **kwargs):
        if self.organization is None:
            form = RelOrganizationPKIntForm(self.request.GET)
            if form.is_valid():
                self.organization = get_object_or_404(OrganizationStructure, pk=form.cleaned_data['organization'])

        if self.organization is None:
            raise Http404("Organization not found")
        return super().list(request, *args, **kwargs)


@register_lookups(prefix="laborgbase", basename="laborgbase")
class LabOrgBaseS2(generics.RetrieveAPIView, BaseSelect2View):
    model = Laboratory
    fields = ['name']
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = GPaginatorMoreElements
    order_by = ['name']
    organization = None

    def get_queryset(self):
        labs = list(OrganizationStructureRelations.objects.filter(
            organization=self.organization.pk,
            content_type__app_label='laboratory', content_type__model='laboratory'
        ).values_list('object_id', flat=True))
        labs += list(self.organization.laboratory_set.all().values_list('pk', flat=True))
        return Laboratory.objects.filter(pk__in=labs)

    def retrieve(self, request, pk, **kwargs):
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        return self.list(request, pk, **kwargs)

    def list(self, request, *args, **kwargs):
        if self.organization is None:
            form = RelOrganizationPKIntForm(self.request.GET)
            if form.is_valid():
                self.organization = get_object_or_404(OrganizationStructure, pk=form.cleaned_data['organization'])

        if self.organization is None:
            raise Http404("Organization not found")
        return super().list(request, *args, **kwargs)



@register_lookups(prefix="roluserorgbase", basename="roluserorgbase")
class RolUserOrgS2(generics.RetrieveAPIView, BaseSelect2View):
    model = Rol
    fields = ['name']
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        orgs = []
        orgByuser = OrganizationStructure.os_manager.filter_user(self.request.user)
        for org in orgByuser:
            orgs += list(org.descendants())
            orgs += list(org.ancestors())
            orgs.append(org)

        rols = []
        for org in set(orgs):
            rols += list(get_rols_from_organization(org.pk, org=org, rolfilters={'rol__isnull': False}))
        return self.model.objects.filter(pk__in=set(rols))


@register_lookups(prefix="orgbyuser", basename="orgbyuser")
class OrgbyUserOrgS2(BaseSelect2View):
    model = OrganizationStructure
    fields = ['name']
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        self.org = None
        org = self.request.GET.get('org')
        orgByuser = OrganizationStructure.os_manager.filter_user(self.request.user, ancestors=True)
        if org:
            orgByuser = orgByuser.exclude(pk=org)
            self.org = OrganizationStructure.objects.get(pk=org)

        return self.model.objects.filter(pk__in=tuple(orgByuser.values_list('pk', flat=True)))

    def filter_queryset(self, queryset):
        dev = super().filter_queryset(queryset)
        if self.org:
            if self.org.parent:
                self.selected=[str(self.org.parent.pk)]
        return dev