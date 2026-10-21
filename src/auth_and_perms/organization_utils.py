from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from auth_and_perms.models import ProfilePermission, Profile
from laboratory.models import (
    OrganizationStructureRelations,
    OrganizationStructure,
    UserOrganization,
)


def user_is_allowed_on_organization(user, organization):

    if organization is None:
        raise ObjectDoesNotExist("Organization not found")

    if not user.is_authenticated:
        raise PermissionDenied(
            _("User %(user)s not allowed on organization %(organization)r ") % {
                "user": user,
                "organization": organization,
            }
        )

    if isinstance(organization, (str, int)):
        organization = get_object_or_404(OrganizationStructure, pk=organization)

    # Una vista suele preguntar lo mismo varias veces en la misma petición
    # (decorador, vista, serializer): solo se recuerda el sí, que es lo que no
    # cambia a mitad de una petición.
    allowed_cache = getattr(user, "_org_allowed_cache", None)
    if allowed_cache is None:
        allowed_cache = set()
        try:
            user._org_allowed_cache = allowed_cache
        except AttributeError:
            pass
    if organization.pk in allowed_cache:
        return True

    # La organización y sus ancestros en una consulta, en vez de dos por nivel.
    org_ids = list(
        organization.ancestors(include_self=True).values_list("pk", flat=True)
    )
    allowed = OrganizationStructure.objects.filter(
        pk__in=org_ids, users=user
    ).exists()
    if not allowed:
        user_org_content_type = ContentType.objects.get_for_model(UserOrganization)
        allowed = OrganizationStructureRelations.objects.filter(
            organization__in=org_ids,
            content_type=user_org_content_type,
            object_id__in=UserOrganization.objects.filter(user=user).values("pk"),
        ).exists()
    if allowed:
        allowed_cache.add(organization.pk)
        return True

    raise PermissionDenied(
        _("User %(user)s not allowed on organization %(organization)r ")
        % {"user": user, "organization": organization}
    )


def get_sds_shared_organization_ids(user, org_pk):
    """Organizaciones cuyas sustancias y fichas de seguridad ve `org_pk`.

    Las fichas se comparten con toda la estructura: el árbol completo de la raíz
    (los reactivos suelen crearse en la organización padre y los usan los
    laboratorios hijos) más las organizaciones que algún nodo del árbol tiene
    relacionadas explícitamente, que pueden no colgar de él.
    """
    organization = get_object_or_404(OrganizationStructure, pk=org_pk)
    user_is_allowed_on_organization(user, organization)

    # La propia organización se añade aparte: con un `parent` que apunta a sí
    # misma, `descendants` devuelve vacío aunque se pida `include_self`.
    tree_ids = {organization.pk} | set(
        OrganizationStructure.objects.descendants(
            organization.root, include_self=True
        ).values_list("pk", flat=True)
    )
    related_ids = set(
        OrganizationStructureRelations.objects.filter(
            organization__in=tree_ids,
            content_type__app_label="laboratory",
            content_type__model="organizationstructure",
        ).values_list("object_id", flat=True)
    )
    return tree_ids | related_ids


def organization_can_change_laboratory(laboratory, organization, raise_exec=False):
    if laboratory.organization == organization:
        return True
    if (
        OrganizationStructureRelations.objects.using(settings.READONLY_DATABASE)
        .filter(
            content_type__app_label=laboratory._meta.app_label,
            content_type__model=laboratory._meta.model_name,
            object_id=laboratory.pk,
            organization=organization,
        )
        .exists()
    ):
        return True

    descendants = organization.descendants()
    if (
        OrganizationStructureRelations.objects.using(settings.READONLY_DATABASE)
        .filter(
            content_type__app_label=laboratory._meta.app_label,
            content_type__model=laboratory._meta.model_name,
            object_id=laboratory.pk,
            organization__in=descendants,
        )
        .exists()
    ):
        return True

    if raise_exec:
        raise PermissionDenied(_("You can modify this laboratory"))
    return False


