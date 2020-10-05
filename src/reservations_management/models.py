from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from laboratory.models import ShelfObject
import uuid


PROCESSING = 0
REQUESTED = 1
ACCEPTED = 2
DENIED = 3
CLOSED = 4
STATUS = (
    (PROCESSING, _("Processing")),
    (REQUESTED, _("Requested")),
    (ACCEPTED, _("Accepted")),
    (DENIED, _("Denied")),
    (CLOSED, _("Closed")),
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
    status = models.SmallIntegerField(choices=STATUS, default=REQUESTED)
    comments = models.CharField(max_length=500)


class MassiveReservations(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.SmallIntegerField(choices=STATUS, default=REQUESTED)
    comments = models.CharField(max_length=500)
    days = models.SmallIntegerField(choices=DAYS)


class ReservedProducts(models.Model):
    shelf_object_id = models.ForeignKey(ShelfObject, on_delete=models.CASCADE)
    # Using generic relation to be able to connect to both the reservations and the MassiveReservations model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    is_returnable = models.BooleanField(default=True)
    amount_required = models.FloatField()
    initial_date = models.DateTimeField()
    final_date = models.DateTimeField()
    was_returned = models.BooleanField(default=True)


class ReservationTasks(models.Model):
    reserved_product = models.ForeignKey(ReservedProducts, on_delete=models.CASCADE)
    celery_task_id = models.UUIDField(default=uuid.uuid4, editable=False)
