from django.contrib.admin.models import CHANGE
from laboratory.logsustances import log_object_add_change, log_object_change
from laboratory.models import ShelfObjectObservation
from laboratory.utils import organilab_logentry
from django.utils.translation import gettext_lazy as _


def save_increase_decrease_shelf_object(user, validated_data, laboratory, is_increase_process=False):
    provider = None
    if 'provider' in validated_data:
        provider = validated_data['provider']

    bill = validated_data.get('bill', '')
    description = validated_data.get('description', '')
    shelfobject = validated_data['shelf_object']
    amount = validated_data['amount']

    old = shelfobject.quantity
    new = old - amount
    action_taken = _("Object was decreased")

    if is_increase_process:
        new = old + amount
        action_taken = _("Object was increased")
        log_object_add_change(user, laboratory.pk, shelfobject, old, new, "Add", provider, bill, create=False)

    else:
        log_object_change(user, laboratory.pk, shelfobject, old, new, description, 2, "Substract", create=False)

    shelfobject.quantity = new
    shelfobject.save()

    changed_data = list(validated_data.keys())
    organilab_logentry(user, shelfobject, CHANGE, 'shelfobject', changed_data=changed_data,relobj=[laboratory, shelfobject])

    if not description:
        description = _("Current available objects: %(amount)d") % {'amount': new}
    ShelfObjectObservation.objects.create(action_taken=action_taken, description=description, shelf_object=shelfobject, creator=user)