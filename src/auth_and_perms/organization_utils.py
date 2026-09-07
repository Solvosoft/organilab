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
    if organization.users.filter(pk=user.pk).exists():
        return True

    user_org_content_type = ContentType.objects.get_for_model(UserOrganization)
    user_org_ids = UserOrganization.objects.filter(user=user).values_list(
        "pk", flat=True
    )
    has_relation = OrganizationStructureRelations.objects.filter(
        organization=organization,
        content_type=user_org_content_type,
        object_id__in=user_org_ids,
    ).exists()

    if has_relation:
        return True

    for ancestor in organization.ancestors():
        if ancestor.users.filter(pk=user.pk).exists():
            return True
        has_ancestor_relation = OrganizationStructureRelations.objects.filter(
            organization=ancestor,
            content_type=user_org_content_type,
            object_id__in=user_org_ids,
        ).exists()
        if has_ancestor_relation:
            return True

    raise PermissionDenied(
        _("User %(user)s not allowed on organization %(organization)r ")
        % {"user": user, "organization": organization}
    )


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

    if org_pk and effective_org is not None:
        query |= Q(
            profile=profile,
            object_id=effective_org.pk,
            content_type__app_label="laboratory",
            content_type__model="organizationstructure",
        )

    return query
