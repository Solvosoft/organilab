"""Fusión y eliminación de usuarios a nivel de plataforma.

Un usuario pertenece a varias organizaciones, así que estas operaciones no
dependen de ninguna: las autoriza `auth_and_perms.can_manage_users` (o ser
superusuario) y nunca un rol de organización.

Cada relación que apunta a `User` o a `Profile` está clasificada:

- ``MOVE``: datos y trazas (autoría, bitácoras, reservas…). Pasan al usuario
  destino al fusionar y al usuario centinela al eliminar, para no perderlos.
- ``MEMBERSHIP``: pertenencias y responsabilidades (roles, organizaciones,
  progreso de tutoriales…). Pasan al destino al fusionar; al eliminar se
  descartan, porque darle al centinela los roles del usuario sería un error.
- ``PERSONAL``: credenciales y datos propios del usuario (perfil, TOTP,
  tokens…). No se mueven y se borran con él.

`tests.test_user_merge` falla si aparece una relación sin clasificar; en tiempo
de ejecución una relación desconocida se trata como ``MOVE``, que no pierde datos.
"""

import logging

from django.conf import settings
from django.contrib.admin.models import CHANGE, DELETION
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from auth_and_perms.models import Profile, ProfilePermission
from auth_and_perms.user_notifications import notify_user_deleted, notify_user_merged
from auth_and_perms.utils import preserve_audit_trail_before_delete

logger = logging.getLogger("organilab")

MOVE = "move"
MEMBERSHIP = "membership"
PERSONAL = "personal"

USER_RELATIONS = {
    "admin.LogEntry.user": MOVE,
    "auth_and_perms.Profile.user": PERSONAL,
    "auth_and_perms.RegistrationUser.user": PERSONAL,
    "auth_and_perms.UserTOTPDevice.user": PERSONAL,
    "auth_and_perms.AuthorizedApplication.user": MEMBERSHIP,
    "auth_and_perms.ImpostorLog.impostor": MOVE,
    "auth_and_perms.ImpostorLog.imposted_as": MOVE,
    "auth_and_perms.UserDeletionRequest.user": PERSONAL,
    "presentation.FeedbackEntry.user": MOVE,
    "presentation.TutorialProgress.user": MEMBERSHIP,
    "laboratory.OrganizationStructure.users": MEMBERSHIP,
    "laboratory.UserOrganization.user": MEMBERSHIP,
    "laboratory.Laboratory.responsible": MEMBERSHIP,
    "laboratory.ObjectLogChange.user": MOVE,
    "laboratory.BlockedListNotification.user": MEMBERSHIP,
    "laboratory.Protocol.upload_by": MOVE,
    "laboratory.LabOrOrgRequest.responsible": MEMBERSHIP,
    "laboratory.LabOrOrgRequest.requested_by": MOVE,
    "djreservation.Reservation.user": MOVE,
    "authtoken.Token.user": PERSONAL,
    "sga.BuilderInformation.user": MOVE,
    "sga.SDSTraceability.verified_by": MOVE,
    "async_notification.EmailNotification.user": PERSONAL,
    "risk_management.Regent.user": MEMBERSHIP,
    "risk_management.Buildings.manager": MEMBERSHIP,
    "risk_management.Structure.manager": MEMBERSHIP,
    "risk_management.IPERAssessment.responsible": MEMBERSHIP,
    "risk_management.IPERObservation.author": MOVE,
    "djgentelella.Notification.user": MEMBERSHIP,
    "djgentelella.ChunkedUpload.user": PERSONAL,
    "djgentelella.Trash.deleted_by": MOVE,
    "djgentelella.UserSignatureConfig.user": PERSONAL,
    "reservations_management.Reservations.user": MOVE,
    "reservations_management.ReservedProducts.user": MOVE,
    "otp_totp.TOTPDevice.user": PERSONAL,
    "report.ObjectChangeLogReportBuilder.user": MOVE,
}