def profile_permission_scope_query(profile, user, org_pk=None, lab_pk=None,
                                   effective_org=None, include_profile=True):
    """El ámbito de `ProfilePermission` que aplica a una petición.

    Es el `Q` con el que `ProfileMiddleware` decide qué roles cuentan para el usuario en
    esta URL, extraído aquí para que no exista en dos sitios: el middleware lo usa para
    autorizar y la sonda de `presentation/probe.py` para atribuir «qué rol hizo esto».
    Si las dos copias se separaran, la medición dejaría de hablar del sistema real.

    Tres ramas, y el orden importa entenderlo:

    - **Por perfil** (siempre): `object_id=profile.pk`. Concede en *todas* las
      organizaciones, y por eso una prueba de aislamiento entre inquilinos no puede
      apoyarse en ella.
    - **Por laboratorio**, cuando la URL trae `lab_pk`: literal, y la única que permite
      distinguir inquilinos.
    - **Por organización efectiva**, cuando la URL trae `org_pk`: la organización del
      árbol en la que el perfil tiene realmente sus permisos.
    - **Por edificio**, cuando la URL trae `org_pk`: los roles asignados sobre edificios
      de esa organización. Dejan **entrar** a las pantallas del módulo ambiental; qué
      edificio puede tocar cada uno lo decide `ambiental.access.BuildingAccess`, porque
      esta bolsa une los roles de todos los edificios.

    `effective_org` y la lista de laboratorios los calcula quien llama, porque en el
    middleware salen de consultas que además deciden si hay que devolver 404.
    `include_profile=False` sirve para componer ramas sin repetir la del perfil.
    """
    from django.db.models import Q

    query = Q(pk__in=()) if not include_profile else Q(
        profile=profile,
        object_id=profile.pk,
        content_type__app_label=profile._meta.app_label,
        content_type__model=profile._meta.model_name,
    )

    if lab_pk:
        query |= Q(
            profile=profile,
            object_id=lab_pk,
            content_type__app_label="laboratory",
            content_type__model="laboratory",
        )

    if org_pk:
        query |= Q(
            profile=profile,
            organization_id=org_pk,
            content_type__app_label="risk_management",
            content_type__model="buildings",
        )

    if org_pk and effective_org is not None:
        query |= Q(
            profile=profile,
            object_id=effective_org.pk,
            content_type__app_label="laboratory",
            content_type__model="organizationstructure",
        )

    return query


class AllPermissions(frozenset):
    """Conjunto de permisos de un superusuario: contiene cualquier permiso."""

    def __contains__(self, item):
        return True


def organization_permissions(user, organization):
    """Permisos que el usuario tiene **en toda la organización**.

    Salen de los roles de su organización efectiva y de su perfil global, más los
    permisos directos y de grupo. A diferencia de lo que arma `ProfileMiddleware`, no
    suman roles de laboratorio ni de edificio: sirve para decidir acciones que abarcan
    toda la organización (parámetros, reglas de alerta, ver todos los edificios).
    """
    from django.db.models import Q

    if not user.is_authenticated or not user.is_active:
        return frozenset()
    if user.is_superuser:
        return AllPermissions()
    profile = getattr(user, "profile", None)
    perms = set()
    if profile is not None:
        query = profile_permission_scope_query(profile, user)
        effective_org = organization.get_effective_org_for_profile(profile)
        if effective_org is not None:
            query |= Q(
                profile=profile,
                object_id=effective_org.pk,
                content_type__app_label="laboratory",
                content_type__model="organizationstructure",
            )
        perms |= {
            "%s.%s" % (app, codename)
            for app, codename in ProfilePermission.objects.filter(query).values_list(
                "rol__permissions__content_type__app_label", "rol__permissions__codename"
            )
            if codename
        }
    perms |= {
        "%s.%s" % (app, codename)
        for app, codename in user.user_permissions.values_list("content_type__app_label", "codename")
    }
    from django.contrib.auth.models import Permission

    perms |= {
        "%s.%s" % (app, codename)
        for app, codename in Permission.objects.filter(group__user=user).values_list(
            "content_type__app_label", "codename"
        )
    }
    return frozenset(perms)
