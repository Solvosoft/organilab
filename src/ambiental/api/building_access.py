"""API de la pantalla «Acceso por edificio».

Cada fila es un ``ProfilePermission`` sobre un edificio: una persona, un edificio y los
roles ambientales que tiene ahí. Solo se listan, crean, editan y borran filas de
edificios donde quien opera tiene ``ambiental.manage_building_access``.
"""
from django.contrib.admin.models import ADDITION, CHANGE
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django_filters import FilterSet, NumberFilter
from rest_framework import serializers

from ambiental.access import BUILDING_ROLES, building_content_type
from ambiental.api.mixins import AmbientalViewSet
from ambiental.api.serializers import DataTableSerializer
from auth_and_perms.models import Profile, ProfilePermission, Rol
from laboratory.models import UserOrganization
from presentation.parameters import organization_chain
from risk_management.models import Buildings

MANAGE_PERM = "ambiental.manage_building_access"


def organization_users(organization):
    """Personas que pueden entrar a la organización: miembros de ella o de un ancestro."""
    user_ids = UserOrganization.objects.filter(
        organization__in=organization_chain(organization), user__isnull=False, status=True
    ).values_list("user", flat=True)
    return get_user_model().objects.filter(pk__in=user_ids, is_active=True)


def user_display(user):
    full_name = user.get_full_name()
    return "%s (%s)" % (full_name, user.username) if full_name else user.username


class BuildingAccessSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    building = serializers.SerializerMethodField()
    rol = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    def get_user(self, obj):
        user = obj.profile.user
        return {"id": user.pk, "text": user_display(user)}

    def get_building(self, obj):
        building = self.context["buildings"].get(obj.object_id)
        return {"id": obj.object_id, "text": building.name if building else "---"}

    def get_rol(self, obj):
        return [{"id": rol.pk, "text": rol.name} for rol in obj.rol.all()]

    def get_actions(self, obj):
        allowed = self.context["building_access"].has(MANAGE_PERM, obj.object_id)
        return {"update": allowed, "destroy": allowed}

    class Meta:
        model = ProfilePermission
        fields = ("id", "user", "building", "rol", "actions")


class BuildingAccessDataTableSerializer(DataTableSerializer):
    data = serializers.ListField(child=BuildingAccessSerializer(), required=True)


class BuildingAccessSaveSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.none())
    building = serializers.PrimaryKeyRelatedField(queryset=Buildings.objects.none())
    rol = serializers.PrimaryKeyRelatedField(
        queryset=Rol.objects.filter(name__in=BUILDING_ROLES), many=True, allow_empty=False
    )

    def get_fields(self):
        fields = super().get_fields()
        organization = self.context.get("organization")
        access = self.context.get("building_access")
        if organization is not None and access is not None:
            fields["user"].queryset = organization_users(organization)
            fields["building"].queryset = access.buildings(MANAGE_PERM)
        return fields

    def validate(self, attrs):
        if self.instance is not None:
            if attrs["user"] != self.instance.profile.user or attrs["building"].pk != self.instance.object_id:
                raise serializers.ValidationError(
                    {"building": [_("To move an access, delete it and create a new one.")]}
                )
        return attrs

    def to_representation(self, instance):
        return BuildingAccessSerializer(instance, context=self.context).data

    def save(self, **kwargs):
        organization = self.context["organization"]
        user = self.validated_data["user"]
        building = self.validated_data["building"]
        profile, _created = Profile.objects.get_or_create(user=user)
        permission = self.instance or ProfilePermission.objects.filter(
            profile=profile, organization=organization,
            content_type=building_content_type(), object_id=building.pk,
        ).first()
        if permission is None:
            permission = ProfilePermission.objects.create(
                profile=profile, organization=organization,
                content_type=building_content_type(), object_id=building.pk,
            )
        permission.rol.set(self.validated_data["rol"])
        self.instance = permission
        return permission


class BuildingAccessFilter(FilterSet):
    user = NumberFilter(field_name="profile__user")
    building = NumberFilter(field_name="object_id")

    class Meta:
        model = ProfilePermission
        fields = ["user", "building"]


class BuildingAccessViewSet(AmbientalViewSet):
    serializer_class = {
        "list": BuildingAccessDataTableSerializer,
        "create": BuildingAccessSaveSerializer,
        "update": BuildingAccessSaveSerializer,
        "retrieve": BuildingAccessSerializer,
        "get_values_for_update": BuildingAccessSerializer,
    }
    perms = {
        "list": [MANAGE_PERM],
        "create": [MANAGE_PERM],
        "update": [MANAGE_PERM],
        "retrieve": [MANAGE_PERM],
        "get_values_for_update": [MANAGE_PERM],
        "destroy": [MANAGE_PERM],
    }
    queryset = ProfilePermission.objects.select_related("profile__user").prefetch_related("rol")
    search_fields = ["profile__user__username", "profile__user__first_name", "profile__user__last_name"]
    filterset_class = BuildingAccessFilter
    ordering_fields = ["object_id", "profile__user__username"]
    ordering = ("object_id", "profile__user__username")
    building_field = "object_id"

    def get_queryset(self):
        queryset = super(AmbientalViewSet, self).get_queryset().filter(
            content_type=building_content_type()
        )
        return self.get_access().filter(queryset, MANAGE_PERM, "object_id")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if "org_pk" in self.kwargs:
            context["buildings"] = {
                building.pk: building
                for building in Buildings.objects.filter(organization=self.get_organization())
            }
        return context

    def get_related_objects(self, instance):
        building = Buildings.objects.filter(pk=instance.object_id).first()
        return [building, instance.profile.user]

    def check_building(self, perm, building):
        if not self.get_access().has(MANAGE_PERM, building):
            raise PermissionDenied

    def perform_create(self, serializer):
        self.check_building(MANAGE_PERM, serializer.validated_data["building"])
        serializer.save()
        if self.should_log(serializer.instance):
            self._add_log(serializer.instance, ADDITION, ["rol"], _("Building access granted"))

    def perform_update(self, serializer):
        self.check_building(MANAGE_PERM, serializer.instance.object_id)
        serializer.save()
        if self.should_log(serializer.instance):
            self._add_log(serializer.instance, CHANGE, ["rol"], _("Building access changed"))

    def perform_destroy(self, instance):
        self.check_building(MANAGE_PERM, instance.object_id)
        super(AmbientalViewSet, self).perform_destroy(instance)