PROFILE_RELATIONS = {
    "auth_and_perms.ProfilePermission.profile": MEMBERSHIP,
    "laboratory.ShelfObjectMaintenance.validator": MOVE,
    "laboratory.ShelfObjectCalibrate.validator": MOVE,
    "laboratory.ShelfObjectTraining.intern_people_receive_training": MOVE,
    "pending_tasks.PendingTask.profile": MEMBERSHIP,
}

# Relaciones con filas que no pueden duplicarse: se fusionan a mano antes del
# traspaso genérico.
UNIQUE_MERGED = {
    "presentation.TutorialProgress.user",
    "laboratory.UserOrganization.user",
    "auth_and_perms.ProfilePermission.profile",
}


class UserManagementError(Exception):
    pass


def relation_label(rel):
    return "%s.%s" % (rel.related_model._meta.label, rel.field.name)


def classify(rel, relations):
    label = relation_label(rel)
    if label in relations:
        return relations[label]
    # La autoría (`created_by`) siempre es un dato que se conserva.
    return MOVE


def get_sentinel_user():
    username = getattr(settings, "DELETED_USER_SENTINEL_USERNAME", None)
    sentinel = User.objects.filter(username=username).first() if username else None
    if sentinel is None:
        raise UserManagementError(
            _("The sentinel user (%(username)s) does not exist; users cannot be deleted without losing their data.")
            % {"username": username}
        )
    return sentinel


def check_can_manage(actor, *users):
    """Valida las reglas comunes; lanza `UserManagementError` si no se cumplen."""
    sentinel_username = getattr(settings, "DELETED_USER_SENTINEL_USERNAME", None)
    for user in users:
        if user.pk == actor.pk:
            raise UserManagementError(_("You cannot delete or merge your own user."))
        if user.username == sentinel_username:
            raise UserManagementError(_("The sentinel user cannot be deleted or merged."))
        if user.is_superuser and not actor.is_superuser:
            raise UserManagementError(_("Only a superuser can delete or merge a superuser."))


def _move_foreign_keys(relations, classification, source, target, categories):
    for rel in relations:
        label = relation_label(rel)
        if rel.one_to_one or label in UNIQUE_MERGED or classify(rel, classification) not in categories:
            continue
        if rel.many_to_many:
            _move_many_to_many(rel, source, target)
        else:
            # `_base_manager` incluye las filas que los managers ocultan (papelera).
            rel.related_model._base_manager.filter(**{rel.field.name: source}).update(**{rel.field.name: target})


def _move_many_to_many(rel, source, target):
    through = rel.through
    field = rel.field
    user_attname = through._meta.get_field(field.m2m_reverse_field_name()).attname
    owner_attname = through._meta.get_field(field.m2m_field_name()).attname
    manager = through._base_manager
    already = manager.filter(**{user_attname: target.pk}).values_list(owner_attname, flat=True)
    manager.filter(**{user_attname: source.pk, "%s__in" % owner_attname: list(already)}).delete()
    manager.filter(**{user_attname: source.pk}).update(**{user_attname: target.pk})


def _merge_tutorial_progress(source, target):
    from presentation.models import TutorialProgress

    targets = {progress.tutorial_id: progress for progress in TutorialProgress.objects.filter(user=target)}
    for progress in TutorialProgress.objects.filter(user=source):
        existing = targets.get(progress.tutorial_id)
        if existing is None:
            progress.user = target
            progress.save(update_fields=["user"])
        elif progress.completed and not existing.completed:
            existing.delete()
            progress.user = target
            progress.save(update_fields=["user"])
        else:
            progress.delete()


