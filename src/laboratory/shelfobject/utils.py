from django.conf import settings
from django.contrib.admin.models import CHANGE
from laboratory.logsustances import log_object_add_change
from laboratory.utils import organilab_logentry


def save_shelf_object(shelfobject, user, shelf_object, amount, provider, bill, changed_data, laboratory):
    old = shelfobject.quantity
    new = old + amount
    shelfobject.quantity = new
    shelfobject.save()
    log_object_add_change(user, laboratory.pk, shelfobject, old, new, "Add", provider, bill, create=False)
    organilab_logentry(user, shelfobject, CHANGE, 'shelfobject', changed_data=changed_data, relobj=[laboratory, shelfobject])


def status_shelfobject(shelfobject, shelf, amount):
    status_shelf_obj = False
    if shelf.measurement_unit == None:
        status_shelf_obj = True
    if shelf.measurement_unit == shelfobject.measurement_unit:
        quantity = (amount + shelf.get_total_refuse()) <= shelf.quantity
        if quantity:
            status_shelf_obj = True
    if shelf.quantity == settings.DEFAULT_SHELF_ULIMIT:
        status_shelf_obj = True
    return status_shelf_obj