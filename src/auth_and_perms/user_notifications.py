"""Correos de la gestión de usuarios de plataforma.

Siguen el patrón de `laboratory.lab_or_org_request_notifications`: el asunto y
el cuerpo se traducen aquí, en el idioma del perfil del destinatario, y la
plantilla de correo solo los inserta.
"""

import logging

from django.utils import translation
from django.utils.translation import gettext as _
from djgentelella.async_notification.sending import send_email_from_template

logger = logging.getLogger("organilab")

CODE_MERGED = "user-merged"
CODE_DELETED = "user-deleted"
CODE_DELETION_WARNING = "user-deletion-warning"


def _language_of(user):
    profile = getattr(user, "profile", None)
    return getattr(profile, "language", None) or translation.get_language()


def _send(code, user, build):
    if not user.email:
        return
    with translation.override(_language_of(user)):
        subject, body = build()
    try:
        send_email_from_template(code, user.email, context={"subject": subject, "body": body}, enqueued=True, user=None, upfile=None)
    except Exception as e:
        logger.error("Error sending %s email", code, exc_info=e)


def _name(user):
    return user.get_full_name() or user.username


def notify_user_merged(source, target):
    def build():
        subject = _("Your Organilab account was merged")
        body = _(
            "Hi %(name)s,\n\n"
            "Your Organilab account %(source)s was merged into the account %(target)s. "
            "From now on use %(target)s to log in; your information is available there.\n\n"
            "Thanks,\nOrganilab system"
        ) % {"name": _name(source), "source": source.username, "target": target.username}
        return subject, body

    _send(CODE_MERGED, source, build)


def notify_user_deleted(user):
    def build():
        subject = _("Your Organilab account was deleted")
        body = _(
            "Hi %(name)s,\n\n"
            "Your Organilab account %(username)s was deleted. "
            "The records you created remain in the system to preserve its history.\n\n"
            "Thanks,\nOrganilab system"
        ) % {"name": _name(user), "username": user.username}
        return subject, body

    _send(CODE_DELETED, user, build)


def notify_user_deletion_warning(deletion_request, days_left):
    user = deletion_request.user

    def build():
        subject = _("Your Organilab account will be deleted in %(days)d days") % {"days": days_left}
        body = _(
            "Hi %(name)s,\n\n"
            "Your Organilab account %(username)s has not been used for a long time and will be deleted on %(date)s. "
            "If you want to keep it, just log in before that date.\n\n"
            "Thanks,\nOrganilab system"
        ) % {"name": _name(user), "username": user.username, "date": deletion_request.expiration_date.date().isoformat()}
        return subject, body

    _send(CODE_DELETION_WARNING, user, build)


def register_email_contexts():
    from djgentelella.async_notification.registry import register_context

    for code in (CODE_MERGED, CODE_DELETED, CODE_DELETION_WARNING):
        register_context(
            code=code,
            subject="{{ subject|safe }}",
            models={},
            extra_variables={
                "subject": "Rendered subject of the email",
                "body": "Rendered body of the email",
            },
        )
