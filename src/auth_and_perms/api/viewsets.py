from django.conf import settings
from django.contrib.admin.models import CHANGE, DELETION, ADDITION
from django.contrib.auth.models import Permission, User, Group
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django_filters.rest_framework import DjangoFilterBackend
from djgentelella.objectmanagement import AuthAllPermBaseObjectManagement
from rest_framework import mixins, viewsets, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from rest_framework.views import APIView

from api.utils import AllPermissionOrganization
from auth_and_perms.api import filterset
from auth_and_perms.api.serializers import (
    RolSerializer,
    ProfilePermissionRolOrganizationSerializer,
    OrganizationSerializer,
    ProfileFilterSet,
    ProfileRolDataTableSerializer,
    DeleteUserFromContenttypeSerializer,
    ProfileAssociateOrganizationSerializer,
    ValidateGroupsByProfileSerializer,
    ShelfObjectSerializer,
    ValidateSearchShelfObjectSerializer,
    ShelfObjectDataTableSerializer,
    ValidateOrganizationSerializer,
    ExternalUserSerializer,
    AddExternalUserSerializer,
    ValidateProfileOrganizationSerializer,
    ListUserSerializer,
    UserListDataTableSerializer,
    LaboratoryOrganizationDataTableSerializer,
    OrganizationLaboratoryDataTableSerializer,
    ProfileLaboratoryOrgRoles,
)
from auth_and_perms.forms import (
    LaboratoryAndOrganizationForm,
    OrganizationForViewsetForm,
    SearchShelfObjectViewsetForm,
)
from auth_and_perms.models import Rol, ProfilePermission, Profile
from auth_and_perms.organization_utils import (
    user_is_allowed_on_organization,
    organization_can_change_laboratory,
)
from laboratory.models import (
    OrganizationStructure,
    Laboratory,
    UserOrganization,
    ShelfObject,
    OrganizationStructureRelations,
)
from laboratory.utils import (
    get_profile_by_organization,
    get_organizations_by_user,
    get_laboratories_from_organization,
    get_user_laboratories,
    organilab_logentry,
)


