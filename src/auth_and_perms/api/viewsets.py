from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from rest_framework.views import APIView

from auth_and_perms.api.serializers import RolSerializer, \
    ProfilePermissionRolOrganizationSerializer, \
    OrganizationSerializer, ProfileFilterSet, ProfileRolDataTableSerializer, \
    DeleteUserFromContenttypeSerializer, \
    ProfileAssociateOrganizationSerializer, ValidateGroupsByProfileSerializer, \
    ShelfObjectSerializer, ValidateSearchShelfObjectSerializer, \
    ShelfObjectDataTableSerializer, ValidateOrganizationSerializer
from auth_and_perms.forms import LaboratoryAndOrganizationForm, \
    OrganizationForViewsetForm, SearchShelfObjectViewsetForm
from auth_and_perms.models import Rol, ProfilePermission, Profile
from auth_and_perms.organization_utils import user_is_allowed_on_organization, organization_can_change_laboratory
from laboratory.models import OrganizationStructure, Laboratory, UserOrganization, \
    ShelfObject
from laboratory.utils import get_profile_by_organization, get_organizations_by_user, \
    get_laboratories_from_organization


class RolAPI(mixins.ListModelMixin,
             mixins.UpdateModelMixin,
             mixins.CreateModelMixin,
             viewsets.GenericViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        self.request = request
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        super().perform_create(serializer)
        organizationstructure = OrganizationStructure.objects.using(settings.READONLY_DATABASE
                                                                    ).filter(pk=self.request.data['rol']).first()

        user_is_allowed_on_organization(self.request.user, organizationstructure)

        serializer.instance.organizationstructure_set.add(organizationstructure)

        if 'relate_rols' in self.request.data:
            relate_rols = self.request.data['relate_rols']
            perms_rols = list(Rol.objects.filter(pk__in=relate_rols).values_list('permissions__pk', flat=True))
            permissions = list(Permission.objects.filter(pk__in=perms_rols))
            serializer.instance.permissions.add(*permissions)


class ProfileToContenttypeObjectAPI(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = UserOrganization.objects.all()
    serializer_class = ProfileAssociateOrganizationSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        contenttypeobj = None
        organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE),
                                            pk=serializer.data['organization'])
        user_is_allowed_on_organization(self.request.user, organization)
        type_user=UserOrganization.LABORATORY_USER
        user = get_object_or_404(User.objects.using(settings.READONLY_DATABASE), pk=serializer.data['user'])
        if serializer.data['typeofcontenttype'] == 'laboratory':
            contenttypeobj = get_object_or_404(Laboratory.objects.using(settings.READONLY_DATABASE),
                                               pk=serializer.data['laboratory'])
            if not organization_can_change_laboratory(contenttypeobj, organization):
                return HttpResponseForbidden(_("Laboratory modification not authorized"))
        elif serializer.data['typeofcontenttype'] == 'organization':
            contenttypeobj = organization
            type_user=UserOrganization.LABORATORY_MANAGER


        UserOrganization.objects.get_or_create(organization=organization, user=user, type_in_organization=type_user)

        ProfilePermission.objects.get_or_create(
            profile=user.profile,
            content_type=ContentType.objects.filter(app_label=contenttypeobj._meta.app_label,
                                                    model=contenttypeobj._meta.model_name).first(),
            object_id=contenttypeobj.pk
        )

        if serializer.data['typeofcontenttype'] == 'laboratory':
            ## add user to organization if not exist but without perms
            instance, created = ProfilePermission.objects.get_or_create(
                profile=user.profile,
                content_type=ContentType.objects.filter(
                    app_label=organization._meta.app_label,
                    model=organization._meta.model_name).first(),
                object_id=organization.pk
            )
        if  ('addlaboratories' in serializer.validated_data  and
            serializer.validated_data['addlaboratories'] is not None):
            for lab in serializer.validated_data['addlaboratories']:
                instance, created = ProfilePermission.objects.get_or_create(
                    profile=user.profile,
                    content_type=ContentType.objects.filter(
                        app_label=lab._meta.app_label,
                        model=lab._meta.model_name).first(),
                    object_id=lab.pk
                )


