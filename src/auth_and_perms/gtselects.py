from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db.models import Q, Case, When
from django.http import Http404
from djgentelella.groute import register_lookups
from djgentelella.views.select2autocomplete import BaseSelect2View, GPaginator
from rest_framework import generics, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auth_and_perms.api.serializers import ValidateProfileSerializer, \
    ValidateOrganizationSerializer
from auth_and_perms.models import Rol, ProfilePermission
from auth_and_perms.node_tree import get_tree_organization_pks_by_user, \
    get_org_parents_info
from auth_and_perms.organization_utils import user_is_allowed_on_organization, organization_can_change_laboratory
from auth_and_perms.utils import get_roles_by_user
from laboratory.forms import RelOrganizationPKIntForm
from laboratory.models import Laboratory, OrganizationStructure, \
    OrganizationStructureRelations, Object
from laboratory.utils import get_profile_by_organization, get_users_from_organization, get_rols_from_organization
from django.utils.translation import gettext_lazy as _

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
                self.organization = form.cleaned_data['organization']

        if self.organization:
            self.organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=self.organization)
        user_is_allowed_on_organization(self.request.user, self.organization)
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset=super().get_queryset()
        return queryset.using(settings.READONLY_DATABASE)

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
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    organization = None
    contenttypeobj = None

    def retrieve(self, request, pk, **kwargs):
        self.organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=pk)

        if not self.organization.active:
            return Response({
                'status': 'Bad request',
                'errors': {"organization": [_("Organization cannot be inactive")]},
            }, status=status.HTTP_400_BAD_REQUEST)

        return self.list(request, pk, **kwargs)

    def list(self, request, *args, **kwargs):
        if self.organization is None:
            form = RelOrganizationPKIntForm(self.request.GET)

            if form.is_valid():
                self.organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=form.cleaned_data['organization'])

                if form.cleaned_data['typeofcontenttype'] == 'laboratory':
                    if form.cleaned_data['laboratory']:
                        self.contenttypeobj = get_object_or_404(Laboratory.objects.using(settings.READONLY_DATABASE), pk=form.cleaned_data['laboratory'])
                        organization_can_change_laboratory(self.contenttypeobj, self.organization)
                elif form.cleaned_data['typeofcontenttype'] == 'organization':
                    self.contenttypeobj = self.organization
                    user_is_allowed_on_organization(self.request.user, self.contenttypeobj)
            else:
                return Response({
                    'status': 'Bad request',
                    'errors': form.errors,
                }, status=status.HTTP_400_BAD_REQUEST)

            if self.organization:
                user_is_allowed_on_organization(self.request.user, self.organization)
            return super().list(request, *args, **kwargs)


    def get_queryset(self):
        if self.organization:
            orgByuser = OrganizationStructure.os_manager.organization_tree(self.organization.pk)
            users = list(OrganizationStructure.objects.filter(pk__in=orgByuser).values_list('users', flat=True))
            queryset = self.model.objects.filter(Q(userorganization__organization__in=orgByuser)|Q(pk__in=users))
            if self.contenttypeobj:
                profiles = get_profile_by_organization(self.organization.pk)
                profiles=profiles.filter(profilepermission__content_type__app_label= self.contenttypeobj._meta.app_label,
                                profilepermission__content_type__model= self.contenttypeobj._meta.model_name,
                                profilepermission__object_id=self.contenttypeobj.pk)
                queryset = queryset.exclude(profile__in=profiles)
                return queryset.distinct().order_by('first_name')
            return queryset.none()
        return self.model.objects.none()

    def get_text_display(self, obj):
        if hasattr(obj, 'profile') and obj.profile:
            return f"{obj.profile} ({obj.username})"
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
        self.organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=pk)
        return self.list(request, pk, **kwargs)

    def list(self, request, *args, **kwargs):
        if self.organization is None:
            form = RelOrganizationPKIntForm(self.request.GET)
            if form.is_valid():
                if form.cleaned_data['laboratory']:
                    self.laboratory = get_object_or_404(Laboratory.objects.using(settings.READONLY_DATABASE), pk=form.cleaned_data['laboratory'])
                self.organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=form.cleaned_data['organization'])

        user_is_allowed_on_organization(self.request.user, self.organization)
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
    fields = ['pk','name']
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return get_roles_by_user(user)

    def get_text_display(self, obj):
        org_str =''
        for i, org in enumerate(obj.organizationstructure_set.all()):
            if i:
                org_str += " -- "
            org_str += org.name

        if self.fields:
            fields = [self.get_field_value(obj, x, str) for x in self.fields]
            return self.text_separator.join(fields) + " ("+org_str+")"
        return str(obj)


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

        if self.organization.parent:
            labs = OrganizationStructure.os_manager.filter_labs_by_user(self.request.user,
                                                                    ancestors=True,
                                                                    org_pk=self.organization.pk)
        else:
            labs = OrganizationStructure.os_manager.filter_labs_by_user(
                self.request.user,
                org_pk=self.organization.pk,
                relate_labs_org_parent=True
            )

        # it's required than exclude labs that are part of the organization to prevent repeat labs
        exclude_labs = OrganizationStructureRelations.objects.filter(
            organization=self.organization.pk,
            content_type__app_label='laboratory', content_type__model='laboratory'
        ).values_list('object_id', flat=True)
        return labs.exclude(pk__in=exclude_labs).order_by(*self.order_by)

    def retrieve(self, request, pk, **kwargs):
        self.organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=pk)
        return self.list(request, pk, **kwargs)

    def list(self, request, *args, **kwargs):
        if self.organization is None:
            form = RelOrganizationPKIntForm(self.request.GET)
            if form.is_valid():
                self.organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=form.cleaned_data['organization'])

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
        labs = list(OrganizationStructureRelations.objects.using(settings.READONLY_DATABASE).filter(
            organization=self.organization.pk,
            content_type__app_label='laboratory', content_type__model='laboratory'
        ).values_list('object_id', flat=True))
        labs += list(self.organization.laboratory_set.using(settings.READONLY_DATABASE).all().values_list('pk', flat=True))
        return Laboratory.objects.using(settings.READONLY_DATABASE).filter(pk__in=labs)

    def retrieve(self, request, pk, **kwargs):
        self.organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=pk)

        if not self.organization.active:
            return Response({
                'status': 'Bad request',
                'errors': {"organization": [_("Organization cannot be inactive")]},
            }, status=status.HTTP_400_BAD_REQUEST)

        return self.list(request, pk, **kwargs)

    def list(self, request, *args, **kwargs):
        if self.organization is None:
            form = RelOrganizationPKIntForm(self.request.GET)
            if form.is_valid():
                self.organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=form.cleaned_data['organization'])
            else:
                return Response({
                    'status': 'Bad request',
                    'errors': form.errors,
                }, status=status.HTTP_400_BAD_REQUEST)

        if self.organization is None:
            raise Http404(_("Organization not found"))
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