class RolAPI(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
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
        organizationstructure = (
            OrganizationStructure.objects.using(settings.READONLY_DATABASE)
            .filter(pk=self.request.data["rol"])
            .first()
        )

        user_is_allowed_on_organization(self.request.user, organizationstructure)

        serializer.instance.organizationstructure_set.add(organizationstructure)

        if "relate_rols" in self.request.data:
            relate_rols = self.request.data["relate_rols"]
            perms_rols = list(
                Rol.objects.filter(pk__in=relate_rols).values_list(
                    "permissions__pk", flat=True
                )
            )
            permissions = list(Permission.objects.filter(pk__in=perms_rols))
            serializer.instance.permissions.add(*permissions)


class ProfileToContenttypeObjectAPI(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = UserOrganization.objects.all()
    serializer_class = ProfileAssociateOrganizationSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        contenttypeobj = None
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=serializer.data["organization"],
        )
        user_is_allowed_on_organization(self.request.user, organization)
        type_user = UserOrganization.LABORATORY_USER
        user = get_object_or_404(
            User.objects.using(settings.READONLY_DATABASE), pk=serializer.data["user"]
        )

        if serializer.data["typeofcontenttype"] == "laboratory":
            contenttypeobj = get_object_or_404(
                Laboratory.objects.using(settings.READONLY_DATABASE),
                pk=serializer.data["laboratory"],
            )
            if not organization_can_change_laboratory(contenttypeobj, organization):
                return HttpResponseForbidden(
                    _("Laboratory modification not authorized")
                )
        elif serializer.data["typeofcontenttype"] == "organization":
            contenttypeobj = organization
            type_user = UserOrganization.LABORATORY_MANAGER

        UserOrganization.objects.get_or_create(
            organization=organization, user=user, type_in_organization=type_user
        )

        ProfilePermission.objects.get_or_create(
            profile=user.profile,
            content_type=ContentType.objects.filter(
                app_label=contenttypeobj._meta.app_label,
                model=contenttypeobj._meta.model_name,
            ).first(),
            object_id=contenttypeobj.pk,
            organization=organization,
        )

        if serializer.data["typeofcontenttype"] == "laboratory":
            # add user to organization if not exist but without perms
            instance, created = ProfilePermission.objects.get_or_create(
                profile=user.profile,
                content_type=ContentType.objects.filter(
                    app_label=organization._meta.app_label,
                    model=organization._meta.model_name,
                ).first(),
                object_id=organization.pk,
                organization=organization,
            )

        if (
            "addlaboratories" in serializer.validated_data
            and serializer.validated_data["addlaboratories"] is not None
        ):
            for lab in serializer.validated_data["addlaboratories"]:
                instance, created = ProfilePermission.objects.get_or_create(
                    profile=user.profile,
                    content_type=ContentType.objects.filter(
                        app_label=lab._meta.app_label, model=lab._meta.model_name
                    ).first(),
                    object_id=lab.pk,
                    organization=organization,
                )


class UpdateRolOrganizationProfilePermission(
    mixins.UpdateModelMixin, viewsets.GenericViewSet
):
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
        if action == "append":
            self.append_rols(profilepermission, rols)
        if action == "sustract":
            self.sustract_rols(profilepermission, rols)
        if action == "full":
            self.full_rols(profilepermission, rols)

    def update(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=False):
            org = OrganizationStructure.objects.get(pk=pk)
            user_is_allowed_on_organization(request.user, org)
            action = serializer.data["mergeaction"]
            rols = org.root.rol.filter(pk__in=serializer.data["rols"])

            if serializer.data["as_role"]:
                profile = Profile.objects.get(pk=serializer.data["profile"])
                ppdata = {
                    "profile_id": serializer.data["profile"],
                    "content_type": ContentType.objects.filter(
                        app_label=serializer.data["contenttypeobj"]["appname"],
                        model=serializer.data["contenttypeobj"]["model"],
                    ).first(),
                }

                content_type = serializer.data["contenttypeobj"]

                if (
                    content_type["model"] == "laboratory"
                    and content_type["appname"] == "laboratory"
                ):

                    lab = Laboratory.objects.filter(
                        pk=int(content_type["objectid"])
                    ).first()
                    if not organization_can_change_laboratory(lab, org):
                        return HttpResponseForbidden(
                            _("Laboratory modification not authorized")
                        )

                    if lab and action == "append":
                        profile.laboratories.add(lab)

                    elif lab and action == "sustract":
                        profile.laboratories.remove(lab)

                if (
                    "objectid" in serializer.data["contenttypeobj"]
                    and serializer.data["contenttypeobj"]["objectid"]
                ):
                    ppdata["object_id"] = serializer.data["contenttypeobj"]["objectid"]
                else:
                    ppdata = {
                        "profile_id": serializer.data["profile"],
                        "content_type": ContentType.objects.filter(
                            app_label=profile._meta.app_label,
                            model=profile._meta.model_name,
                        ).first(),
                        "object_id": profile.pk,
                    }

                profilepermission = ProfilePermission.objects.filter(**ppdata).first()
                if not profilepermission:
                    profilepermission = ProfilePermission.objects.create(**ppdata)

                self.manage_rols(action, profilepermission, rols)

            return Response(serializer.data)
        return Response(serializer.errors)


class OrganizationAPI(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    queryset = OrganizationStructure.objects.all()
    serializer_class = OrganizationSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_organizations_by_user(self.request.user)


class UserLaboratoryOrganization(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileRolDataTableSerializer
    queryset = Profile.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = [
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__username",
    ]  # for the global search
    filterset_class = ProfileFilterSet
    ordering_fields = [
        "user",
    ]
    ordering = ("-user",)  # default order

    def get_queryset(self):
        profiles = get_profile_by_organization(self.organization.pk)
        return profiles.filter(
            profilepermission__content_type__app_label=self.contenttypeobj._meta.app_label,
            profilepermission__content_type__model=self.contenttypeobj._meta.model_name,
            profilepermission__object_id=self.contenttypeobj.pk,
            profilepermission__organization=self.organization,
        )  # Is laboratory

    def list(self, request, *args, **kwargs):
        form = LaboratoryAndOrganizationForm(request.GET)
        if form.is_valid():
            self.organization = form.cleaned_data["organization"]
            self.contenttypeobj = form.cleaned_data["laboratory"]
            user_is_allowed_on_organization(request.user, self.organization)
            if not organization_can_change_laboratory(
                self.contenttypeobj, self.organization
            ):
                return HttpResponseForbidden(
                    _("Laboratory modification not authorized")
                )
            queryset = self.get_queryset()
            total = queryset.count()
            queryset = self.filter_queryset(queryset)
            data = self.paginate_queryset(queryset)
        else:
            data = Profile.objects.none()
            queryset = data
            total = 0
        response = {
            "data": data,
            "recordsTotal": total,
            "recordsFiltered": queryset.count(),
            "draw": self.request.GET.get("draw", 1),
        }
        return Response(self.get_serializer(response).data)


class UserInOrganization(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileRolDataTableSerializer
    queryset = Profile.objects.using(settings.READONLY_DATABASE).order_by("pk")
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["user__first_name", "user__last_name"]  # for the global search
    filterset_class = ProfileFilterSet
    ordering_fields = [
        "user",
    ]
    ordering = ("-user",)  # default order

    def get_queryset(self):
        users = (
            UserOrganization.objects.using(settings.READONLY_DATABASE)
            .filter(
                organization=self.organization,
                type_in_organization__in=[
                    UserOrganization.ADMINISTRATOR,
                    UserOrganization.LABORATORY_MANAGER,
                    UserOrganization.LABORATORY_USER,
                ],
                user__isnull=False,
            )
            .values_list("user", flat=True)
            .distinct()
        )

        return Profile.objects.using(settings.READONLY_DATABASE).filter(
            user__pk__in=users
        )

    def list(self, request, *args, **kwargs):
        form = OrganizationForViewsetForm(request.GET)
        if form.is_valid():
            self.organization = form.cleaned_data["organization"]
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
        response = {
            "data": data,
            "recordsTotal": total,
            "recordsFiltered": queryset.count(),
            "draw": self.request.GET.get("draw", 1),
        }
        return Response(self.get_serializer(response).data)

    # TODO Metodo obsoleto, ya que ahora todos los permisos los maneja la root
    @action(detail=False, methods=["post"])
    def inerit_profile(self, request):
        serializer = ValidateProfileOrganizationSerializer(data=request.data)
        if serializer.is_valid():
            organization = serializer.validated_data["organization"]
            user_is_allowed_on_organization(request.user, organization)
            object_id = serializer.validated_data["object_id"]
            user_pp = ProfilePermission.objects.filter(
                profile=serializer.validated_data["profile"],
                content_type=ContentType.objects.filter(
                    app_label=organization._meta.app_label,
                    model=organization._meta.model_name,
                ).first(),
                object_id=organization.pk,
            ).first()

            descendants = serializer.validated_data["organization"].descendants(
                include_self=False
            )
            org_vinculate = (
                UserOrganization.objects.filter(
                    user=serializer.validated_data["profile"].user,
                    organization=serializer.validated_data["organization"],
                )
                .first()
                .type_in_organization
            )

            for org in descendants:
                obj, created = ProfilePermission.objects.get_or_create(
                    profile=serializer.validated_data["profile"],
                    content_type=ContentType.objects.filter(
                        app_label=org._meta.app_label, model=org._meta.model_name
                    ).first(),
                    object_id=org.pk,
                )
                org.users.add(serializer.validated_data["profile"].user)
                if user_pp:
                    for rol in user_pp.rol.filter(organizationstructure=organization):
                        org.rol.add(rol)
                        obj.rol.add(rol)

                UserOrganization.objects.get_or_create(
                    organization=serializer.validated_data["organization"],
                    user=serializer.validated_data["profile"].user,
                    type_in_organization=org_vinculate,
                )

            return Response({"result": "ok"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExternalUserToOrganizationViewSet(
    mixins.UpdateModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):

    authentication_classes = [SessionAuthentication]
    permission_classes = [
        IsAuthenticated,
        AllPermissionOrganization(
            ["auth_and_perms.can_add_external_user_in_org"],
            lookup_keyword="organization",
        ),
    ]
    serializer_class = ExternalUserSerializer
    create_serializer_class = AddExternalUserSerializer
    queryset = User.objects.using(settings.READONLY_DATABASE)
    lookup_url_kwarg = "org_pk"

    def create(self, request, *args, **kwargs):
        serializer = self.create_serializer_class(data=request.data)
        response = {"success": False}
        if serializer.is_valid(raise_exception=False):
            organization = serializer.validated_data["organization"]
            user = serializer.validated_data["email"]
            user_is_allowed_on_organization(request.user, organization)
            organization.users.add(user)
            organilab_logentry(
                request.user,
                user,
                ADDITION,
                "user",
                changed_data=[],
                change_message=_("Added the user %(user)r in the organization %(org)r")
                % {"user": user.username, "org": organization.name},
                relobj=organization,
            )
            response = {"success": True}
        headers = self.get_success_headers(serializer.data)
        return Response(response, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        errors = {}
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["email"]

            response = {"pk": user.pk, "display_text": str(user.profile)}
            return JsonResponse(response)
        else:
            errors = serializer.errors

        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)


class DeleteUserFromContenttypeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    http_method_names = ["delete"]
    serializer_class = DeleteUserFromContenttypeSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def delete_profile_from_organization(self, user, organization):
        is_root = organization.root.pk == organization.pk
        descendant_orgs = []

        if is_root:
            org_ids = [organization.pk]
            descendant_orgs = list(organization.descendants())
            org_ids.extend([org.pk for org in descendant_orgs])
        else:
            org_ids = [organization.pk]

        for org_pk in org_ids:
            labs = get_laboratories_from_organization(org_pk, self.request.user)
            pps = ProfilePermission.objects.filter(
                profile=user.profile,
                content_type__app_label="laboratory",
                content_type__model="laboratory",
                object_id__in=labs.values_list("pk", flat=True),
                organization__pḱ=organization.pk,
            )
            for pp in pps:
                organilab_logentry(
                    user,
                    pp,
                    DELETION,
                    "profilepermission",
                    changed_data=[],
                    relobj=organization,
                )
            pps.delete()

        pps_orgs = ProfilePermission.objects.filter(
            profile=user.profile,
            content_type__app_label="laboratory",
            content_type__model="organizationstructure",
            object_id__in=org_ids,
        )
        for pp in pps_orgs:
            organilab_logentry(
                user,
                pp,
                DELETION,
                "profilepermission",
                changed_data=[],
                relobj=organization,
            )
        pps_orgs.delete()

        organization.users.remove(user)
        if is_root:
            for desc_org in descendant_orgs:
                desc_org.users.remove(user)

        organilab_logentry(
            user, user, DELETION, "user", changed_data=[], relobj=organization
        )

    def delete(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            org = (
                OrganizationStructure.objects.using(settings.READONLY_DATABASE)
                .filter(pk=serializer.data["organization"])
                .first()
            )
            user_is_allowed_on_organization(request.user, org)
            user = org.users.filter(profile=serializer.data["profile"]).first()
            if user and serializer.data["model"] == "organizationstructure":
                self.delete_profile_from_organization(user, org)
            if user and serializer.data["disable_user"]:
                user.is_active = False
                user.save()
                organilab_logentry(
                    user, user, CHANGE, "user", changed_data=["is_active"], relobj=org
                )

            pps = ProfilePermission.objects.filter(
                profile_id=serializer.data["profile"],
                content_type__app_label=serializer.data["app_label"],
                content_type__model=serializer.data["model"],
                object_id=serializer.data["object_id"],
            )
            for pp in pps:
                organilab_logentry(
                    user, pp, DELETION, "profilepermission", changed_data=[], relobj=org
                )
            pps.delete()
        return Response({"result": "ok"})

    def list(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


class UpdateGroupsByProfile(APIView):
    def post(self, request):
        errors = {}

        organization = get_object_or_404(
            OrganizationStructure, pk=request.data.get("organization")
        )
        user_is_allowed_on_organization(request.user, organization)
        serializer = ValidateGroupsByProfileSerializer(data=request.data)
        groups_exclude = []

        if serializer.is_valid():
            profile = serializer.validated_data["profile"]
            groups = serializer.validated_data.get("groups")
            profile.groups.remove(*profile.groups.all())
            if groups:
                groups_pk = [x.pk for x in groups]
                groups_exclude = profile.groups.all().exclude(pk__in=groups_pk)
                profile.groups.remove(*profile.groups.all())

            if groups_exclude:
                organilab_logentry(
                    request.user,
                    profile,
                    DELETION,
                    "profile",
                    changed_data=["groups"],
                    change_message=_(
                        "Removed the groups %(groups)r from the profile %(profile)r"
                    )
                    % {
                        "groups": ", ".join(
                            list(groups_exclude.values_list("name", flat=True))
                        ),
                        "profile": str(profile),
                    },
                    relobj=organization,
                )
            if groups:
                profile.groups.add(*groups)
                groups_pk = [x.pk for x in groups]
                groups_add = Group.objects.filter(pk__in=groups_pk)
                organilab_logentry(
                    request.user,
                    profile,
                    ADDITION,
                    "profile",
                    changed_data=["groups"],
                    change_message=_(
                        "Added the groups %(groups)r to the profile %(profile)r"
                    )
                    % {
                        "groups": ", ".join(
                            list(groups_add.values_list("name", flat=True))
                        ),
                        "profile": str(profile),
                    },
                    relobj=organization,
                )

        else:
            errors = serializer.errors

        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse(
            {"detail": _("Profile was updated successfully.")},
            status=status.HTTP_200_OK,
        )


class SearchShelfObjectOrganization(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ShelfObjectDataTableSerializer
    queryset = ShelfObject.objects.using(settings.READONLY_DATABASE)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    ordering_fields = [
        "id",
    ]
    ordering = ("-id",)  # default order

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(
            in_where_laboratory__organization=self.organization, object=self.object
        ).distinct()
        return queryset

    def list(self, request, *args, **kwargs):
        validate_serializer = ValidateSearchShelfObjectSerializer(data=request.GET)
        if validate_serializer.is_valid():
            self.object = validate_serializer.validated_data.get("object")
            self.organization = validate_serializer.validated_data.get("organization")
            user_is_allowed_on_organization(request.user, self.organization)
            queryset = self.get_queryset()
            total = queryset.count()
            queryset = self.filter_queryset(queryset)
            data = self.paginate_queryset(queryset)
            response = {
                "data": data,
                "recordsTotal": total,
                "recordsFiltered": queryset.count(),
                "draw": self.request.GET.get("draw", 1),
            }
            return Response(self.get_serializer(response).data)
        else:
            return JsonResponse(
                {"errors": validate_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )


class OrganizationButtons(APIView):
    def get(self, request):
        serializer = ValidateOrganizationSerializer(data=request.GET)

        if serializer.is_valid():
            organization = serializer.validated_data.get("organization")
            user_is_allowed_on_organization(request.user, organization)
            return JsonResponse(
                {
                    "result": render_to_string(
                        "auth_and_perms/organization_buttons.html",
                        context={"request": request, "organization": organization},
                    )
                },
                status=status.HTTP_200_OK,
            )
        else:
            return JsonResponse(
                {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )


class LaboratoryGeolocationsAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        labs = (
            get_user_laboratories(request.user)
            .select_related("organization")
            .exclude(geolocation="")
        )
        data = []
        for lab in labs:
            try:
                lat, lng = lab.geolocation.split(",")
                data.append(
                    {
                        "lat": float(lat),
                        "lng": float(lng),
                        "lab": lab.name,
                        "organization": (
                            lab.organization.name if lab.organization else ""
                        ),
                    }
                )
            except (ValueError, AttributeError):
                continue
        return JsonResponse({"laboratories": data})


class ManageOrgLabsAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        from laboratory.utils import register_laboratory_contenttype

        org = get_object_or_404(OrganizationStructure, pk=pk)
        user_is_allowed_on_organization(request.user, org)
        labs = request.data.get("labs", [])
        mergeaction = request.data.get("mergeaction", "append")
        ct = ContentType.objects.get(app_label="laboratory", model="laboratory")
        if mergeaction == "full":
            OrganizationStructureRelations.objects.filter(
                organization=org, content_type=ct
            ).delete()
            for lab_pk in labs:
                register_laboratory_contenttype(org, int(lab_pk))
        elif mergeaction == "append":
            for lab_pk in labs:
                register_laboratory_contenttype(org, int(lab_pk))
        elif mergeaction == "sustract":
            OrganizationStructureRelations.objects.filter(
                organization=org,
                content_type=ct,
                object_id__in=[int(p) for p in labs],
            ).delete()
        return Response({"ok": True})


class UserListViewset(AuthAllPermBaseObjectManagement):
    perms = {"list": ["auth_and_perms.view_profile"]}
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ListUserSerializer
    queryset = User.objects.using(settings.READONLY_DATABASE).order_by("pk")
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = filterset.UserFilter

    search_fields = [
        "first_name",
        "last_name",
        "username",
        "email",
    ]
    ordering_fields = [
        "first_name",
        "last_name",
        "username",
        "email",
    ]
    ordering = ("-pk",)

    def get_queryset(self):
        queryset = super().get_queryset()
        extra_filter = {"organization__isnull": False}
        if self.request.GET.get("organization", 0):
            extra_filter["organization__pk"] = self.request.GET.get("organization")
        users = (
            UserOrganization.objects.using(settings.READONLY_DATABASE)
            .filter(
                type_in_organization__in=[
                    UserOrganization.ADMINISTRATOR,
                    UserOrganization.LABORATORY_MANAGER,
                    UserOrganization.LABORATORY_USER,
                ],
                user__isnull=False,
                **extra_filter
            )
            .values_list("user", flat=True)
            .distinct()
        )
        queryset = queryset.filter(pk__in=users)
        if self.request.GET.getlist("roles[]", []):
            queryset = queryset.filter(
                profile__profilepermission__rol__in=self.request.GET.getlist(
                    "roles[]", []
                )
            )

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        total = queryset.count()
        queryset = self.filter_queryset(queryset)
        data = self.paginate_queryset(queryset)
        serialized_data = ListUserSerializer(
            data, many=True, context={"request": request}
        ).data
        response = {
            "data": serialized_data,
            "recordsTotal": total,
            "recordsFiltered": queryset.count(),
            "draw": request.GET.get("draw", 1),
        }
        return Response(response)


class OrganizationLaboratoryViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationLaboratoryDataTableSerializer
    queryset = OrganizationStructure.objects.using(settings.READONLY_DATABASE).filter(
        active=True, approval_status=OrganizationStructure.APPROVED
    )
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["name"]  # for the global search
    ordering_fields = [
        "pk",
    ]
    ordering = ("-pk",)  # default order

    def list(self, request, *args, **kwargs):
        if self.request.user.has_perm("laboratory.view_organizationstructure"):
            queryset = self.get_queryset()
            total = queryset.count()
            queryset = self.filter_queryset(queryset)
            data = self.paginate_queryset(queryset)
            response = {
                "data": data,
                "recordsTotal": total,
                "recordsFiltered": queryset.count(),
                "draw": self.request.GET.get("draw", 1),
            }
            return Response(self.get_serializer(response).data)
        else:
            return Response(
                {"error": _("You don't have permissions to access this section")},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LaboratoryOrganizationViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = LaboratoryOrganizationDataTableSerializer
    queryset = Laboratory.objects.using(settings.READONLY_DATABASE).filter(
        approval_status=Laboratory.APPROVED
    )
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["name"]  # for the global search
    ordering_fields = [
        "pk",
    ]
    ordering = ("-pk",)  # default order

    def list(self, request, *args, **kwargs):
        if self.request.user.has_perm("laboratory.view_laboratory"):
            queryset = self.get_queryset()
            total = queryset.count()
            queryset = self.filter_queryset(queryset)
            data = self.paginate_queryset(queryset)
            response = {
                "data": data,
                "recordsTotal": total,
                "recordsFiltered": queryset.count(),
                "draw": self.request.GET.get("draw", 1),
            }
            return Response(self.get_serializer(response).data)
        else:
            return Response(
                {"error": _("You don't have permissions to access this section")},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LaboratoryOrganizationRoles(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileLaboratoryOrgRoles
    queryset = Profile.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["user__first_name", "user__last_name"]  # for the global search
    filterset_class = ProfileFilterSet
    ordering_fields = [
        "user",
    ]
    ordering = ("-user",)  # default order

    def get_queryset(self):
        profiles = get_profile_by_organization(self.organization.pk)

        return profiles.filter(
            profilepermission__content_type__app_label=self.contenttypeobj._meta.app_label,
            profilepermission__content_type__model=self.contenttypeobj._meta.model_name,
            profilepermission__object_id=self.contenttypeobj.pk,
            profilepermission__organization=self.organization,
        )

    def list(self, request, *args, **kwargs):
        form = LaboratoryAndOrganizationForm(request.GET)
        if form.is_valid():
            self.organization = form.cleaned_data["organization"]
            self.contenttypeobj = form.cleaned_data["laboratory"]
            # user_is_allowed_on_organization(request.user, self.organization)
            queryset = self.get_queryset()
            return Response(self.get_serializer(queryset, many=True).data)
        return Response(self.get_serializer(Profile.objects.none(), many=True).data)


class UserRoles(viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileLaboratoryOrgRoles
    queryset = Profile.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["user__first_name", "user__last_name"]  # for the global search
    filterset_class = ProfileFilterSet
    ordering_fields = [
        "user",
    ]
    ordering = ("-user",)  # default order

    @action(
        detail=False,
        methods=["get"],
        url_path="roles-in-organization/(?P<user_pk>[^/.]+)",
    )
    def roles_in_organization(self, request, user_pk=None):
        """
        Devuelve los roles de un usuario en una organización específica.
        URL: /userroles/roles-in-organization/<user_pk>/?organization=<org_pk>
        """
        organization_pk = request.GET.get("organization")
        if not organization_pk:
            return Response(
                {"error": _("Organization parameter is required")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = get_object_or_404(User, pk=user_pk)
        organization = get_object_or_404(OrganizationStructure, pk=organization_pk)
        profile = user.profile

        profile_perm = ProfilePermission.objects.filter(
            profile=profile,
            content_type__app_label="laboratory",
            content_type__model="organizationstructure",
            object_id=organization.pk,
        ).first()

        roles_data = []
        if profile_perm:
            roles_data = list(
                set(profile_perm.rol.all().values_list("name", flat=True))
            )
        result = {
            "roles": roles_data,
        }

        return Response(result)

    @action(
        detail=False,
        methods=["get"],
        url_path="roles-in-laboratory/(?P<user_pk>[^/.]+)",
    )
    def roles_in_laboratory(self, request, user_pk=None):
        """
        Devuelve los roles de un usuario en un laboratorio,
        en cada una de las organizaciones vinculadas al laboratorio.
        URL: /userroles/roles-in-laboratory/<user_pk>/?laboratory=<lab_pk>
        """
        user = get_object_or_404(User, pk=user_pk)
        profile = user.profile

        lab_content_type = ContentType.objects.get_for_model(Laboratory)
        lab = get_object_or_404(Laboratory, pk=request.GET.get("laboratory", 0))

        # Obtener todos los ProfilePermission del usuario para laboratorios
        permissions = (
            ProfilePermission.objects.filter(
                profile=profile,
                content_type=lab_content_type,
                organization__isnull=False,
                object_id=lab.pk,
            )
            .select_related("organization")
            .prefetch_related("rol")
        )

        # Agrupar por organización
        org_data = {}
        results = []
        for perm in permissions:
            org = perm.organization

            results.append(
                {
                    "org_name": org.name,
                    "roles": list(set(perm.rol.all().values_list("name", flat=True))),
                }
            )

        return Response({"data": results})
