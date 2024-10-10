import logging

from django.conf import settings
from django.contrib.admin.models import CHANGE, ADDITION, DELETION
from django.db.models import Q
from django.shortcuts import get_object_or_404
from laboratory.logsustances import log_object_add_change, log_object_change
from laboratory.models import ShelfObjectObservation, ShelfObject, Object, Catalog, \
    Shelf, BaseUnitValues
from laboratory.utils import organilab_logentry, get_pk_org_ancestors, \
    save_object_by_action
from django.utils.translation import gettext_lazy as _
from laboratory.qr_utils import get_or_create_qr_shelf_object
from laboratory.utils_base_unit import get_conversion_units, \
    get_conversion_from_two_units

logger = logging.getLogger('organilab')


def save_increase_decrease_shelf_object(user, validated_data, laboratory, organization,
                                        is_increase_process=False):
    provider = None
    if 'provider' in validated_data:
        provider = validated_data['provider']

    measurement_unit = None
    if 'measurement_unit' in validated_data:
        measurement_unit = validated_data['measurement_unit']

    bill = validated_data.get('bill', '')
    description = validated_data.get('description', '')
    shelfobject = validated_data['shelf_object']
    amount = validated_data['amount']

    old = shelfobject.quantity
    converted_amount = get_conversion_from_two_units(
            measurement_unit,
            shelfobject.shelf.measurement_unit, amount)

    if shelfobject.shelf.measurement_unit == None:
        converted_amount = get_conversion_from_two_units(
            measurement_unit,
            shelfobject.measurement_unit, amount)

    new = old - converted_amount
    action_taken = _("Object was decreased")

    if is_increase_process:

        new = old + converted_amount
        action_taken = _("Object was increased")
        log_object_add_change(user, laboratory.pk, shelfobject, old, new, "Add",
                              provider, bill, create=False, organization=organization)

    else:
        log_object_change(user, laboratory.pk, shelfobject, old, new, description, 2,
                          "Substract", create=False, organization=organization)

    shelfobject.quantity = new

    changed_data = list(validated_data.keys())
    save_object_by_action(user, shelfobject, [laboratory, shelfobject, organization],
                          changed_data, CHANGE, 'shelfobject')

    if not description:
        description = _("Current available objects: %(amount)d") % {'amount': new}
    ShelfObjectObservation.objects.create(action_taken=action_taken,
                                          description=description,
                                          shelf_object=shelfobject, created_by=user)


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

def get_available_containers_for_selection(laboratory_id, shelf_id):
    # all containers that belong to a laboratory that are not in use.  If shelf is limited it only returns those allowed.
    shelf = get_object_or_404(Shelf.objects.using(settings.READONLY_DATABASE), pk=shelf_id)

    filters = {'in_where_laboratory_id': laboratory_id, 'object__type': Object.MATERIAL,
                'containershelfobject': None, 'object__is_container': True}
    if shelf.limit_only_objects:
        filters['object__pk__in'] = shelf.available_objects_when_limit.values_list('pk')

    containers = ShelfObject.objects.filter(**filters)
    return containers

def get_containers_for_cloning(organization_id, shelf_id):
     # any object of type material that belongs to the organization (and its ancestors) can be a container.  If shelf is limited it only returns those allowed.
    organizations = get_pk_org_ancestors(organization_id)
    shelf = get_object_or_404(Shelf.objects.using(settings.READONLY_DATABASE), pk=shelf_id)

    filters = {'organization__in': organizations, 'type': Object.MATERIAL,
               'is_container': True}
    if shelf.limit_only_objects:
        filters['limit_objects'] = shelf

    containers = Object.objects.filter(**filters)
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
                                     'description', 'created_by', 'shelf_object_url', 'shelf_object_qr'],
                       relobj=destination_laboratory_id)
    create_shelfobject_observation(shelfobject, shelfobject.description, _("Created Object"), request.user, destination_laboratory_id)

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
    create_shelfobject_observation(shelfobject, shelfobject.description, _("Created Object"), request.user, destination_laboratory_id)

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
    create_shelfobject_observation(shelfobject, shelfobject.description, _(observation_text), request.user, destination_laboratory_id)

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



def get_available_objs_by_shelfobject(queryset, shelfobject, key, filters):
    obj_pk = []
    lab_info = queryset.filter(**filters).values(key, 'pk').distinct()

    for lab in lab_info:
        if lab[key] != shelfobject.shelf.pk:
            shelf = Shelf.objects.get(pk=lab[key])
            items_object_shelf = shelf.get_total_refuse(
                include_containers=False, measurement_unit=shelf.measurement_unit)
            items_with_shelfobject = items_object_shelf + shelfobject.quantity

            if items_with_shelfobject <= shelf.quantity:
                obj_pk.append(lab['pk'])
    return obj_pk


def get_lab_room_queryset_by_filters(queryset, shelfobject, key, filters):
    available_labrooms = get_available_objs_by_shelfobject(queryset, shelfobject, key,
                                                           filters)
    filters_lab_room = Q(furniture__shelf__measurement_unit__isnull=True,
                furniture__shelf__infinity_quantity=True) | \
              Q(furniture__shelf__measurement_unit=shelfobject.measurement_unit,
                furniture__shelf__infinity_quantity=True) | \
              Q(pk__in=available_labrooms)
    return queryset.filter(filters_lab_room).distinct()


