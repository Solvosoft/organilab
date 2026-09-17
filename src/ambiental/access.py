"""Quién puede ver y tocar qué edificio en el módulo ambiental.

Dos fuentes de permisos, y ninguna más:

* **Organización**: los roles del usuario en su organización efectiva (y su perfil
  global) valen para **todos** los edificios de la organización.
* **Edificio**: un ``ProfilePermission`` con ``content_type=risk_management.Buildings``
  da los permisos de sus roles **solo en ese edificio**.

Los roles de laboratorio y el campo «Responsable» del edificio no dan acceso.

``ProfileMiddleware`` suma los roles de todos los edificios para dejar entrar a las
pantallas; esa bolsa no sirve para autorizar un objeto. Todo lo que filtra o valida por
edificio pasa por ``BuildingAccess``.
"""
from django.contrib.contenttypes.models import ContentType

from auth_and_perms.organization_utils import organization_permissions
from risk_management.models import Buildings

#: Roles que se pueden asignar sobre un edificio.
BUILDING_ROLES = (
    "Administrador ambiental",
    "Encargado de registro ambiental",
    "Analista ambiental",
)


def building_content_type():
    return ContentType.objects.get_for_model(Buildings)


def building_permission_map(user, organization):
    """``{building_id: {permisos}}`` de los roles asignados por edificio."""
    from auth_and_perms.models import ProfilePermission

    profile = getattr(user, "profile", None)
    if profile is None:
        return {}
    rows = ProfilePermission.objects.filter(
        profile=profile,
        organization=organization,
        content_type=building_content_type(),
    ).values_list(
        "object_id",
        "rol__permissions__content_type__app_label",
        "rol__permissions__codename",
    )
    result = {}
    for building_id, app, codename in rows:
        perms = result.setdefault(building_id, set())
        if codename:
            perms.add("%s.%s" % (app, codename))
    return result


class BuildingAccess:
    def __init__(self, user, organization):
        self.user = user
        self.organization = organization
        self.org_perms = organization_permissions(user, organization)
        self.building_perms = building_permission_map(user, organization)

    @classmethod
    def for_request(cls, request, organization):
        cache = request.__dict__.setdefault("_ambiental_building_access", {})
        if organization.pk not in cache:
            cache[organization.pk] = cls(request.user, organization)
        return cache[organization.pk]

    def has_org_perm(self, perm):
        return perm in self.org_perms

    def has(self, perm, building):
        """¿Tiene ``perm`` sobre ``building`` (instancia o pk)?"""
        if building is None:
            return self.has_org_perm(perm)
        building_id = getattr(building, "pk", building)
        if self.has_org_perm(perm):
            return Buildings.objects.filter(pk=building_id, organization=self.organization).exists()
        return perm in self.building_perms.get(building_id, ())

    def building_ids(self, perm):
        """Pks de los edificios donde tiene ``perm``; ``None`` significa todos."""
        if self.has_org_perm(perm):
            return None
        return [building_id for building_id, perms in self.building_perms.items() if perm in perms]

    def buildings(self, perm):
        queryset = Buildings.objects.filter(organization=self.organization)
        ids = self.building_ids(perm)
        return queryset if ids is None else queryset.filter(pk__in=ids)

    def filter(self, queryset, perm, building_field):
        """Acota un queryset por el campo que apunta al edificio."""
        ids = self.building_ids(perm)
        if ids is None:
            return queryset
        return queryset.filter(**{"%s__in" % building_field: ids})
