from django.conf import settings
from djgentelella.async_notification.backends import get_backend
from djgentelella.async_notification.sending import send_email_from_template
from laboratory.models import BlockedListNotification
from django.contrib.sites.models import Site


def send_email_limit_objs(lab, shelfobjects, enqueued=True):
    if len(shelfobjects) > 0:
        for shelfobject in shelfobjects:
            BlockedListNotification.objects.filter(
                laboratory=lab, object=shelfobject.object
            )
        print(f"lab {lab.id}")
        responsable = lab.responsible
        if responsable:
            schema = "https"
            if settings.DEBUG:
                schema = "http"
            domain = Site.objects.get_current().domain
            url = f"/lab/{lab.pk}/blocknotifications/"
            context = {
                "laboratory": lab,
                "shelf_object": shelfobjects,
                "domain": domain,
                "blockurl": f"{schema}://{domain}{url}",
            }
            print(context)
            notification = send_email_from_template(
                "shelf-object-in-limit",
                responsable.email,
                context=context,
                enqueued=enqueued,
                user=None,
                upfile=None,
            )
            get_backend().sesend_email_from_templatesend_email_from_templatesend_email_from_templatend(notification.pk)
