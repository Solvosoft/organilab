from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from laboratory.models import ShelfObject,Laboratory
import uuid


REQUESTED = 0
ACCEPTED = 1
DENIED = 2
CLOSED = 3
SELECTED = 4
STATUS = (
    (REQUESTED, _("Requested")),
    (ACCEPTED, _("Accepted")),
    (DENIED, _("Denied")),
    (CLOSED, _("Closed")),
    (SELECTED, _("Selected")),
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


class Reservations(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    laboratory = models.ForeignKey(Laboratory,on_delete=models.CASCADE)
    status = models.SmallIntegerField(choices=STATUS, default=REQUESTED)
    comments = models.CharField(max_length=500, null=True)
    is_massive = models.BooleanField(default=False)

    class Meta:
        ordering = ['status']


class ReservedProducts(models.Model):
    shelf_object = models.ForeignKey(ShelfObject, on_delete=models.CASCADE)
    reservation = models.ForeignKey(Reservations, on_delete=models.CASCADE)
    is_returnable = models.BooleanField(default=True)
    amount_required = models.FloatField()
    initial_date = models.DateTimeField()
    final_date = models.DateTimeField()
    was_returned = models.BooleanField(default=True)
    status = models.SmallIntegerField(choices=STATUS)


class ReservationTasks(models.Model):
    reserved_product = models.ForeignKey(ReservedProducts, on_delete=models.CASCADE)
    celery_task = models.UUIDField(default=uuid.uuid4, editable=False)


class ReservationRange(models.Model):
    day = models.SmallIntegerField(choices=DAYS)
    reserved_product = models.ForeignKey(ReservedProducts, on_delete=models.CASCADE)
