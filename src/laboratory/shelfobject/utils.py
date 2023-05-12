from django.contrib.admin.models import CHANGE
from django.shortcuts import get_object_or_404
from rest_framework import status

from laboratory.logsustances import log_object_add_change
from laboratory.models import ShelfObject, Provider
from laboratory.utils import organilab_logentry


def save_shelf_object(shelfobject, user, shelf_object, amount, provider, bill, changed_data):
    old = shelfobject.quantity
    new = old + amount
    shelfobject.quantity = new
    shelfobject.save()
    log_object_add_change(user, shelf_object, shelfobject, old, new, "Add", provider, bill, create=False)
    organilab_logentry(user, shelfobject, CHANGE, 'shelfobject', changed_data=changed_data)
    return status.HTTP_201_CREATED

def get_clean_shelfobject_data(serializer, changed_data, lab_pk):
    provider = None
    bill = serializer.data.get('bill', '')
    amount = serializer.data['amount']
    shelfobject = get_object_or_404(ShelfObject, pk=serializer.data['shelf_object'])

    if bill:
        changed_data.append("bill")

    provider_obj = Provider.objects.filter(laboratory=lab_pk, pk=serializer.data['provider'])
    if provider_obj.exists():
        provider = provider_obj.first()
        changed_data.append("provider")

    return bill, amount, shelfobject, provider


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