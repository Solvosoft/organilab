from __future__ import absolute_import, unicode_literals
from laboratory.models import Profile
from django.conf import settings
from async_notifications.utils import send_email_from_template
from laboratory.models import BlockedListNotification
from django.contrib.sites.models import Site


def send_email_limit_objs(lab, shelfobjects, enqueued=True):
    allowed_emails = []
    if len(shelfobjects)>0:
        for shelfobject in shelfobjects:
            blocked = BlockedListNotification.objects.filter(
                laboratory=lab, object=shelfobject.object)
            blocked_emails = [x for x in blocked.values_list('user__email', flat=True)]
            ptech = Profile.objects.filter(laboratories__in=[lab])
            emails = [x for x in ptech.values_list('user__email', flat=True)]
            allowed_emails.extend([x for x in emails if x not in blocked_emails])

        emails = list(set(allowed_emails))
        context = {
            'laboratory': lab,
            'shelf_object': shelfobjects,
        }
        schema = 'https'
        if settings.DEBUG:
                schema = 'http'


        url = f"/lab/{lab.pk}/blocknotifications/"
        domain = Site.objects.get_current().domain
        context['blockurl'] = f"{schema}://{domain}{url}"
        context['domain'] = domain
        send_email_from_template("Shelf object in limit",
                                     emails,
                                     context=context,
                                     enqueued=enqueued,
                                     user=None,
                                     upfile=None)