def get_furniture_queryset_by_filters(queryset, shelfobject, key, filters):
    available_furnitures = get_available_objs_by_shelfobject(queryset,
                                                             shelfobject,
                                                             key, filters)
    filters_furniture = Q(shelf__measurement_unit__isnull=True,
                shelf__infinity_quantity=True) | \
              Q(shelf__measurement_unit=shelfobject.measurement_unit,
                shelf__infinity_quantity=True) | \
              Q(pk__in=available_furnitures)

    return queryset.filter(filters_furniture).distinct()


def get_shelf_queryset_by_filters(queryset, shelfobject, key, filters):
    available_shelves = get_available_objs_by_shelfobject(queryset,
                                                             shelfobject,
                                                             key, filters)
    filters_shelves = Q(measurement_unit__isnull=True, infinity_quantity=True) | \
              Q(measurement_unit=shelfobject.measurement_unit,
                infinity_quantity=True) | \
              Q(pk__in=available_shelves)

    return queryset.filter(filters_shelves).exclude(pk=shelfobject.shelf.pk).distinct()


def limit_objects_by_shelf(shelf, object):
    error_msg = ""

    if shelf.limit_only_objects:
        if not shelf.available_objects_when_limit.filter(pk=object.pk).exists():
            logger.debug(
                f'limit_objects_by_shelf --> shelf.limit_only_objects and not '
                f'shelf.available_objects_when_limit.filter(pk=object.pk ({object.pk})).exists()')
            error_msg = _("Object is not allowed in the shelf.")

    return error_msg


def validate_measurement_unit_and_quantity(shelf, object, quantity, measurement_unit=None, container=None):
    errors = {}

    total = shelf.get_total_refuse(include_containers=False, measurement_unit=shelf.measurement_unit) + quantity

    shelfbaseunit = BaseUnitValues.objects.filter(measurement_unit=shelf.measurement_unit).first()
    baseunit = BaseUnitValues.objects.filter(measurement_unit=measurement_unit).first()

    if shelfbaseunit == None:
        shelfbaseunit = baseunit

    if (baseunit.measurement_unit_base and shelfbaseunit.measurement_unit_base and
        baseunit.measurement_unit_base != shelfbaseunit.measurement_unit_base):
        # if measurement unit is not provided (None) then this validation is not applied, for material and equipment it is not required
        logger.debug(
            f'validate_measurement_unit_and_quantity --> shelf.measurement_unit and measurement_unit '
            f'and measurement_unit ({measurement_unit}) != shelf.measurement_unit ({measurement_unit})')
        errors.update({'measurement_unit': _(
            "Measurement unit cannot be different than the shelf's measurement unit.")})
    if total > shelf.quantity and not shelf.infinity_quantity:
        logger.debug(
            f'validate_measurement_unit_and_quantity --> total ({total}) > shelf.quantity ({shelf.quantity}) and not shelf.infinity_quantity')
        errors.update({'quantity': _(
            "Resulting quantity cannot be greater than the shelf's quantity limit: %(limit)s.") % {
                                       'limit': shelf.quantity,
                                   }})

    limit_object_error = limit_objects_by_shelf(shelf, object)
    if limit_object_error:
        errors.update({'object': limit_object_error})

    if quantity <= 0:
        logger.debug('validate_measurement_unit_and_quantity --> quantity <= 0')
        errors.update({'quantity': _("Quantity cannot be less or equal to zero.")})

    if container:
        if not hasattr(container,'object'):
            if hasattr(container,'materialcapacity'):
                material_capacity = container.materialcapacity
            else:
                return errors
        elif hasattr(container.object, 'materialcapacity'):
            material_capacity = container.object.materialcapacity
        else:
            return errors

        container_capacity = material_capacity.capacity
        container_unit = material_capacity.capacity_measurement_unit
        if container_capacity < quantity:
            logger.debug(
                f'validate --> total ({container_capacity}) < quantity ({quantity})')
            errors.update({'quantity': _(
                "Quantity cannot be greater than the container capacity limit: %(capacity)s.") % {
                                               'capacity': container_capacity,
                                           }})

        if container_unit != measurement_unit:
            logger.debug(
                f'validate --> total ({container_unit}) < quantity ({measurement_unit})')
            errors.update({'measurement_unit': _(
                "Measurement unit cannot be different than the container object measurement unit: %(unit)s.") % {
                'unit': container_unit}})

    return errors


def get_selected_container(data):
    container = None
    container_select_option = data.get('container_select_option')
    if container_select_option == 'available':
        container = data.get('available_container')
    elif container_select_option == 'clone':
        container = data["container_for_cloning"]
    return container


def group_object_errors_for_serializer(errors, save_to_key="shelf_object", keys_to_group=('quantity', 'object', 'measurement_unit')):
    object_errors = []
    updated_errors = {}
    for key, error in errors.items():
        if key in keys_to_group:
            object_errors.append(error)
        else:  # any other error goes in its own key
            updated_errors[key] = error

        if object_errors:
            updated_errors[save_to_key] = object_errors
    return updated_errors


def save_shelfobject_characteristics(characteristic, user):
    obj = characteristic.save()
    changed_data= ['authorized_roles_to_use_equipment', 'equipment_price',
                       'purchase_equipment_date', 'delivery_equipment_date',
                       'have_guarantee', 'contract_of_maintenance', 'available_to_use',
                       'first_date_use', 'notes', 'provider'
                       ]
    organilab_logentry(user, obj, ADDITION, changed_data=changed_data)

def delete_shelfobjects(shelfobject, user, laboratory):
    organilab_logentry(user, shelfobject, DELETION, relobj=laboratory)
    shelfobject.delete()
