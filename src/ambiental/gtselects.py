from django.core.exceptions import PermissionDenied
from djgentelella.groute import register_lookups
from djgentelella.permission_management import AnyPermissionByAction
from djgentelella.views.select2autocomplete import BaseSelect2View
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication

from ambiental.ambiental_defaults import RESOURCE_TYPES
from ambiental.api.serializers import resource_info_payload

from ambiental.models import MeasurementPoint
from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.gtselects import GPaginatorMoreElements
from laboratory.models import Laboratory, OrganizationStructure
from risk_management.models import Buildings


class AmbientalOrganizationSelect(BaseSelect2View):
    """Base de los autocompletes del módulo: todo se acota a la organización.

    A diferencia de los autocompletes de ``risk_management``, aquí se comprueba
    que el usuario pertenezca a la organización pedida: sin eso, cualquiera con
    el permiso de modelo podría listar los edificios de otra institución
    cambiando ``org_pk`` en la URL.
    """

    authentication_classes = [SessionAuthentication]
    pagination_class = GPaginatorMoreElements
    permission_classes = (AnyPermissionByAction,)

    def get_organization(self):
        org_pk = self.request.GET.get("org_pk")
        if not org_pk or not str(org_pk).isdigit():
            return None
        organization = OrganizationStructure.objects.filter(pk=org_pk).first()
        if organization is None:
            return None
        try:
            user_is_allowed_on_organization(self.request.user, organization)
        except PermissionDenied:
            return None
        return organization

    def get_queryset(self):
        organization = self.get_organization()
        if organization is None:
            return self.model.objects.none()
        return self.scope_queryset(super().get_queryset(), organization)

    def scope_queryset(self, queryset, organization):
        return queryset.filter(organization=organization)

    def get_building(self):
        building = self.request.GET.get("building")
        if building and str(building).isdigit():
            return building
        return None


@register_lookups(prefix="ambiental_buildings", basename="ambiental_buildings")
class AmbientalBuildings(AmbientalOrganizationSelect):
    model = Buildings
    fields = ["name"]
    order_by = "name"
    perms = {"list": ["ambiental.view_measurementpoint"]}


@register_lookups(prefix="ambiental_laboratories", basename="ambiental_laboratories")
class AmbientalLaboratories(AmbientalOrganizationSelect):
    model = Laboratory
    fields = ["name"]
    order_by = "name"
    perms = {"list": ["ambiental.view_measurementpoint"]}

    def scope_queryset(self, queryset, organization):
        return queryset.filter(pk__in=organization.get_my_laboratories).distinct()


@register_lookups(prefix="ambiental_points", basename="ambiental_points")
class AmbientalMeasurementPoints(AmbientalOrganizationSelect):
    model = MeasurementPoint
    fields = ["code", "name"]
    order_by = "code"
    text_separator = " - "
    perms = {"list": ["ambiental.view_measurementpoint"]}

    def scope_queryset(self, queryset, organization):
        queryset = queryset.filter(organization=organization).select_related("resource_type")
        building = self.get_building()
        if building:
            queryset = queryset.filter(building__pk=building)
        waste = self.request.GET.get("waste")
        if waste in ("0", "1"):
            waste_resources = [
                name for name, info in RESOURCE_TYPES.items() if info["is_waste"]
            ]
            lookup = {"resource_type__description__in": waste_resources}
            queryset = queryset.filter(**lookup) if waste == "1" else queryset.exclude(**lookup)
        return queryset

    def get_serializer_class(self):
        # Cada opción lleva la unidad y los campos del recurso: al elegir el punto,
        # el formulario de consumo precarga la unidad y muestra solo lo que aplica.
        base = super().get_serializer_class()

        class PointSerializer(base):
            resource_info = serializers.SerializerMethodField()

            def get_resource_info(self, obj):
                return resource_info_payload(obj)

            class Meta(base.Meta):
                fields = base.Meta.fields + ["resource_info"]

        return PointSerializer
