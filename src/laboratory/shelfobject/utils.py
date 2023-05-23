from django.contrib.admin.models import CHANGE
from laboratory.logsustances import log_object_add_change
from laboratory.utils import organilab_logentry


def save_shelf_object(shelfobject, user, amount, provider, bill, changed_data, laboratory):
    old = shelfobject.quantity
    new = old + amount
    shelfobject.quantity = new
    shelfobject.save()
    log_object_add_change(user, laboratory.pk, shelfobject, old, new, "Add", provider, bill, create=False)
    organilab_logentry(user, shelfobject, CHANGE, 'shelfobject', changed_data=changed_data, relobj=[laboratory, shelfobject])