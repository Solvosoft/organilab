from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from laboratory.models import ShelfObject, Laboratory
import uuid

from presentation.models import AbstractOrganizationRef

REQUESTED = 0
ACCEPTED = 1
BORROWED = 1
DENIED = 2
CLOSED = 3
SELECTED = 3
RETURNED = 4

RESERVATION_STATUS = (
    (REQUESTED, _("Requested")),
    (ACCEPTED, _("Accepted")),
    (DENIED, _("Denied")),
    (CLOSED, _("Closed")),
)

PRODUCT_STATUS = (
    (REQUESTED, _("Requested")),
    (BORROWED, _("Borrowed")),
    (DENIED, _("Denied")),
    (SELECTED, _("Selected")),
    (RETURNED, _("Returned")),
)

L = 0
K = 1
M = 2
J = 3
V = 4
S = 5
D = 6
DAYS = (
    (L, _("Monday")),
    (K, _("Tuesday")),
    (M, _("Wednesday")),
    (J, _("Thursday")),
    (V, _("Friday")),
    (S, _("Saturday")),
    (D, _("Sunday")),
)


class Reservations(AbstractOrganizationRef):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservation_user', verbose_name=_('User'))
    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE, verbose_name=_('Laboratory'))
    status = models.SmallIntegerField(choices=RESERVATION_STATUS, default=REQUESTED, verbose_name=_('Status'))
    comments = models.CharField(max_length=500, null=True, blank=True, verbose_name=_('Comments'))
    is_massive = models.BooleanField(default=False, verbose_name=_('Is massive'))

    class Meta:
        ordering = ['status']


class ReservedProducts(AbstractOrganizationRef):
    shelf_object = models.ForeignKey(ShelfObject, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='reserved_user', verbose_name=_('User'))
    reservation = models.ForeignKey(Reservations, on_delete=models.CASCADE, null=True, verbose_name=_('Reservation'))
    is_returnable = models.BooleanField(default=True, verbose_name=_('Is Returnable'))
    amount_required = models.FloatField(verbose_name=_('Amount Required'))
    amount_returned = models.FloatField(default=0, verbose_name=_('Amount Returned'))
    initial_date = models.DateTimeField(verbose_name=_('Initial Date'))
    final_date = models.DateTimeField(verbose_name=_('Final Date'))
    status = models.SmallIntegerField(choices=PRODUCT_STATUS, default=SELECTED, verbose_name=_('Status'))


class ReservationTasks(models.Model):
    reserved_product = models.ForeignKey(ReservedProducts, on_delete=models.CASCADE)
    celery_task = models.UUIDField(default=uuid.uuid4, editable=False)
    task_type = models.CharField(max_length=20)



class ReservationRange(models.Model):
    day = models.SmallIntegerField(choices=DAYS)
    reserved_product = models.ForeignKey(ReservedProducts, on_delete=models.CASCADE)
