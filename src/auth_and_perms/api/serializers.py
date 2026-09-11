import uuid
from random import random

from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.urls import reverse
from django_filters import FilterSet
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse_lazy
from django.contrib.contenttypes.models import ContentType
from auth_and_perms.models import (
    Rol,
    Profile,
    AuthenticateDataRequest,
    ProfilePermission,
)
from auth_and_perms.organization_utils import organization_can_change_laboratory
from laboratory.models import (
    OrganizationStructure,
    Laboratory,
    Shelf,
    ShelfObject,
    Object,
    OrganizationStructureRelations,
    UserOrganization,
)
from django.utils.translation import gettext_lazy as _
import logging

from django.conf import settings

from laboratory.utils import (
    check_user_access_kwargs_org_lab,
    get_profile_by_organization,
)
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger("organilab")


class RolSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=False)

    class Meta:
        model = Rol
        fields = ["name", "permissions", "description"]


class ProfileAssociateOrganizationSerializer(serializers.Serializer):
    typeofcontenttype = serializers.CharField(required=True)
    user = serializers.PrimaryKeyRelatedField(
        many=False, queryset=User.objects.all(), required=True
    )
    organization = serializers.PrimaryKeyRelatedField(
        many=False, queryset=OrganizationStructure.objects.all(), required=True
    )
    laboratory = serializers.PrimaryKeyRelatedField(
        many=False, queryset=Laboratory.objects.all(), required=False
    )
    addlaboratories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Laboratory.objects.using(settings.READONLY_DATABASE).all(),
        required=False,
    )


class AuthenticateDataRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthenticateDataRequest
        fields = "__all__"


class AuthenticateDataRequestNotifySerializer(serializers.Serializer):
    id_transaction = serializers.IntegerField()
    data = AuthenticateDataRequestSerializer()


class ContentTypeObjectToPermissionManager(serializers.Serializer):
    org = serializers.PrimaryKeyRelatedField(
        queryset=OrganizationStructure.objects.all()
    )
    appname = serializers.CharField()
    model = serializers.CharField()
    objectid = serializers.IntegerField(required=False, allow_null=True)


class ProfilePermissionRolOrganizationSerializer(serializers.Serializer):
    rols = serializers.PrimaryKeyRelatedField(many=True, queryset=Rol.objects.all())
    as_conttentype = serializers.BooleanField(required=True)
    as_user = serializers.BooleanField(required=True)
    as_role = serializers.BooleanField(required=True)
    profile = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(), allow_null=True, required=False
    )
    contenttypeobj = ContentTypeObjectToPermissionManager(allow_null=True)
    mergeaction = serializers.ChoiceField(
        choices=[
            ("append", reverse_lazy("Append")),
            ("sustract", reverse_lazy("Sustract")),
            ("full", reverse_lazy("Only roles selected")),
        ]
    )


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationStructure
        fields = ["name", "parent"]


class ProfileFilterSet(FilterSet):

    def filter_queryset(self, queryset):
        search = self.request.GET.get("search", "")
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(user__username__icontains=search)
                | Q(user__email__icontains=search)
            )
        return queryset

    class Meta:
        model = Profile
        fields = {"user": ["exact"], "user__email": ["exact"]}