def _merge_user_organizations(source, target):
    from laboratory.models import UserOrganization

    for membership in UserOrganization.objects.filter(user=source):
        existing = UserOrganization.objects.filter(user=target, organization_id=membership.organization_id).first()
        if existing is None:
            membership.user = target
            membership.save(update_fields=["user"])
            continue
        # El número menor es el tipo con más privilegios (administrador = 1).
        existing.type_in_organization = min(existing.type_in_organization, membership.type_in_organization)
        existing.status = existing.status or membership.status
        existing.save(update_fields=["type_in_organization", "status"])
        membership.delete()


def _merge_profile_permissions(source_profile, target_profile):
    for permission in ProfilePermission.objects.filter(profile=source_profile):
        existing = ProfilePermission.objects.filter(
            profile=target_profile,
            organization_id=permission.organization_id,
            content_type_id=permission.content_type_id,
            object_id=permission.object_id,
        ).first()
        if existing is None:
            permission.profile = target_profile
            permission.save(update_fields=["profile"])
        else:
            existing.rol.add(*permission.rol.all())
            permission.delete()


def _profile_of(user):
    profile, _created = Profile.objects.get_or_create(user=user)
    return profile


def _reassign(source, target, categories):
    _move_foreign_keys(User._meta.related_objects, USER_RELATIONS, source, target, categories)
    source_profile = Profile.objects.filter(user=source).first()
    if source_profile is not None:
        _move_foreign_keys(Profile._meta.related_objects, PROFILE_RELATIONS, source_profile, _profile_of(target), categories)


@transaction.atomic
def merge_users(source, target, actor):
    """Pasa todo lo de `source` a `target` y elimina `source`."""
    if source.pk == target.pk:
        raise UserManagementError(_("A user cannot be merged with itself."))
    check_can_manage(actor, source)
    if target.username == getattr(settings, "DELETED_USER_SENTINEL_USERNAME", None):
        raise UserManagementError(_("The sentinel user cannot be deleted or merged."))
    if target.is_superuser and not actor.is_superuser:
        raise UserManagementError(_("Only a superuser can delete or merge a superuser."))

    _merge_tutorial_progress(source, target)
    _merge_user_organizations(source, target)
    source_profile = Profile.objects.filter(user=source).first()
    if source_profile is not None:
        target_profile = _profile_of(target)
        _merge_profile_permissions(source_profile, target_profile)
        target_profile.laboratories.add(*source_profile.laboratories.all())
        target_profile.workplace.add(*source_profile.workplace.all())
    target.groups.add(*source.groups.all())
    target.user_permissions.add(*source.user_permissions.all())

    _reassign(source, target, {MOVE, MEMBERSHIP})

    description = "%s (%s)" % (source.get_full_name() or source.username, source.username)
    source.delete()
    _log(actor, target, CHANGE, "User %s merged into %s" % (description, target.username))
    transaction.on_commit(lambda: notify_user_merged(source, target))
    logger.info("User %s merged into %s by %s", description, target.username, actor.username)
    return target


@transaction.atomic
def delete_user(user, actor=None):
    """Elimina `user` conservando sus datos y trazas en el usuario centinela.

    `actor` es None cuando la elimina la tarea de usuarios inactivos.
    """
    if actor is not None:
        check_can_manage(actor, user)
    sentinel = get_sentinel_user()
    if user.pk == sentinel.pk:
        raise UserManagementError(_("The sentinel user cannot be deleted or merged."))

    preserve_audit_trail_before_delete(user)
    _reassign(user, sentinel, {MOVE})

    description = "%s (%s)" % (user.get_full_name() or user.username, user.username)
    _log(actor or sentinel, user, DELETION, "User %s deleted" % description)
    user.delete()
    transaction.on_commit(lambda: notify_user_deleted(user))
    logger.info("User %s deleted by %s", description, actor.username if actor else "inactive users task")


def _log(actor, user, action_flag, message):
    from laboratory.utils import organilab_logentry

    # relobj=[]: la operación es de plataforma, no de una organización.
    organilab_logentry(actor, user, action_flag, change_message=message, relobj=[])
