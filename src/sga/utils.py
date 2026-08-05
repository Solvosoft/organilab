"""
Created on 10 mar. 2018
@author: luisza
"""

from async_notifications.utils import send_email_from_template
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
import logging

from auth_and_perms.models import Profile
from laboratory.models import Object
from pending_tasks.models import PendingTask

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
        logger.error("Error sending new substace email", exc_info=e)


def notify_request_created(instance, user, url=None):
    subject = _("New substance request: %(name)s") % {
        "name": instance["name"],
    }
    body = _(
        "Hi,\n\n"
        "A new substance request has been submitted and requires your review.\n\n"
        "Name: %(name)s\n"
        "Requested by: %(user)s\n\n"
        "Please log in to review this request.\n\n"
        "Thanks,\nOrganilab system"
    ) % {
        "name": instance["name"],
        "user": user.get_full_name() or user.username,
    }
    emails = list(
        Group.objects.filter(name="RegisterOrganization")
        .values_list("user__email", "user__pk")
        .exclude(user__email="")
        .distinct()
    )
    for email, pk in emails:
        try:
            profile = Profile.objects.get(user__pk=pk)
        except Profile.DoesNotExist:
            continue
        PendingTask.objects.create(
            name="New Substance Request", description=body, profile=profile, link=url
        )
        _send("lab_or_org_request_created", email, subject, body)


def create_object_notification(instance):
    suscharobj = instance.substancecharacteristics
    obj = Object.objects.create(
        created_by=instance.created_by,
        organization=instance.organization.root,
        name=instance.comercial_name,
        type=Object.REACTIVE,
        has_threshold=suscharobj.has_threshold,
        threshold=suscharobj.threshold,
        is_dangerous=suscharobj.is_dangerous,
        is_pure=suscharobj.is_pure,
        description=instance.description,
    )
    obj.features.add(*instance.features.all())
    suscharobj.object_related = obj
    suscharobj.save()