class ProfileSerializer(serializers.ModelSerializer):
    rols = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    action = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    def get_rols(self, obj):
        contenttypeobj = self.context["view"].contenttypeobj
        org = self.context["view"].organization.root
        datatext = (
            """data-org="%d" data-profile="%d" data-appname="%s" data-model="%s" data-objectid="%s" """
            % (
                org.pk,
                obj.pk,
                contenttypeobj._meta.app_label,
                contenttypeobj._meta.model_name,
                contenttypeobj.pk,
            )
        )
        profile_perm = ProfilePermission.objects.filter(
            profile_id=obj.pk,
            content_type__app_label=contenttypeobj._meta.app_label,
            content_type__model=contenttypeobj._meta.model_name,
            object_id=contenttypeobj.pk,
        ).first()
        role_items = ""
        if profile_perm:
            for rol in profile_perm.rol.filter(organizationstructure=org):
                role_items += (
                    """<li><span class="dropdown-item-text small" style="padding: 1px 8px; line-height: 1.2;">%s</span></li>"""
                    % (rol.name)
                )

        if not role_items:
            role_items = (
                """<li><span class="dropdown-item-text text-secondary small" style="padding: 1px 8px; line-height: 1.2;">%s</span></li>"""
                % str(_("No roles assigned"))
            )

        return """
        <div class="btn-group p-0 m-0">
            <button %s class="btn btn-sm border-0 text-secondary p-0 m-0" type="button" onclick="newuserrol(%s, '%s', %s)" id="profile_%s" data-bs-toggle="tooltip" data-bs-placement="top" title="%s">
                <i class="fa fa-user-md" aria-hidden="true"></i>
            </button>
            <button type="button" class="btn btn-sm border-0 text-secondary p-0 m-0 dropdown-toggle dropdown-toggle-split"
                data-bs-toggle="dropdown" aria-expanded="false" data-bs-toggle="tooltip" data-bs-placement="top" title="%s">
                <span class="visually-hidden">Toggle Dropdown</span>
            </button>
            <ul class="dropdown-menu">%s</ul>
        </div>
        """ % (
            datatext,
            obj.pk,
            contenttypeobj._meta.model_name,
            contenttypeobj.pk,
            f"{obj.pk}_{contenttypeobj._meta.model_name}_{contenttypeobj.pk}",
            str(_("Roles: manage the user's roles within the organization")),
            str(_("List Roles: show user's roles")),
            role_items,
        )

    def get_user(self, obj):
        return str(obj)

    def get_email(self, obj):
        return obj.user.email

    def get_action(self, obj):
        contenttypeobj = self.context["view"].contenttypeobj
        action_uuid = str(uuid.uuid4())
        org = self.context["view"].organization
        datatext = (
            """ id="ndel_%s" data-org="%s" data-profileid="%s" data-profile="%s" data-appname="%s" data-model="%s" data-objectid="%s" """
            % (
                action_uuid,
                str(contenttypeobj),
                obj.pk,
                str(obj),
                contenttypeobj._meta.app_label,
                contenttypeobj._meta.model_name,
                contenttypeobj.pk,
            )
        )
        impostor = ""
        if self.context["request"].user.has_perm("auth_and_perms.change_impostorlog"):
            if obj.user.pk != self.context["request"].user.pk:
                impostor = """<a class="me-2" href="%s" target="_blank" data-bs-toggle="tooltip" data-bs-placement="top" title="%s">
                    <i class="fa fa-user-secret" aria-hidden="true"></i>
                    </a>""" % (
                    reverse(
                        "auth_and_perms:change_to_impostor",
                        kwargs={"pk": obj.user.pk, "org_pk": org.pk},
                    ),
                    _(
                        "Incognito mode: browse the system as this user without modifying your session"
                    ),
                )
                new_uuid = str(uuid.uuid4())
                data_inerit = (
                    """ id="inerit_%s" data-org="%s" data-profileid="%s" data-profile="%s" data-appname="%s" data-model="%s" data-objectid="%s" """
                    % (
                        str(new_uuid),
                        str(contenttypeobj),
                        obj.pk,
                        str(obj),
                        contenttypeobj._meta.app_label,
                        contenttypeobj._meta.model_name,
                        contenttypeobj.pk,
                    )
                )
                impostor += (
                    """<i %s class='fa fa-users me-2' onclick="inerit_profile('%s', %s)" aria-hidden="true" data-bs-toggle="tooltip" data-bs-placement="top" title="%s"></i>"""
                    % (
                        data_inerit,
                        str(new_uuid),
                        str(org.pk),
                        _(
                            "Inherit: propagate the user's profile and roles to all child organizations"
                        ),
                    )
                )

        return """
        <i %s class="fa fa-trash me-2" onclick="deleteuserlab('%s', %s)" aria-hidden="true" data-bs-toggle="tooltip" data-bs-placement="top" title="%s"></i>%s
        """ % (
            datatext,
            action_uuid,
            org.pk,
            _(
                "Remove: remove user from organization, can also disable platform access"
            ),
            impostor,
        )

    class Meta:
        model = Profile
        fields = ["user", "rols", "action", "email"]


class ExternalUserSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=OrganizationStructure.objects.all()
    )

    def validate_email(self, value):
        queryset = User.objects.filter(Q(email=value) | Q(username=value))
        instance = queryset.first()
        if instance is None:
            raise ValidationError(
                detail=_(
                    "User not found, Sorry try to use add user button on organization list"
                )
            )
        return instance

    def validate(self, attrs):
        user = attrs["email"]
        organization = attrs["organization"]
        if organization.users.all().filter(pk=user.pk).exists():
            raise serializers.ValidationError(
                {"email": _("User exist on organization")}
            )
        return attrs

    class Meta:
        model = User
        fields = ["email", "organization"]


class AddExternalUserSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=OrganizationStructure.objects.all(), required=True
    )
    pk = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=True)

    def validate_email(self, value):
        queryset = User.objects.filter(Q(email=value) | Q(username=value))
        instance = queryset.first()
        if instance is None:
            raise ValidationError(
                detail=_(
                    "User not found, Sorry try to use add user button on organization list"
                )
            )
        return instance

    def validate(self, attrs):
        user = attrs["email"]
        organization = attrs["organization"]
        if organization.users.all().filter(pk=user.pk).exists():
            raise ValidationError(detail=_("User exist on organization"))
        if attrs["pk"] != user:
            raise ValidationError(detail=_("User not match with email"))
        return attrs

    class Meta:
        model = User
        fields = ["email", "pk", "organization"]


class ProfileRolDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ProfileSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class DeleteUserFromContenttypeSerializer(serializers.Serializer):
    profile = serializers.PrimaryKeyRelatedField(
        many=False, queryset=Profile.objects.all()
    )
    app_label = serializers.CharField()
    model = serializers.CharField()
    object_id = serializers.IntegerField()
    organization = serializers.PrimaryKeyRelatedField(
        many=False, queryset=OrganizationStructure.objects.all()
    )
    disable_user = serializers.BooleanField(default=False)


class UserAccessOrgLabValidateSerializer(serializers.Serializer):
    laboratory = serializers.PrimaryKeyRelatedField(
        queryset=Laboratory.objects.using(settings.READONLY_DATABASE)
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=OrganizationStructure.objects.using(settings.READONLY_DATABASE)
    )

    def validate(self, data):
        laboratory = data["laboratory"]
        organization = data["organization"]
        user = self.context.get("user")

        has_permission = organization_can_change_laboratory(laboratory, organization)
        check_user_access = check_user_access_kwargs_org_lab(
            organization.pk, laboratory.pk, user
        )

        if not has_permission:
            logger.debug(
                f"ValidateUserAccessOrgLabSerializer --> organization_can_change_laboratory is ({has_permission})"
            )
            raise serializers.ValidationError(
                {"organization": _("Organization can't change this laboratory")}
            )

        if not check_user_access:
            logger.debug(
                f"ValidateUserAccessOrgLabSerializer --> check_user_access_kwargs_org_lab is ({check_user_access})"
            )
            raise serializers.ValidationError(
                {"user": _("User doesn't have permissions")}
            )

        return data


