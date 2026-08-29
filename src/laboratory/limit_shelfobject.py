from django.template.loader import render_to_string

from auth_and_perms.models import Profile
from django.conf import settings
from djgentelella.async_notification.sending import send_email_from_template
from laboratory.models import BlockedListNotification
from django.contrib.sites.models import Site
from django.utils.translation import gettext_lazy as _

from pending_tasks.models import PendingTask
from pending_tasks.utils import create_pending_task


def send_email_limit_objs(lab, shelfobjects, enqueued=True):
    allowed_emails = []
    responsable = None
    if len(shelfobjects) > 0:
        for shelfobject in shelfobjects:
            blocked = BlockedListNotification.objects.filter(
                laboratory=lab, object=shelfobject.object
            )

        responsable = lab.responsible
        if responsable:
            create_pending_task(
                responsable,
                _("ShelfObject expiration"),
                [],
                description=render_to_string(
                    "laboratory/limit_shelfobject_notify.html",
                    {
                        "shelf_objects": shelfobjects,
                        "laboratory": lab,
                        "date": today,
                    },
                ),
                status=PendingTask.PENDING,
                profile=responsable.profile,
                link="",
                notify=True,
            )

            # emails = [responsable.email]
            # context = {
            #     "laboratory": lab,
            #     "shelf_object": shelfobjects,
            # }
            # schema = "https"
            # if settings.DEBUG:
            #     schema = "http"
            # url = f"/lab/{lab.pk}/blocknotifications/"
            # domain = Site.objects.get_current().domain
            # context["blockurl"] = f"{schema}://{domain}{url}"
            # context["domain"] = domain
            # send_email_from_template(
            #     "shelf-object-in-limit",
            #     emails,
            #     context=context,
            #     enqueued=enqueued,
            #     user=None,
            #     upfile=None,
            # )
