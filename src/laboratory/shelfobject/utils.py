from django.contrib.admin.models import CHANGE, ADDITION, DELETION
from laboratory.logsustances import log_object_add_change, log_object_change
from laboratory.models import ShelfObjectObservation, ShelfObject, Object
from laboratory.utils import organilab_logentry, get_pk_org_ancestors
from django.utils.translation import gettext_lazy as _
from laboratory.qr_utils import get_or_create_qr_shelf_object


def save_increase_decrease_shelf_object(user, validated_data, laboratory, organization, is_increase_process=False):
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
        log_object_add_change(user, laboratory.pk, shelfobject, old, new, "Add", provider, bill, create=False, organization=organization)

    else:
        log_object_change(user, laboratory.pk, shelfobject, old, new, description, 2, "Substract", create=False, organization=organization)

    shelfobject.quantity = new
    shelfobject.save()

    changed_data = list(validated_data.keys())
    organilab_logentry(user, shelfobject, CHANGE, 'shelfobject', changed_data=changed_data,relobj=[laboratory, shelfobject, organization])

    if not description:
        description = _("Current available objects: %(amount)d") % {'amount': new}
    ShelfObjectObservation.objects.create(action_taken=action_taken, description=description, shelf_object=shelfobject, created_by=user)

def build_shelfobject_qr(request, shelfobject, organization, laboratory):
    qr, url = get_or_create_qr_shelf_object(request, shelfobject, organization, laboratory)
    shelfobject.shelf_object_url = url
    shelfobject.save()
    return qr

def save_shelfobject_limits_from_serializer(limits_serializer, user):
    limits = limits_serializer.save()
    organilab_logentry(user, limits, ADDITION, changed_data=['minimum_limit', 'maximum_limit', 'expiration_date'])
    return limits

def create_shelfobject_observation(shelfobject, description, action_taken, user, laboratory):
    observation = ShelfObjectObservation.objects.create(description=description, action_taken=action_taken, shelf_object=shelfobject, created_by=user)
    organilab_logentry(user, observation, ADDITION, 'shelfobjectobservation', relobj=laboratory)
    return observation

def clone_shelfobject_limits(shelfobject, user):
    new_limits = None  # return None if the shelfobject doesn't have limits setup
    if shelfobject.limits:
        new_limits = shelfobject.limits
        new_limits.pk = None
        new_limits._state.adding = True
        new_limits.save()
        organilab_logentry(user, new_limits, ADDITION, changed_data=['minimum_limit', 'maximum_limit', 'expiration_date'])
    return new_limits

def get_available_containers_for_selection(laboratory_id):
    # all containers that belong to a laboratory that are not in use
    containers = ShelfObject.objects.filter(
        in_where_laboratory_id=laboratory_id,
        object__type=Object.MATERIAL,
        containershelfobject=None  # it's not used as container - query the reverse relationship
    )
    return containers

def get_containers_for_cloning(organization_id):
     # any object of type material that belongs to the organization (and its ancestors) can be a container
    organizations = get_pk_org_ancestors(organization_id)
    containers = Object.objects.filter(
        organization__in=organizations,
        type=Object.MATERIAL
    )
    return containers

def move_shelfobject_partial_quantity_to(shelfobject, destination_organization_id, destination_laboratory_id, destination_shelf, request, quantity):
    # it will create a new shelfobject in the destination shelf and laboratory with provided quantity and decrease the quantity on the original shelfobject

    original_shelfobject = ShelfObject.objects.get(pk=shelfobject.pk)
    new_limits = clone_shelfobject_limits(original_shelfobject, request.user)

    shelfobject.pk = None  # to save the container with some changes into a new one (clone it)
    shelfobject.shelf = destination_shelf
    shelfobject.in_where_laboratory_id = destination_laboratory_id
    shelfobject.limits = new_limits
    shelfobject.created_by = request.user
    shelfobject.quantity = quantity
    shelfobject.shelf_object_qr = None
    shelfobject.shelf_object_url = None
    shelfobject._state.adding = True
    shelfobject.save()
    build_shelfobject_qr(request, shelfobject, destination_organization_id, destination_laboratory_id)

    log_object_change(request.user, destination_laboratory_id, shelfobject, 0, shelfobject.quantity, '', ADDITION, "Create", create=True, organization=destination_organization_id)
    organilab_logentry(request.user, shelfobject, ADDITION,
                       changed_data=['shelf', 'object', 'batch', 'status', 'quantity', 'limit_quantity', 'limits',
                                     'measurement_unit', 'in_where_laboratory', 'marked_as_discard', 'laboratory_name',
                                     'course_name', 'creator', 'shelf_object_url', 'shelf_object_qr'],
                       relobj=destination_laboratory_id)
    create_shelfobject_observation(shelfobject, shelfobject.course_name, _("Created Object"), request.user, destination_laboratory_id)

    update_shelfobject_quantity(original_shelfobject, original_shelfobject.quantity - quantity, request.user, organization=destination_organization_id)

    return shelfobject

def is_container_available(container):
    return container.containershelfobject == None  # True it is available, False it is in use

def create_new_shelfobject_from_object(object, destination_laboratory):
    pass

def move_shelfobject_to(shelfobject, destination_laboratory):
    pass

def update_shelfobject_quantity(shelfobject, new_quantity, user, organization):
    if new_quantity > 0:
        old_quantity = shelfobject.quantity
        shelfobject.quantity = new_quantity
        shelfobject.save()

        log_object_change(user, shelfobject.in_where_laboratory.pk, shelfobject, old_quantity, new_quantity, '', CHANGE, "Change quantity", organization=organization)
        organilab_logentry(user, shelfobject, CHANGE, changed_data=['quantity'])
    else:  # delete those that will be left with quantity of 0 or less with the requested change
        log_object_change(user, shelfobject.in_where_laboratory.pk, shelfobject, shelfobject.quantity, 0, '', DELETION, "Delete ShelfObject with no quantity left", organization=organization)
        organilab_logentry(user, shelfobject, DELETION)

        shelfobject.delete()