class ValidateUserAccessOrgLabSerializer(UserAccessOrgLabValidateSerializer):
    laboratory = serializers.PrimaryKeyRelatedField(
        queryset=Laboratory.objects.using(settings.READONLY_DATABASE)
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=OrganizationStructure.objects.using(settings.READONLY_DATABASE)
    )
    shelf = serializers.PrimaryKeyRelatedField(
        queryset=Shelf.objects.using(settings.READONLY_DATABASE),
        allow_null=True,
        required=False,
    )
    shelfobject = serializers.PrimaryKeyRelatedField(
        queryset=ShelfObject.objects.using(settings.READONLY_DATABASE),
        allow_null=True,
        required=False,
    )

    def validate(self, data):
        data = super().validate(data)
        laboratory = data["laboratory"]
        organization = data["organization"]
        shelf_object = data.get("shelfobject")
        shelf = data.get("shelf")

        if shelf_object:
            if shelf_object.in_where_laboratory != laboratory:
                logger.debug(
                    f"ValidateUserAccessOrgLabSerializer --> shelfobject.in_where_laboratory!=laboratory"
                )
                raise serializers.ValidationError(
                    {
                        "shelfobject": _(
                            "Shelfobject does not belong to this laboratory."
                        )
                    }
                )

            lab_content_type = ContentType.objects.get_for_model(Laboratory)
            lab_pk = shelf_object.in_where_laboratory.pk

            is_related = OrganizationStructureRelations.objects.filter(
                organization=organization,
                content_type=lab_content_type,
                object_id=lab_pk,
            ).exists()

            if not is_related:
                descendant_pks = organization.descendants(
                    include_self=False
                ).values_list("pk", flat=True)
                is_related = OrganizationStructureRelations.objects.filter(
                    organization__pk__in=descendant_pks,
                    content_type=lab_content_type,
                    object_id=lab_pk,
                ).exists()

            is_owner = shelf_object.in_where_laboratory.organization == organization

            if not is_related and not is_owner:
                logger.debug(
                    f"ValidateUserAccessOrgLabSerializer --> laboratory not related to organization"
                )
                raise serializers.ValidationError(
                    {
                        "shelfobject": _(
                            "Shelfobject does not belong to this organization."
                        )
                    }
                )

            if shelf:
                if shelf != shelf_object.shelf:
                    logger.debug(
                        f"ValidateUserAccessOrgLabSerializer --> shelf != shelf_object.shelf"
                    )
                    raise serializers.ValidationError(
                        {"shelfobject": _("Shelfobject does not belong to this shelf.")}
                    )

        if shelf:
            if shelf.furniture.labroom.laboratory != laboratory:
                logger.debug(
                    f"ValidateUserAccessOrgLabSerializer --> shelf.furniture.labroom.laboratory != laboratory"
                )
                raise serializers.ValidationError(
                    {"shelf": _("Shelf does not belong to this laboratory.")}
                )

            shelf_lab_pk = shelf.furniture.labroom.laboratory.pk
            shelf_is_related = organization.organizationstructurerelations_set.filter(
                content_type__model="laboratory",
                object_id=shelf_lab_pk,
            ).exists()

            if not shelf_is_related:
                descendant_pks = organization.descendants(
                    include_self=False
                ).values_list("pk", flat=True)
                shelf_is_related = OrganizationStructureRelations.objects.filter(
                    organization__pk__in=descendant_pks,
                    content_type__model="laboratory",
                    object_id=shelf_lab_pk,
                ).exists()

            if (
                not shelf_is_related
                and shelf.furniture.labroom.laboratory.organization != organization
            ):
                logger.debug(
                    f"ValidateUserAccessOrgLabSerializer --> shelf.furniture.labroom.laboratory.organization != organization"
                )
                raise serializers.ValidationError(
                    {"shelf": _("Shelf does not belong to this organization.")}
                )

        return data


class ValidateProfileSerializer(serializers.Serializer):
    profile = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.using(settings.READONLY_DATABASE)
    )


class ValidateOrganizationSerializer(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=OrganizationStructure.objects.using(settings.READONLY_DATABASE)
    )

    def validate_organization(self, value):
        organization = super().validate(value)
        if not organization.active:
            logger.debug(
                f"ValidateOrganizationSerializer --> not organization.active = False"
            )
            raise serializers.ValidationError(_("Organization cannot be inactive"))
        return organization