@register_lookups(prefix="groupsbyprofile", basename="groupsbyprofile")
class GroupsByProfile(BaseSelect2View):
    model = Group
    fields = ['name']
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    profile = None

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.profile:
            return self.profile.groups.all()
        return queryset.none()

    def list(self, request, *args, **kwargs):
        self.serializer = ValidateProfileSerializer(data=request.GET)

        if self.serializer.is_valid():
            self.profile = self.serializer.validated_data.get('profile', None)
            return super().list(request, *args, **kwargs)

        return Response({
                'status': 'Bad request',
                'errors': self.serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)


@register_lookups(prefix="usersbyorg", basename="usersbyorg")
class UsersByOrganization(BaseSelect2View):
    model = User
    fields = ['first_name']
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer, organization = None, None

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.organization:
            queryset = self.organization.users.all().using(settings.READONLY_DATABASE).distinct()
        else:
            queryset = queryset.none()

        return queryset

    def list(self, request, *args, **kwargs):
        self.serializer = ValidateOrganizationSerializer(data=request.GET)

        if self.serializer.is_valid():
            self.organization = self.serializer.validated_data.get('organization')
            user_is_allowed_on_organization(request.user, self.organization)
            return super().list(request, *args, **kwargs)

        return Response({
                'status': 'Bad request',
                'errors': self.serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

    def get_text_display(self, obj):
        name = obj.get_full_name()
        if not name:
            name = obj.username
        return name


@register_lookups(prefix="orgtree", basename="orgtree")
class OrgTree(BaseSelect2View):
    model = OrganizationStructure
    fields = ["name"]
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    user = None

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.user:
            parents, parents_pks = get_org_parents_info(self.user)
            pks = []
            for node in parents:
                if node.pk not in pks:
                    get_tree_organization_pks_by_user(node, self.user, pks,
                                          parents=parents_pks, extras={'active': True})

            tree_order = Case(*[When(pk=pk, then=i) for i, pk in enumerate(pks)])
            queryset = queryset.filter(pk__in=pks).order_by(tree_order)
            return queryset
        return queryset.none()

    def list(self, request, *args, **kwargs):
        self.user = request.user
        return super().list(request, *args, **kwargs)

    def get_text_display(self, obj):
        name = "%d | %s" % (obj.pk, obj.name)

        if obj.parent:
            name = "%s %d | %s" % ("--" * obj.level, obj.pk, obj.name)
        return name


@register_lookups(prefix="objbyorg", basename="objbyorg")
class ObjectByOrganization(BaseSelect2View):
    model = Object
    fields = ["code", "name"]
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    user, organization = None, None

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.organization:
            queryset = queryset.filter(organization=self.organization).order_by("name")
        else:
            queryset = queryset.none()
        return queryset

    def list(self, request, *args, **kwargs):
        self.serializer = ValidateOrganizationSerializer(data=request.GET)

        if self.serializer.is_valid():
            self.organization = self.serializer.validated_data.get('organization')
            user_is_allowed_on_organization(request.user, self.organization)
            return super().list(request, *args, **kwargs)

        return Response({
            'status': 'Bad request',
            'errors': self.serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    def get_text_display(self, obj):
        return str(obj)
