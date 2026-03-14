from auth_and_perms.models import Profile
from django.conf import settings
from async_notifications.utils import send_email_from_template
from laboratory.models import BlockedListNotification
from django.contrib.sites.models import Site
from django.utils.translation import gettext_lazy as _


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
            emails = [responsable.email]
            context = {
                "laboratory": lab,
                "shelf_object": shelfobjects,
            }
            schema = "https"
            if settings.DEBUG:
                schema = "http"
            url = f"/lab/{lab.pk}/blocknotifications/"
            domain = Site.objects.get_current().domain
            context["blockurl"] = f"{schema}://{domain}{url}"
            context["domain"] = domain
            send_email_from_template(
                _("Shelf object in limit"),
                emails,
                context=context,
                enqueued=enqueued,
                user=None,
                upfile=None,
            )
