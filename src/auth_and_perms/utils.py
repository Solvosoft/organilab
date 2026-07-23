import logging
import uuid

from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from rest_framework import permissions

from auth_and_perms.models import Rol, ProfilePermission
from laboratory.models import OrganizationStructure, ObjectLogChange

logger = logging.getLogger("organilab")


def get_roles_by_user(user):
    orgs = OrganizationStructure.os_manager.filter_user(user).values_list(
        "pk", flat=True
    )
    return Rol.objects.filter(organizationstructure__in=orgs).distinct()


def get_rol_name(rol):
    org_str = ""
    for i, org in enumerate(rol.organizationstructure_set.all()):
        if i:
            org_str += " -- "
        org_str += org.name

    return f"{rol.pk} {rol.name} ({org_str})"


def get_roles_in_html(user, lab, org):
    profile = ProfilePermission.objects.filter(
        profile_id=user,
        content_type__app_label=lab._meta.app_label,
        content_type__model=lab._meta.model_name,
        object_id=lab.pk,
    ).first()
    roles = []
    if profile:
        for rol in profile.rol.filter(organizationstructure=org):
            rol_uuid = str(uuid.uuid4())
            datatext = (
                """data-org="%d" data-profile="%d" data-appname="%s" data-model="%s" data-objectid="%s" """
                % (org.pk, user, lab._meta.app_label, lab._meta.model_name, lab.pk)
            )
            roles.append(
                """<span class="applyasrole small" onclick="applyasrole('%s', %s)" id="rol_%s" style="color: %s;" title="%s" %s>%s</span>"""
                % (
                    rol_uuid,
                    user,
                    rol_uuid,
                    rol.color.replace("[", "")
                    .replace("]", "")
                    .replace("'", "")
                    .strip(),
                    get_rol_name(rol),
                    datatext,
                    rol.name[0],
                )
            )
        return " ".join(roles)
    return None


# Fixme: move to relevant place
def send_email(request, user):
    schema = request.scheme + "://"
    context = {"user": user, "domain": schema + request.get_host()}
    send_mail(
        subject="Nuevo usuario creado en la plataforma",
        message="Por favor use un visor de html",
        recipient_list=[user.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
        html_message=render_to_string(
            "gentelella/registration/new_user.html", context=context
        ),
    )


def get_ip_address(request):
    """
    try to obtain the ip address from request

    :param request:
    :return:
    """
    try:
        ip_addr = request.META.get(
            "HTTP_X_FORWARDED_FOR",
            request.META.get("HTTP_X_REAL_IP", request.META.get("REMOTE_ADDR", "")),
        )
    except AttributeError:
        ip_addr = ""
    # if there are several ip addresses separated by comma like HTTP_X_FORWARDED_FOR returns,
    # take only the first one, which is the client's address
    if "," in ip_addr:
        ip_addr = ip_addr.split(",", 1)[0].strip()
    return ip_addr


def preserve_audit_trail_before_delete(user):
    """Reassign LogEntry/ObjectLogChange rows from `user` to the sentinel
    configured in DELETED_USER_SENTINEL_USERNAME, tagging each with the
    original user's name. Must run before `user.delete()` — a signal fired
    during delete() runs after Django has already collected CASCADE rows by
    pk, too late to rescue them by changing their FK value."""
    sentinel_username = getattr(settings, "DELETED_USER_SENTINEL_USERNAME", None)
    sentinel = None
    if sentinel_username:
        sentinel = (
            User.objects.filter(username=sentinel_username)
            .exclude(pk=user.pk)
            .first()
        )

    if not sentinel:
        logger.warning(
            "DELETED_USER_SENTINEL_USERNAME (%s) not configured or user not found; "
            "audit trail for user %s will be lost on delete.",
            sentinel_username,
            user.username,
        )
        return

    full_name = user.get_full_name() or user.username
    tag = _("Deleted user: %(full_name)s (%(username)s)") % {
        "full_name": full_name,
        "username": user.username,
    }

    log_entries = list(LogEntry.objects.filter(user=user))
    if log_entries:
        suffix = f" ({tag})"
        for entry in log_entries:
            entry.object_repr = f"{entry.object_repr[:200 - len(suffix)]}{suffix}"[:200]
            entry.user = sentinel
        LogEntry.objects.bulk_update(log_entries, ["object_repr", "user"])

    ObjectLogChange.objects.filter(user=user).update(
        deleted_user_info=tag[:200],
        user=sentinel,
    )
