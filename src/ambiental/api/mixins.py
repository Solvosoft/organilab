from django.core.exceptions import PermissionDenied

from ambiental.access import BuildingAccess
from presentation.api_mixins import OrganizationLogsViewSet


def resolve_path(obj, path):
    for part in path.split("__"):
        if obj is None:
            return None
        obj = getattr(obj, part, None)
    return obj


class AmbientalViewSet(OrganizationLogsViewSet):
    """Base de las APIs del módulo ambiental (ver ``OrganizationLogsViewSet``).

    Además de la organización, acota todo por edificio con ``BuildingAccess``:

    * el queryset solo trae objetos de edificios donde el usuario tiene ``view_<modelo>``;
    * crear exige ``add_<modelo>`` en el edificio del dato nuevo;
    * editar exige ``change_<modelo>`` en el edificio de antes y en el de después (no se
      puede mover un objeto a un edificio ajeno);
    * borrar exige ``delete_<modelo>`` en su edificio.

    ``building_field`` es la ruta al edificio desde el modelo (``building`` o
    ``point__building``).
    """

    building_field = "building"

    def get_access(self):
        return BuildingAccess.for_request(self.request, self.get_organization())

    def model_perm(self, action):
        meta = self.queryset.model._meta
        return "%s.%s_%s" % (meta.app_label, action, meta.model_name)

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.get_access().filter(queryset, self.model_perm("view"), self.building_field)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if "org_pk" in self.kwargs:
            context["building_access"] = self.get_access()
        return context

    def building_from_data(self, data, instance=None):
        first, _sep, rest = self.building_field.partition("__")
        if first in data:
            value = data[first]
            return resolve_path(value, rest) if rest else value
        return resolve_path(instance, self.building_field) if instance is not None else None

    def check_building(self, perm, building):
        if not self.get_access().has(perm, building):
            raise PermissionDenied

    def perform_create(self, serializer):
        self.check_building(self.model_perm("add"), self.building_from_data(serializer.validated_data))
        super().perform_create(serializer)

    def perform_update(self, serializer):
        perm = self.model_perm("change")
        instance = serializer.instance
        self.check_building(perm, resolve_path(instance, self.building_field))
        self.check_building(perm, self.building_from_data(serializer.validated_data, instance))
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        self.check_building(self.model_perm("delete"), resolve_path(instance, self.building_field))
        super().perform_destroy(instance)