class ValidateGroupsByProfileSerializer(ValidateOrganizationSerializer):
    profile = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.using(settings.READONLY_DATABASE)
    )
    groups = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.using(settings.READONLY_DATABASE),
        many=True,
        required=False,
    )


class ShelfObjectSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    shelf_name = serializers.SerializerMethodField()
    laboratory_name = serializers.SerializerMethodField()

    def get_name(self, obj):
        url = reverse(
            "laboratory:rooms_list",
            kwargs={
                "lab_pk": obj.in_where_laboratory.pk,
                "org_pk": obj.in_where_laboratory.organization.pk,
            },
        ) + "?shelfobject=%d" % (obj.pk)
        name = "<a target='_blank' href=%s>%s</a>" % (url, str(obj.object))
        return name

    def get_shelf_name(self, obj):
        url = reverse(
            "laboratory:rooms_list",
            kwargs={
                "lab_pk": obj.in_where_laboratory.pk,
                "org_pk": obj.in_where_laboratory.organization.pk,
            },
        ) + "?shelf=%d" % (obj.shelf.pk)
        name = "<a target='_blank' href=%s>%s</a>" % (url, obj.shelf.name)
        return name

    def get_laboratory_name(self, obj):
        url = reverse(
            "laboratory:labindex",
            kwargs={
                "lab_pk": obj.in_where_laboratory.pk,
                "org_pk": obj.in_where_laboratory.organization.pk,
            },
        )
        name = "<a target='_blank' href=%s>%s</a>" % (url, obj.in_where_laboratory.name)
        return name

    class Meta:
        model = ShelfObject
        fields = ["id", "name", "shelf_name", "laboratory_name", "quantity"]


class ShelfObjectDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ShelfObjectSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class ValidateSearchShelfObjectSerializer(ValidateOrganizationSerializer):
    object = serializers.PrimaryKeyRelatedField(
        queryset=Object.objects.using(settings.READONLY_DATABASE)
    )


class ValidateLabOrgObjectSerializer(serializers.Serializer):
    laboratory = serializers.PrimaryKeyRelatedField(
        queryset=Laboratory.objects.using(settings.READONLY_DATABASE)
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=OrganizationStructure.objects.using(settings.READONLY_DATABASE)
    )
    object = serializers.PrimaryKeyRelatedField(
        queryset=Object.objects.using(settings.READONLY_DATABASE),
        allow_null=False,
        allow_empty=False,
    )


class ValidateProfileOrganizationSerializer(serializers.Serializer):
    profile = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.using(settings.READONLY_DATABASE),
        many=False,
        required=True,
    )
    organization = serializers.PrimaryKeyRelatedField(
        queryset=OrganizationStructure.objects.using(settings.READONLY_DATABASE),
        many=False,
        required=True,
    )
    app_label = serializers.CharField()
    model = serializers.CharField()
    object_id = serializers.IntegerField()


class ListUserSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    laboratory = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.username if obj.username else ""

    def get_name(self, obj):
        first_name = obj.first_name if obj.first_name else ""
        last_name = obj.last_name if obj.last_name else ""
        return f"{first_name} {last_name}"

    def get_email(self, obj):
        return obj.email if obj.email else ""

    def get_laboratory(self, obj):
        orgs = UserOrganization.objects.filter(
            user=obj,
            organization__isnull=False,
        ).values_list("organization", flat=True)
        labs = OrganizationStructureRelations.objects.filter(
            organization__in=orgs,
            content_type__app_label="laboratory",
            content_type__model="laboratory",
        ).values_list("object_id", flat=True)
        labs = list(
            set(Laboratory.objects.filter(pk__in=labs).values_list("name", "id"))
        )

        buttons = "<ul class='list-group'>"
        for lab in labs:
            pp = ProfilePermission.objects.filter(
                profile=obj.profile,
                content_type__app_label="laboratory",
                content_type__model="laboratory",
                object_id=lab[1],
            )
            if pp.exists():
                buttons += (
                    "<li class='list-group-item d-flex justify-content-between align-items-start'>"
                    "<span class='dropdown-item-text small'>%s</span> "
                    "<button class='btn btn-sm btn-secondary' title='%s' "
                    "data-user='%s' data-lab='%s' onclick=get_roles_in_laboratory(this)>"
                    "<i class='fa fa-user-md' aria-hidden='true'></i> "
                    "<span class='badge bg-secondary'>%s</span></button></li>"
                    % (lab[0], _("Roles"), obj.pk, lab[1], pp.count())
                )

        buttons += "</ul>"

        return buttons

    def get_organization(self, obj):
        orgs = UserOrganization.objects.filter(
            user=obj,
            organization__isnull=False,
        ).values_list("organization", flat=True)
        orgs = list(
            set(
                OrganizationStructure.objects.filter(pk__in=orgs).values_list(
                    "name", "pk"
                )
            )
        )

        buttons = "<ul class='list-group'>"
        for org in orgs:
            pp = ProfilePermission.objects.filter(
                profile=obj.profile,
                content_type__app_label="laboratory",
                content_type__model="organizationstructure",
                object_id=org[1],
            ).first()

            buttons += (
                "<li class='list-group-item d-flex justify-content-between align-items-start'>"
                "<span class='dropdown-item-text small'>%s</span> "
                "<button class='btn btn-sm btn-secondary' title='%s' "
                "data-user='%s' data-org='%s' onclick=get_roles_in_organization(this)>"
                "<i class='fa fa-user-md' aria-hidden='true'></i> "
                "<span class='badge bg-secondary'>%s</span></button></li>"
                % (org[0], _("Roles"), obj.pk, org[1], pp.rol.count() if pp else 0)
            )
        buttons += "</ul>"
        return buttons

    def get_actions(self, obj):
        user = self.context["request"].user
        action_list = {
            "list": user.has_perm("auth_and_perms.view_profile"),
        }
        return action_list

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "username",
            "email",
            "laboratory",
            "organization",
            "actions",
        ]


class UserListDataTableSerializer(serializers.Serializer):
    data = ListUserSerializer(many=True)
    recordsTotal = serializers.IntegerField()
    recordsFiltered = serializers.IntegerField()
    draw = serializers.CharField()


class OrganizationLaboratorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    laboratories = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.name if obj.name else ""

    def get_laboratories(self, obj):
        labs = OrganizationStructureRelations.objects.filter(
            organization=obj,
            content_type__app_label="laboratory",
            content_type__model="laboratory",
        ).values_list("object_id", flat=True)
        labs = list(
            set(Laboratory.objects.filter(pk__in=labs).values_list("name", "id"))
        )

        buttons = "<ul class='list-group'>"
        for lab in labs:
            profile = get_profile_by_organization(obj.pk)
            users = profile.filter(
                profilepermission__content_type__app_label="laboratory",
                profilepermission__content_type__model="laboratory",
                profilepermission__object_id=lab[1],
            ).values_list("user", flat=True)
            buttons += (
                "<li class='list-group-item d-flex justify-content-between align-items-start'>"
                "<span class='dropdown-item-text small'>%s</span> "
                "<button class='btn btn-sm btn-secondary' title='%s' "
                "data-org='%s' data-lab='%s' data-content='%s' onclick=get_roles(this)>"
                "<i class='fa fa-user-md' aria-hidden='true'></i> "
                "<span class='badge bg-secondary'>%s</span></button></li>"
                % (lab[0], _("Users"), obj.pk, lab[1], "organization", users.count())
            )
        buttons += "</ul>"
        return buttons

    class Meta:
        model = OrganizationStructure
        fields = ["name", "laboratories"]


class LaboratoryOrganizationSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    organizations = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.name if obj.name else ""

    def get_organizations(self, obj):
        labs = OrganizationStructureRelations.objects.filter(
            content_type__app_label="laboratory",
            content_type__model="laboratory",
            object_id=obj.pk,
        ).values_list("organization", flat=True)
        labs = list(
            set(
                OrganizationStructure.objects.filter(pk__in=labs)
                .exclude(name="UNA")
                .values_list("name", "id")
            )
        )

        buttons = "<ul class='list-group'>"
        for org in labs:
            profile = get_profile_by_organization(org[1])
            users = profile.filter(
                profilepermission__content_type__app_label="laboratory",
                profilepermission__content_type__model="laboratory",
                profilepermission__object_id=obj.pk,
                profilepermission__organization__pk=org[1],
            ).values_list("user", flat=True)
            buttons += (
                "<li class='list-group-item d-flex justify-content-between align-items-start'>"
                "<span class='dropdown-item-text small'>%s</span> "
                "<button class='btn btn-sm btn-secondary' title='%s' "
                "data-org='%s' data-lab='%s' data-content='%s' onclick=get_roles(this)>"
                "<i class='fa fa-user-md' aria-hidden='true'></i> "
                "<span class='badge bg-secondary'>%s</span></button></li>"
                % (org[0], _("Users"), org[1], obj.pk, "laboratory", users.count())
            )
        buttons += "</ul>"
        return buttons

    class Meta:
        model = Laboratory
        fields = ["name", "organizations"]


class OrganizationLaboratoryDataTableSerializer(serializers.Serializer):
    data = OrganizationLaboratorySerializer(many=True)
    recordsTotal = serializers.IntegerField()
    recordsFiltered = serializers.IntegerField()
    draw = serializers.CharField()


class LaboratoryOrganizationDataTableSerializer(serializers.Serializer):
    data = LaboratoryOrganizationSerializer(many=True)
    recordsTotal = serializers.IntegerField()
    recordsFiltered = serializers.IntegerField()
    draw = serializers.CharField()


class ProfileLaboratoryOrgRoles(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    def get_roles(self, obj):
        contenttypeobj = self.context["view"].contenttypeobj
        org = self.context["view"].organization
        profile_perm = ProfilePermission.objects.filter(
            profile_id=obj.pk,
            content_type__app_label=contenttypeobj._meta.app_label,
            content_type__model=contenttypeobj._meta.model_name,
            object_id=contenttypeobj.pk,
            organization=org,
        ).first()
        if profile_perm:
            roles = list(set(profile_perm.rol.all().values_list("name", flat=True)))
            roles = ", ".join(roles)
            return roles
        return ""

    def get_user(self, obj):
        return str(obj)

    class Meta:
        model = Profile
        fields = ["user", "roles"]


class UserRolesInOrganizationSerializer(serializers.Serializer):
    organization_name = serializers.CharField()
    roles = serializers.ListField(child=serializers.DictField())


class UserRolesInLaboratorySerializer(serializers.Serializer):
    organization_name = serializers.CharField()
    laboratory_name = serializers.CharField()
    roles = serializers.ListField(child=serializers.DictField())


class OrganizationStructureRelationsSerializer(serializers.ModelSerializer):
    laboratory_name = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationStructureRelations
        fields = ["id","laboratory_name","actions"]

    def get_laboratory_name(self, obj):
        if isinstance(obj, dict):
            object_id = obj.get("object_id")
        else:
            object_id = obj.object_id

        try:
            return Laboratory.objects.get(pk=object_id).name
        except Laboratory.DoesNotExist:
            return str(object_id)


    def get_actions(self, obj):
        user = self.context["request"].user
        return {
            "list": user.has_perm("laboratory.view_organizationstructurerelations"),
            "destroy": user.has_perm("laboratory.delete_organizationstructurerelations"),
        }

class OrganizationStructureRelationsDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=OrganizationStructureRelationsSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)
