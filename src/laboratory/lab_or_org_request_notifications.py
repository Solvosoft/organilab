from django.contrib.auth.models import Group
from django.utils.translation import gettext as _

from async_notifications.utils import send_email_from_template

import logging

logger = logging.getLogger("organilab")


def _send(code, email, subject, body):
    try:
        send_email_from_template(
            code,
            email,
            context={"subject": subject, "body": body},
            enqueued=False,
            user=None,
            upfile=None,
        )
    except Exception as e:
        logger.error("Error sending lab_or_org_request email", exc_info=e)


def notify_request_created(instance):
    subject = _("New %(type)s request: %(name)s") % {
        "type": instance.get_entity_type_display(),
        "name": instance.name,
    }
    body = _(
        "Hi,\n\n"
        "A new %(type)s request has been submitted and requires your review.\n\n"
        "Name: %(name)s\n"
        "Requested by: %(user)s\n\n"
        "Please log in to review this request.\n\n"
        "Thanks,\nOrganilab system"
    ) % {
        "type": instance.get_entity_type_display(),
        "name": instance.name,
        "user": instance.requested_by.get_full_name() or instance.requested_by.username,
    }
    emails = list(
        Group.objects.filter(name="RegisterOrganization")
        .values_list("user__email", flat=True)
        .exclude(user__email="")
        .distinct()
    )
    for email in emails:
        _send("lab_or_org_request_created", email, subject, body)


def notify_request_status_changed(instance):
    status_display = instance.get_status_display()
    subject = _("Your request '%(name)s' has been %(status)s") % {
        "name": instance.name,
        "status": status_display,
    }
    body = _(
        "Hi %(user)s,\n\n"
        "Your %(type)s request '%(name)s' has been %(status)s.\n\n"
        "Thanks,\nOrganilab system"
    ) % {
        "user": instance.requested_by.get_full_name() or instance.requested_by.username,
        "type": instance.get_entity_type_display(),
        "name": instance.name,
        "status": status_display,
    }
    email = instance.requested_by.email
    if email:
        _send("lab_or_org_request_status_changed", email, subject, body)