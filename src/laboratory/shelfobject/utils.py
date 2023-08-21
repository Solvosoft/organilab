from django.contrib.admin.models import CHANGE, ADDITION, DELETION
from django.shortcuts import get_object_or_404
from laboratory.logsustances import log_object_add_change, log_object_change
from laboratory.models import ShelfObjectObservation, ShelfObject, Object, Catalog, \
    Shelf
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

def get_containers_for_cloning(organization_id,shelf):
     # any object of type material that belongs to the organization (and its ancestors) can be a container
    organizations = get_pk_org_ancestors(organization_id)
    shelf = get_object_or_404(Shelf , pk=shelf)
    if shelf.limit_only_objects:
         containers = Object.objects.filter(
            organization__in=organizations,
            type=Object.MATERIAL,
            limit_objects=shelf
         )
    else:
         containers = Object.objects.filter(
            organization__in=organizations,
            type=Object.MATERIAL
         )

    return containers

def get_or_create_container_based_on_selected_option(container_selected_option, destination_organization_id, destination_laboratory_id, destination_shelf, request,
                                                     container_for_cloning=None, available_container=None, source_shelfobject=None):
    container = None
    if container_selected_option == 'clone':
        container = create_new_shelfobject_from_object_in(container_for_cloning, destination_organization_id, destination_laboratory_id,
                                                          destination_shelf, request)
    elif container_selected_option == 'available':
        # it will create a new container in the shelf with quantity of 1 and decrease the quantity by 1 on the original shelfobject
        container = move_shelfobject_partial_quantity_to(available_container, destination_organization_id, destination_laboratory_id,
                                                         destination_shelf, request, quantity=1)
    elif container_selected_option == 'use_source':
        container = move_shelfobject_to(source_shelfobject.container, destination_organization_id, destination_laboratory_id, destination_shelf,
                                        request, observation_text="Moved Container")
    elif container_selected_option == 'new_based_source':
        container = clone_shelfobject_to(source_shelfobject.container, destination_organization_id, destination_laboratory_id, destination_shelf, request)

    return container

def clone_shelfobject_to(shelfobject, destination_organization_id, destination_laboratory_id, destination_shelf, request, quantity=1):
    # clones a shelfobject and saves it in the provided organization, laboratory and shelf

    new_limits = clone_shelfobject_limits(shelfobject, request.user)

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

    log_object_change(request.user, destination_laboratory_id, shelfobject, 0, shelfobject.quantity, '', ADDITION, _("Create"), create=True)
    organilab_logentry(request.user, shelfobject, ADDITION,
                       changed_data=['shelf', 'object', 'batch', 'status', 'quantity', 'limit_quantity', 'limits',
                                     'measurement_unit', 'in_where_laboratory', 'marked_as_discard', 'laboratory_name',
                                     'course_name', 'created_by', 'shelf_object_url', 'shelf_object_qr'],
                       relobj=destination_laboratory_id)
    create_shelfobject_observation(shelfobject, shelfobject.course_name, _("Created Object"), request.user, destination_laboratory_id)

    return shelfobject

def move_shelfobject_partial_quantity_to(shelfobject, destination_organization_id, destination_laboratory_id, destination_shelf, request, quantity):
    # it will create a new shelfobject in the destination shelf and laboratory with provided quantity and decrease the quantity on the original shelfobject

    original_shelfobject = ShelfObject.objects.get(pk=shelfobject.pk)

    shelfobject = clone_shelfobject_to(shelfobject, destination_organization_id, destination_laboratory_id, destination_shelf, request, quantity)

    update_shelfobject_quantity(original_shelfobject, original_shelfobject.quantity - quantity, request.user, organization=destination_organization_id)

    return shelfobject

def create_new_shelfobject_from_object_in(object, destination_organization_id, destination_laboratory_id, destination_shelf, request, measurement_unit_description="Unidades"):
    measurement_unit = get_object_or_404(Catalog, key="units", description=measurement_unit_description)

    shelfobject = ShelfObject.objects.create(
        shelf=destination_shelf,
        object=object,
        quantity=1,
        measurement_unit=measurement_unit,
        in_where_laboratory_id=destination_laboratory_id,
        created_by=request.user
    )
    build_shelfobject_qr(request, shelfobject, destination_organization_id, destination_laboratory_id)

    log_object_change(request.user, destination_laboratory_id, shelfobject, 0, shelfobject.quantity, '', ADDITION, _("Create"), create=True)
    organilab_logentry(request.user, shelfobject, ADDITION,
                       changed_data=['shelf', 'object', 'quantity', 'measurement_unit', 'in_where_laboratory',
                                     'created_by', 'shelf_object_url', 'shelf_object_qr'],
                       relobj=destination_laboratory_id)
    create_shelfobject_observation(shelfobject, shelfobject.course_name, _("Created Object"), request.user, destination_laboratory_id)

    return shelfobject


def move_shelfobject_to(shelfobject, destination_organization_id, destination_laboratory_id, destination_shelf, request, observation_text="Moved Object"):
    log_object_change(request.user, shelfobject.in_where_laboratory.pk, shelfobject, shelfobject.quantity, 0, '', CHANGE, _("Move out"))

    shelfobject.shelf = destination_shelf
    shelfobject.in_where_laboratory_id = destination_laboratory_id
    shelfobject.created_by = request.user
    shelfobject.shelf_object_qr = None
    shelfobject.shelf_object_url = None
    shelfobject.save()
    build_shelfobject_qr(request, shelfobject, destination_organization_id, destination_laboratory_id)

    log_object_change(request.user, destination_laboratory_id, shelfobject, 0, shelfobject.quantity, '', CHANGE, _("Move in"))
    organilab_logentry(request.user, shelfobject, CHANGE,
                       changed_data=['shelf', 'in_where_laboratory', 'created_by', 'shelf_object_qr', 'shelf_object_url'],
                       relobj=destination_laboratory_id)
    create_shelfobject_observation(shelfobject, shelfobject.course_name, _(observation_text), request.user, destination_laboratory_id)

    return shelfobject


def update_shelfobject_quantity(shelfobject, new_quantity, user, organization):
    if new_quantity > 0:
        old_quantity = shelfobject.quantity
        shelfobject.quantity = new_quantity
        shelfobject.save()
        log_object_change(user, shelfobject.in_where_laboratory.pk, shelfobject, old_quantity, new_quantity, '', CHANGE, _("Change quantity"), organization=organization)
        organilab_logentry(user, shelfobject, CHANGE, changed_data=['quantity'])
    else:  # delete those that will be left with quantity of 0 or less with the requested change
        log_object_change(user, shelfobject.in_where_laboratory.pk, shelfobject, shelfobject.quantity, 0, '', DELETION, _("Delete ShelfObject with no quantity left"), organization=organization)
        organilab_logentry(user, shelfobject, DELETION)
        shelfobject.delete()