class UpdateRolOrganizationProfilePermission(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = ProfilePermission.objects.all()
    serializer_class = ProfilePermissionRolOrganizationSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def append_rols(self, profilepermission, rols):
        profilepermission.rol.add(*rols)

    def sustract_rols(self, profilepermission, rols):
        profilepermission.rol.remove(*rols)

    def full_rols(self, profilepermission, rols):
        profilepermission.rol.clear()
        self.append_rols(profilepermission, rols)

    def manage_rols(self, action, profilepermission, rols):
        if action == 'append':
            self.append_rols(profilepermission, rols)
        if action == 'sustract':
            self.sustract_rols(profilepermission, rols)
        if action == 'full':
            self.full_rols(profilepermission, rols)

    def update(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=False):
            org = OrganizationStructure.objects.get(pk=pk)
            user_is_allowed_on_organization(request.user, org)
            action = serializer.data['mergeaction']
            rols = org.rol.filter(pk__in=serializer.data['rols'])

            if serializer.data['as_role']:
                profile = Profile.objects.get(pk=serializer.data['profile'])
                ppdata = {
                    'profile_id': serializer.data['profile'],
                    'content_type': ContentType.objects.filter(
                        app_label=serializer.data['contenttypeobj']['appname'],
                        model=serializer.data['contenttypeobj']['model'],
                    ).first()
                }

                content_type = serializer.data['contenttypeobj']

                if content_type['model'] == 'laboratory' and content_type['appname'] == 'laboratory':

                    lab = Laboratory.objects.filter(pk=int(content_type['objectid'])).first()
                    if not organization_can_change_laboratory(lab, org):
                        return HttpResponseForbidden(_("Laboratory modification not authorized"))

                    if lab and action == 'append':
                        profile.laboratories.add(lab)

                    elif lab and action == 'sustract':
                        profile.laboratories.remove(lab)

                if 'objectid' in serializer.data['contenttypeobj'] and serializer.data['contenttypeobj']['objectid']:
                    ppdata['object_id'] = serializer.data['contenttypeobj']['objectid']
                else:
                    ppdata = {
                        'profile_id': serializer.data['profile'],
                        'content_type': ContentType.objects.filter(
                            app_label=profile._meta.app_label,
                            model=profile._meta.model_name,

                        ).first(),
                        'object_id': profile.pk,
                    }

                profilepermission = ProfilePermission.objects.filter(**ppdata).first()
                if not profilepermission:
                    profilepermission = ProfilePermission.objects.create(**ppdata)

                self.manage_rols(action, profilepermission, rols)

            return Response(serializer.data)
        return Response(serializer.errors)


class OrganizationAPI(mixins.ListModelMixin,
                      mixins.UpdateModelMixin,
                      viewsets.GenericViewSet):
    queryset = OrganizationStructure.objects.all()
    serializer_class = OrganizationSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_organizations_by_user(self.request.user)


class UserLaboratoryOrganization(mixins.ListModelMixin,
                                 viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileRolDataTableSerializer
    queryset = Profile.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['user__first_name', 'user__last_name']  # for the global search
    filterset_class = ProfileFilterSet
    ordering_fields = ['user', ]
    ordering = ('-user',)  # default order

    def get_queryset(self):
        profiles = get_profile_by_organization(self.organization.pk)
        return profiles.filter(
            profilepermission__content_type__app_label=self.contenttypeobj._meta.app_label,
            profilepermission__content_type__model=self.contenttypeobj._meta.model_name,
            profilepermission__object_id=self.contenttypeobj.pk) # Is laboratory

    def list(self, request, *args, **kwargs):
        form = LaboratoryAndOrganizationForm(request.GET)
        if form.is_valid():
            self.organization = form.cleaned_data['organization']
            self.contenttypeobj = form.cleaned_data['laboratory']
            user_is_allowed_on_organization(request.user, self.organization)
            if not organization_can_change_laboratory(self.contenttypeobj, self.organization):
                return HttpResponseForbidden(_("Laboratory modification not authorized"))
            queryset = self.get_queryset()
            total = queryset.count()
            queryset = self.filter_queryset(queryset)
            data = self.paginate_queryset(queryset)
        else:
            data = Profile.objects.none()
            queryset = data
            total = 0
        response = {'data': data, 'recordsTotal': total,
                    'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}
        return Response(self.get_serializer(response).data)


class UserInOrganization(mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileRolDataTableSerializer
    queryset = Profile.objects.using(settings.READONLY_DATABASE)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['user__first_name', 'user__last_name']  # for the global search
    filterset_class = ProfileFilterSet
    ordering_fields = ['user', ]
    ordering = ('-user',)  # default order

    def get_queryset(self):
        users=self.organization.users.using(settings.READONLY_DATABASE).filter(
            userorganization__type_in_organization__in=[UserOrganization.ADMINISTRATOR,
                                                        UserOrganization.LABORATORY_MANAGER],

        ).values_list('pk', flat=True)

        return self.queryset.filter(user__in=users).distinct()

    def list(self, request, *args, **kwargs):
        form = OrganizationForViewsetForm(request.GET)
        if form.is_valid():
            self.organization = form.cleaned_data['organization']
            # serializer assume that object laboratory is a contenttype element
            self.contenttypeobj = self.organization
            user_is_allowed_on_organization(request.user, self.organization)
            queryset = self.get_queryset()
            total = queryset.count()
            queryset = self.filter_queryset(queryset)
            data = self.paginate_queryset(queryset)
        else:
            data = Profile.objects.none()
            queryset = data
            total = 0
        response = {'data': data, 'recordsTotal': total,
                    'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}
        return Response(self.get_serializer(response).data)


class DeleteUserFromContenttypeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    http_method_names = ['delete']
    serializer_class = DeleteUserFromContenttypeSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def delete_profile_from_organization(self, user, organization):

        labs=get_laboratories_from_organization(organization.pk)
        pps=ProfilePermission.objects.filter(
            profile=user.profile,
            content_type__app_label='laboratory',
            content_type__model='laboratory',
            object_id__in=labs.values_list('pk', flat=True)
        )
        pps.delete()
        organization.users.remove(user)  # only remove relation

    def delete(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            org = OrganizationStructure.objects.using(settings.READONLY_DATABASE).filter(
                pk=serializer.data['organization']).first()
            user_is_allowed_on_organization(request.user, org)
            user = org.users.filter(profile=serializer.data['profile']).first()
            if user and serializer.data['model'] == 'organizationstructure':
                self.delete_profile_from_organization(user, org)
            if user and  serializer.data['disable_user']:
                    user.is_active = False
                    user.save()

            ProfilePermission.objects.filter(
                profile_id=serializer.data['profile'],
                content_type__app_label=serializer.data['app_label'],
                content_type__model=serializer.data['model'],
                object_id=serializer.data['object_id'],
            ).delete()

        return Response({'result': 'ok'})

    def list(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


class UpdateGroupsByProfile(APIView):
    def post(self, request):
        errors = {}

        organization = get_object_or_404(OrganizationStructure,
                                         pk=request.data.get('organization'))
        user_is_allowed_on_organization(request.user, organization)
        serializer = ValidateGroupsByProfileSerializer(data=request.data)

        if serializer.is_valid():
            profile = serializer.validated_data["profile"]
            groups = serializer.validated_data.get("groups")
            profile.groups.remove(*profile.groups.all())

            if groups:
                profile.groups.add(*groups)

        else:
            errors = serializer.errors

        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({"detail": _("Profile was updated successfully.")},
                            status=status.HTTP_200_OK)


class SearchShelfObjectOrganization(mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ShelfObjectDataTableSerializer
    queryset = ShelfObject.objects.using(settings.READONLY_DATABASE)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    ordering_fields = ['id', ]
    ordering = ('-id',)  # default order

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(in_where_laboratory__organization=self.organization,
                                   object=self.object).distinct()
        return queryset

    def list(self, request, *args, **kwargs):
        validate_serializer = ValidateSearchShelfObjectSerializer(data=request.GET)
        if validate_serializer.is_valid():
            self.object = validate_serializer.validated_data.get('object')
            self.organization = validate_serializer.validated_data.get('organization')
            user_is_allowed_on_organization(request.user, self.organization)
            queryset = self.get_queryset()
            total = queryset.count()
            queryset = self.filter_queryset(queryset)
            data = self.paginate_queryset(queryset)
            response = {'data': data, 'recordsTotal': total,
                        'recordsFiltered': queryset.count(),
                        'draw': self.request.GET.get('draw', 1)}
            return Response(self.get_serializer(response).data)
        else:
            return JsonResponse({"errors": validate_serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class OrganizationButtons(APIView):
    def get(self, request):
        serializer = ValidateOrganizationSerializer(data=request.GET)

        if serializer.is_valid():
            organization = serializer.validated_data.get('organization')
            user_is_allowed_on_organization(request.user, organization)
            return JsonResponse({"result": render_to_string(
            'auth_and_perms/organization_buttons.html',
            context={"request": request, "organization": organization}
            )}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

