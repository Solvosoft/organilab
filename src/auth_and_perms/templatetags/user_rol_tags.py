from django import template
from django.db.models import Q

from auth_and_perms.models import ProfilePermission, Rol
from laboratory.models import OrganizationStructureRelations, Laboratory
from laboratory.utils import get_laboratories_by_user_profile

register = template.Library()


@register.simple_tag(takes_context=True)
def has_perm_in_org(context, org_pk, permission):
    user = context["request"].user

    if user.is_superuser:
        return True
    app_label, codename = permission.split(".")

    labs = get_laboratories_by_user_profile(user, org_pk)

    profile_in = ProfilePermission.objects.filter(
        profile=context["request"].user.profile
    ).filter(
        Q(
            content_type__app_label="laboratory",
            content_type__model="organizationstructure",
            object_id=org_pk,
        )
        | Q(
            content_type__app_label="laboratory",
            content_type__model="laboratory",
            object_id__in=labs,
        )
    )
    rols = profile_in.filter(rol__isnull=False).values_list("rol", flat=True)
    rolsquery = Rol.objects.filter(
        pk__in=rols,
        permissions__content_type__app_label=app_label,
        permissions__codename=codename,
    )

    return rolsquery.exists()


@register.simple_tag(takes_context=True)
def organization_any_permission_required(context, *args, **kwargs):
    perms = list(args)
    user = context["request"].user
    org = perms.pop(0)
    for perm in perms:
        has_perm = has_perm_in_org(context, org, perm)
        if has_perm:
            return True

    return False
