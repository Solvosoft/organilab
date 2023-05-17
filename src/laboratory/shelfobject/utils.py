from django.contrib.admin.models import CHANGE
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from rest_framework import status
from dateutil.parser import parse
from laboratory.logsustances import log_object_add_change
from laboratory.models import ShelfObject, Provider
from laboratory.utils import organilab_logentry
from django.utils.translation import gettext_lazy as _

from organilab.settings import DATETIME_INPUT_FORMATS


def save_shelf_object(shelfobject, user, shelf_object, amount, provider, bill, changed_data):
    old = shelfobject.quantity
    new = old + amount
    shelfobject.quantity = new
    shelfobject.save()
    log_object_add_change(user, shelf_object, shelfobject, old, new, "Add", provider, bill, create=False)
    organilab_logentry(user, shelfobject, CHANGE, 'shelfobject', changed_data=changed_data)


def status_shelfobject(shelfobject, shelf, amount):
    status_shelf_obj = False
    if shelf.measurement_unit == None:
        status_shelf_obj = True
    if shelf.measurement_unit == shelfobject.measurement_unit:
        quantity = (amount + shelf.get_total_refuse()) <= shelf.quantity
        if quantity:
            status_shelf_obj = True
    if shelf.measurement_unit == shelfobject.measurement_unit and shelf.quantity == 0:
        status_shelf_obj = True
    return status_shelf_obj


def validate_reservation_dates(initial_date, final_date):
    result = False
    errors_date = {}
    if initial_date != final_date:
        if initial_date < final_date:
            if initial_date != now().date():
                if initial_date > now().date():
                    result = True
                else:
                    errors_date.update({'initial_date': [_("Initial date can't be lower than current date")]})
            else:
                errors_date.update({'initial_date': [_("Initial date can't be equal to current date")]})
        else:
            errors_date.update({'initial_date': [_("Initial date can't be greater than final date")]})
    else:
        errors_date.update({'final_date': [_("Final date can't be equal to initial date")]})
    return result, errors_date