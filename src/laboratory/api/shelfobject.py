from django.conf import settings
from django.contrib.admin.models import CHANGE, ADDITION, DELETION
from django.http import JsonResponse, Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from djgentelella.objectmanagement import AuthAllPermBaseObjectManagement
from rest_framework import status
from rest_framework import viewsets, mixins
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auth_and_perms.organization_utils import user_is_allowed_on_organization, \
    organization_can_change_laboratory
from laboratory import utils
from laboratory.api import serializers
from laboratory.api.serializers import ShelfLabViewSerializer, \
    CreateObservationShelfObjectSerializer
from laboratory.logsustances import log_object_change
from laboratory.models import Catalog, ShelfObjectObservation, Object, Furniture, Shelf, \
    ShelfObjectMaintenance, ShelfObjectLog, ShelfObjectCalibrate, ShelfObjectGuarantee, \
    ShelfObjectTraining
from laboratory.models import OrganizationStructure, ShelfObject, Laboratory, \
    TranferObject
from laboratory.models import REQUESTED, ACCEPTED
from laboratory.qr_utils import get_or_create_qr_shelf_object
from laboratory.shelfobject import serializers as shelfobject_serializers

from laboratory.shelfobject.serializers import IncreaseShelfObjectSerializer, \
    DecreaseShelfObjectSerializer, \
    ReserveShelfObjectSerializer, UpdateShelfObjectStatusSerializer, \
    ShelfObjectObservationDataTableSerializer, \
    MoveShelfObjectSerializer, ShelfObjectDetailSerializer, ShelfSerializer, \
    TransferInShelfObjectSerializer, \
    ShelfObjectLimitsSerializer, ShelfObjectStatusSerializer, \
    ShelfObjectDeleteSerializer, \
    TransferOutShelfObjectSerializer, TransferObjectDataTableSerializer, \
    TransferInShelfObjectApproveWithContainerSerializer, ShelfObjectPk, \
    SearchShelfObjectSerializerMany, MoveShelfObjectWithContainerSerializer, \
    ManageContainerSerializer, ValidateShelfInformationPositionSerializer, \
    EquimentShelfobjectCharacteristicSerializer, \
    MaintenanceSerializer, MaintenanceDatatableSerializer, \
    UpdateMaintenanceSerializer, CreateMaintenanceSerializer, \
    ShelfObjectLogDatatableSerializer, ValidateShelfObjectLogSerializer, \
    ShelfObjectLogSerializer, ValidateShelfObjectCalibrateSerializer, \
    ShelfObjectCalibrateSerializer, ShelfObjectCalibrateDatatableSerializer, \
    UpdateShelfObjectCalibrateSerializer, ShelfObjectGuaranteeDatatableSerializer, \
    ShelfObjectGuaranteeSerializer, ValidateShelfObjectTrainingSerializer, \
    ShelfObjectTrainingeDatatableSerializer, ShelfObjectTrainingSerializer, \
    ShelfObjectLogtFilter, ShelfObjectCalibrateFilter, ShelfObjectTrainingFilter, \
    ShelfObjectMaintenanceFilter, ValidateShelfObjectGuaranteeSerializer, \
    ShelfObjectGuarenteeFilter, ValidateShelfobjectEditSerializer, \
    EditEquipmentShelfObjectSerializer, EditEquimentShelfobjectCharacteristicSerializer

from laboratory.shelfobject.utils import save_increase_decrease_shelf_object, \
    move_shelfobject_partial_quantity_to, build_shelfobject_qr, \
    save_shelfobject_limits_from_serializer, \
    create_shelfobject_observation, get_or_create_container_based_on_selected_option, \
    move_shelfobject_to, create_new_shelfobject_from_object_in, clone_shelfobject_to, \
    save_shelfobject_characteristics, delete_shelfobjects

from laboratory.utils import save_object_by_action,PermissionByLaboratoryInOrganization


class ShelfObjectTableViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    This API allows laboratory room table view.
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ShelfObjectTableSerializer
    queryset = ShelfObject.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['object__name', 'object__type', 'quantity',
                     'measurement_unit__description',
                     'container__object__name']  # for the global search
    ordering_fields = ['object__name', 'object__type', 'quantity',
                       'measurement_unit__description', 'container__object__name']
    ordering = ('-last_update',)  # default order

    def get_queryset(self):
        if not self.data['shelf']:
            return self.queryset.none()
        return self.queryset.filter(
            in_where_laboratory=self.laboratory,
            shelf=self.data['shelf'],
            containershelfobject=None
            # if it's not used as container - query the reverse relationship
        )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        serializer_so = ShelfObjectPk(data=self.request.GET)

        if not queryset and serializer_so.is_valid():
            queryset = self.get_queryset()
            queryset = queryset.filter(
                pk=serializer_so.validated_data['search'].split('=')[1])
        return queryset

    def list(self, request, org_pk, lab_pk, **kwargs):
        self.organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
        self.laboratory = get_object_or_404(
            Laboratory.objects.using(settings.READONLY_DATABASE), pk=lab_pk)
        user_is_allowed_on_organization(request.user, self.organization)
        organization_can_change_laboratory(self.laboratory, self.organization,
                                           raise_exec=True)
        validate_serializer = ShelfLabViewSerializer(data=request.GET,
                                                     laboratory=self.laboratory)
        validate_serializer.is_valid(raise_exception=True)
        self.data = validate_serializer.data

        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {'data': data, 'recordsTotal': ShelfObject.objects.count(),
                    'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}
        return Response(self.get_serializer(response).data)


class ShelfObjectCreateMethods:

    def __init__(self, context={}):
        self.context = context

    def create_reactive(self, serializer, limits_serializer):
        """
        Create reactive type Shelfobject.
        The container is moved to the right shelf (created one with quantity 1 and decrease quantity on the original -or delete it if quantity is 0 after-).

        :param serializer:  ShelfObjectSerializer to create reactive type shelfobject
        :param limits_serializer: Serializer with the data to create ShelfObjectLimits
        :return: reactive type shelfobject was created
        """
        created_by = self.context['request'].user
        laboratory_id = self.context['laboratory_id']
        organization_id = self.context['organization_id']
        request = self.context['request']
        limits = save_shelfobject_limits_from_serializer(limits_serializer, created_by)

        container_select_option = serializer.validated_data.pop('container_select_option')
        container_for_cloning = serializer.validated_data.pop('container_for_cloning')
        available_container = serializer.validated_data.pop('available_container')
        container= get_or_create_container_based_on_selected_option(container_select_option,
                                                                         organization_id, laboratory_id,
                                                                         serializer.validated_data['shelf'],
                                                                         request,container_for_cloning,
                                                                        available_container)
        shelfobject = serializer.save(
            created_by=created_by,
            in_where_laboratory_id=laboratory_id,
            limits=limits,
            container = container
        )


        build_shelfobject_qr(self.context['request'], shelfobject, organization_id,
                             laboratory_id)

        log_object_change(created_by, laboratory_id, shelfobject, 0,
                          shelfobject.quantity, '', 0, "Create", create=True)
        utils.organilab_logentry(created_by, shelfobject, ADDITION,
                                 changed_data=['object', 'shelf', 'status', 'quantity',
                                               'measurement_unit', 'limit_quantity',
                                               'description',
                                               'marked_as_discard', 'batch',
                                               'container', 'created_by',
                                               'in_where_laboratory', 'limits'],
                                 relobj=laboratory_id)

        return {}, shelfobject

    def create_refuse_reactive(self, serializer, limits_serializer, equiment_serializer=None):
        """
        Create refuse reactive type Shelfobject.
        The container is moved to the right shelf (created one with quantity 1 and decrease quantity on the original -or delete it if quantity is 0 after-).

        :param serializer:  ShelfObjectSerializer to create reactive type shelfobject
        :param limits_serializer: Serializer with the data to create ShelfObjectLimits
        :return: Refuse reactive type shelfobject was created
        """
        created_by = self.context['request'].user
        laboratory_id = self.context['laboratory_id']
        organization_id = self.context['organization_id']
        request = self.context['request']
        limits = save_shelfobject_limits_from_serializer(limits_serializer, created_by)

        container_select_option=serializer.validated_data.pop('container_select_option')
        container_for_cloning= serializer.validated_data.pop('container_for_cloning')
        available_container = serializer.validated_data.pop('available_container')
        container= get_or_create_container_based_on_selected_option(container_select_option,
                                                                         organization_id, laboratory_id,
                                                                         serializer.validated_data['shelf'],
                                                                         request,container_for_cloning,
                                                                        available_container)
        shelfobject = serializer.save(
            created_by=created_by,
            in_where_laboratory_id=laboratory_id,
            limits=limits,
            container = container
        )


        build_shelfobject_qr(self.context['request'], shelfobject, organization_id,
                             laboratory_id)

        log_object_change(created_by, laboratory_id, shelfobject, 0,
                          shelfobject.quantity, '',
                          0, "Create", create=True, organization=organization_id)
        utils.organilab_logentry(created_by, shelfobject, ADDITION,
                                 changed_data=['object', 'shelf', 'status', 'quantity',
                                               'measurement_unit', 'marked_as_discard',
                                               'description', 'batch', 'container',
                                               'created_by', 'in_where_laboratory',
                                               'limits'],
                                 relobj=laboratory_id)

        return {}, shelfobject

    def create_material(self, serializer, limits_serializer):
        """
        Create material type Shelfobject .

        :param serializer:  ShelfObjectSerializer to create material type shelfobject
        :param limits_serializer: Serializer with the data to create ShelfObjectLimits
        :return: material type shelfobject was created
        """
        created_by = self.context['request'].user
        laboratory_id = self.context['laboratory_id']
        organization_id = self.context['organization_id']
        limits = save_shelfobject_limits_from_serializer(limits_serializer, created_by)
        measurement_unit = get_object_or_404(Catalog, key="units", description="Unidades")

        shelfobject = serializer.save(
            created_by=created_by,
            in_where_laboratory_id=laboratory_id,
            limits=limits,
            measurement_unit=measurement_unit
        )

        build_shelfobject_qr(self.context['request'], shelfobject, organization_id,
                             laboratory_id)

        log_object_change(created_by, laboratory_id, shelfobject, 0,
                          shelfobject.quantity, '',
                          0, "Create", create=True, organization=organization_id)
        utils.organilab_logentry(created_by, shelfobject, ADDITION,
                                 changed_data=['object', 'shelf', 'status', 'quantity',
                                               'limit_quantity', 'measurement_unit',
                                               'marked_as_discard', 'description',
                                               'created_by', 'in_where_laboratory',
                                               'limits'],
                                 relobj=laboratory_id)

        return {}, shelfobject

    def create_refuse_material(self, serializer, limits_serializer):
        """
        Create refuse material type Shelfobject .

        :param serializer:  ShelfObjectSerializer to create refuse material type shelfobject
        :param limits_serializer: Serializer with the data to create ShelfObjectLimits
        :return: refuse material type shelfobject was created
        """
        created_by = self.context['request'].user
        laboratory_id = self.context['laboratory_id']
        organization_id = self.context['organization_id']
        limits = save_shelfobject_limits_from_serializer(limits_serializer, created_by)
        measurement_unit = get_object_or_404(Catalog, key="units", description="Unidades")

        shelfobject = serializer.save(
            created_by=created_by,
            in_where_laboratory_id=laboratory_id,
            limits=limits,
            measurement_unit=measurement_unit
        )

        build_shelfobject_qr(self.context['request'], shelfobject, organization_id,
                             laboratory_id)

        log_object_change(created_by, laboratory_id, shelfobject, 0,
                          shelfobject.quantity, '',
                          0, "Create", create=True, organization=organization_id)
        utils.organilab_logentry(created_by, shelfobject, ADDITION,
                                 changed_data=['object', 'shelf', 'status', 'quantity',
                                               'limit_quantity', 'measurement_unit',
                                               'marked_as_discard', 'description',
                                               'created_by', 'in_where_laboratory',
                                               'limits'],
                                 relobj=laboratory_id)

        return {}, shelfobject

    def create_equipment(self, serializer, limits_serializer,equipment_serializer = None):
        """
        Create equipment type Shelfobject .

        :param serializer:  ShelfObjectSerializer to create equipment type shelfobject
        :param limits_serializer: Serializer with the data to create ShelfObjectLimits
        :return: equipment type shelfobject was created
        """
        created_by = self.context['request'].user
        laboratory_id = self.context['laboratory_id']
        organization_id = self.context['organization_id']
        measurement_unit = get_object_or_404(Catalog, key="units", description="Unidades")
        data = self.context["request"].data
        shelfobject = serializer.save(
            created_by=created_by,
            in_where_laboratory_id=laboratory_id,
            measurement_unit=measurement_unit
        )


        data.update({"shelfobject": shelfobject.pk, "organization": organization_id,
                     "created_by": created_by.pk})
        equipment_serializer = EquimentShelfobjectCharacteristicSerializer(data=data)

        if equipment_serializer.is_valid():
            save_shelfobject_characteristics(equipment_serializer, created_by)
        else:
            delete_shelfobjects(shelfobject, created_by, laboratory_id)
            return equipment_serializer.errors, None


        build_shelfobject_qr(self.context['request'], shelfobject, organization_id,
                             laboratory_id)

        log_object_change(created_by, laboratory_id, shelfobject, 0,
                          shelfobject.quantity, '',
                          0, "Create", create=True, organization=organization_id)
        utils.organilab_logentry(created_by, shelfobject, ADDITION,
                                 changed_data=['object', 'shelf', 'status', 'quantity',
                                               'limit_quantity', 'measurement_unit',
                                               'marked_as_discard', 'description',
                                               'created_by', 'in_where_laboratory'],
                                 relobj=laboratory_id)

        return {}, shelfobject

    def create_refuse_equipment(self, serializer, limits_serializer, equipment_serializer = None):
        """
        Create refuse equipment type Shelfobject .

        :param serializer:  ShelfObjectSerializer to create refuse equipment type shelfobject
        :param limits_serializer: Serializer with the data to create ShelfObjectLimits
        :return: refuse equipment type shelfobject was created
        """
        created_by = self.context['request'].user
        laboratory_id = self.context['laboratory_id']
        organization_id = self.context['organization_id']
        measurement_unit = get_object_or_404(Catalog, key="units", description="Unidades")

        shelfobject = serializer.save(
            created_by=created_by,
            in_where_laboratory_id=laboratory_id,
            measurement_unit=measurement_unit
        )
        data = self.context["request"].data
        data.update({"shelfobject": shelfobject.pk, "organization": organization_id,
                     "created_by": created_by.pk})
        equipment_serializer = EquimentShelfobjectCharacteristicSerializer(data=data)
        if equipment_serializer.is_valid():
            save_shelfobject_characteristics(equipment_serializer, created_by)
        else:
            delete_shelfobjects(shelfobject, created_by, laboratory_id)
            return equipment_serializer.errors, None


        build_shelfobject_qr(self.context['request'], shelfobject, organization_id,
                             laboratory_id)

        log_object_change(created_by, laboratory_id, shelfobject, 0,
                          shelfobject.quantity, '',
                          0, "Create", create=True, organization=organization_id)
        utils.organilab_logentry(created_by, shelfobject, ADDITION,
                                 changed_data=['object', 'shelf', 'status', 'quantity',
                                               'limit_quantity', 'measurement_unit',
                                               'marked_as_discard', 'description',
                                               'created_by', 'in_where_laboratory'],
                                 relobj=laboratory_id)

        return {}, shelfobject


class ShelfObjectViewSet(viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    permissions_by_endpoint = {
        "transfer_out": ["laboratory.add_tranferobject", "laboratory.view_shelfobject",
                         "laboratory.change_shelfobject"],
        "transfer_in_approve": ["laboratory.add_shelfobject",
                                "laboratory.change_shelfobject",
                                "laboratory.view_shelfobject",
                                "laboratory.change_tranferobject",
                                "laboratory.view_tranferobject"],
        "transfer_available_list": ["laboratory.view_tranferobject"],
        "transfer_in_deny": ["laboratory.view_tranferobject",
                             "laboratory.delete_tranferobject"],
        "create_shelfobject": ["laboratory.add_shelfobject"],
        "fill_increase_shelfobject": ["laboratory.change_shelfobject"],
        "fill_decrease_shelfobject": ["laboratory.change_shelfobject"],
        "reserve": ["reservations_management.add_reservedproducts"],
        "detail": ["laboratory.view_shelfobject"],
        "tag": [],
        "delete": ["laboratory.delete_shelfobject"],
        "chart_graphic": [],
        "create_comments": ["laboratory.add_shelfobjectobservation"],
        "list_comments": ["laboratory.view_shelfobjectobservation"],
        "create_status": ["laboratory.add_catalog"],
        "update_status": ["laboratory.change_shelfobject"],
        "move_shelfobject_to_shelf": ["laboratory.change_shelfobject"],
        "shelf_availability_information": ["laboratory.view_shelf"],
        "manage_shelfobject_container": ["laboratory.change_shelfobject"],
        "edit_shelfobject": ["laboratory.change_shelfobject"],
        "get_shelfobject": ["laboratory.viwe_shelfobject"],

    }

    # This is not an API endpoint
    def _check_permission_on_laboratory(self, request, org_pk, lab_pk, method_name):
        if request.user.has_perms(self.permissions_by_endpoint[
                                      method_name]):  # user can actually perform the requested action, then check object access permissions
            self.organization = get_object_or_404(
                OrganizationStructure.objects.using(settings.READONLY_DATABASE),
                pk=org_pk)
            self.laboratory = get_object_or_404(
                Laboratory.objects.using(settings.READONLY_DATABASE), pk=lab_pk)
            user_is_allowed_on_organization(request.user, self.organization)
            organization_can_change_laboratory(self.laboratory, self.organization,
                                               raise_exec=True)
        else:
            raise PermissionDenied()

    def _get_shelfobject_with_check(self, pk, laboratory_id):
        """
        Validates if the laboratory related to shelfobject is the same laboratory is working
        :param pk: Pk of the Shelfobject is creating o updating
        :param laboratory: laboratory was sended in the request
        :return: the shelfobject serializer and the create function
        """
        obj = get_object_or_404(ShelfObject.objects.using(settings.READONLY_DATABASE),
                                pk=pk)
        if obj.in_where_laboratory is None or obj.in_where_laboratory.pk != laboratory_id:
            raise Http404
        return obj

    def _get_create_shelfobject_serializer(self, request, org_pk, lab_pk):
        """
        Returns the shelfobject serializer and create function by the object type (Reactive, Material, Equipment) creating.
        :param request: http request
        :param org_pk: organization related user permissions
        :param lab_pk: laboratory related to shelfobject and user permissions
        :return: the shelfobject serializer and the create function
        """
        name = ""
        serializer = shelfobject_serializers.ValidateShelfSerializerCreate(
            data=request.data,
            context={"org_pk": org_pk, "lab_pk": lab_pk})
        serializer.is_valid(raise_exception=True)
        key_name = serializer.get_key_descriptor()
        methods_class = ShelfObjectCreateMethods(context={
            "organization_id": org_pk,
            "laboratory_id": lab_pk,
            "request": request
        })
        serializers_class = {
            "reactive": {
                'serializer': shelfobject_serializers.ReactiveShelfObjectSerializer,
                'method': methods_class.create_reactive},
            "reactive_refuse": {
                'serializer': shelfobject_serializers.ReactiveRefuseShelfObjectSerializer,
                'method': methods_class.create_refuse_reactive},
            "material": {
                'serializer': shelfobject_serializers.MaterialShelfObjectSerializer,
                'method': methods_class.create_material},
            "material_refuse": {
                'serializer': shelfobject_serializers.MaterialRefuseShelfObjectSerializer,
                'method': methods_class.create_refuse_material},
            "equipment": {
                'serializer': shelfobject_serializers.EquipmentShelfObjectSerializer,
                'method': methods_class.create_equipment},
            "equipment_refuse": {
                'serializer': shelfobject_serializers.EquipmentRefuseShelfObjectSerializer,
                'method': methods_class.create_refuse_equipment},
        }
        return serializers_class[key_name]

    @action(detail=False, methods=['post'])
    def create_shelfobject(self, request, org_pk, lab_pk, **kwargs):
        """
        This action allows the creates shelfobjects into the shelves, also user needs to have required access permission
        to do this action,futhermore the serializer validate that the quantity adding is less or equal than the shelfs
        quantity,the only moment permit a shelfobject quantity greater than shelf quantity is when the shelf is quantity
        unlimited, also the serializer validates shelfobject measurement unit need to be similar than shelf measurement
        unit, the only form to add a shelfobjects with different unit is when the shelf don't have measurement unit

        :param request: http request
        :param org_pk: organization related user permissions
        :param lab_pk: laboratory related to shelfobject and user permissions
        :param kwargs: extra params
        :return: increase shelf object quantity, return success o error message
        """
        object_type = request.data.get('objecttype',-1)
        self._check_permission_on_laboratory(request, org_pk, lab_pk,
                                             "create_shelfobject")
        self.serializer_class = self._get_create_shelfobject_serializer(request, org_pk,
                                                                        lab_pk)
        serializer = self.serializer_class['serializer'](data=request.data,
                                                         context={"organization_id": org_pk,
                                                                  "laboratory_id": lab_pk})
        limit_serializer = ShelfObjectLimitsSerializer(data=request.data, context={'type_id': object_type,
                                                                'quantity': request.data.get('quantity',0),
                                                                'without_limit':request.data.get('without_limit',False),
                                                                'object_type':object_type})

        errors = {}

        if serializer.is_valid():
            if limit_serializer.is_valid():
                error,shelfobject = self.serializer_class['method'](serializer,
                                                                  limit_serializer)
                if shelfobject:
                    create_shelfobject_observation(shelfobject, shelfobject.description,
                                                        _("Created Object"), request.user,
                                                           lab_pk)
                    return Response({"detail": _("The creation was performed successfully.")},status=status.HTTP_201_CREATED)
                else:
                    errors.update(error)
            else:
                errors.update(limit_serializer.errors)
        else:
            errors.update(serializer.errors)

        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def fill_increase_shelfobject(self, request, org_pk, lab_pk, **kwargs):
        """
        This action allows the shelf object increase by following data:
        required quantity and optional provider and bill validate through serializer,
        also user needs to have required access permission
        to do this action related to this specific organization and laboratory.

        :param request: http request
        :param org_pk: organization related user permissions
        :param lab_pk: laboratory related to shelf object and user permissions
        :param kwargs: extra params
        :return: increase shelf object quantity, return success o error message
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk,
                                             "fill_increase_shelfobject")
        self.serializer_class = IncreaseShelfObjectSerializer
        serializer = self.serializer_class(data=request.data, context={"source_laboratory_id": self.laboratory.pk})
        errors = {}

        if serializer.is_valid():
            save_increase_decrease_shelf_object(request.user, serializer.validated_data,
                                                self.laboratory,
                                                self.organization,
                                                is_increase_process=True,
                                                )
        else:
            errors = serializer.errors

        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({"detail": _("Shelf object was increased successfully.")},
                            status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def fill_decrease_shelfobject(self, request, org_pk, lab_pk, **kwargs):
        """
        This action allows the shelf object decrease by following data:
        required quantity and optional description validate through serializer,
        also user needs to have required access permission
        to do this action related to this specific organization and laboratory.

        :param request: http request
        :param org_pk: organization related user permissions
        :param lab_pk: laboratory related to shelf object and user permissions
        :param kwargs: extra params
        :return: decrease shelf object quantity, return success o error message
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk,
                                             "fill_decrease_shelfobject")
        self.serializer_class = DecreaseShelfObjectSerializer
        serializer = self.serializer_class(data=request.data, context={"source_laboratory_id": self.laboratory.pk})
        errors = {}

        if serializer.is_valid():
            save_increase_decrease_shelf_object(request.user, serializer.validated_data,
                                                self.laboratory, self.organization)
        else:
            errors = serializer.errors

        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({"detail": _("Shelf object was decrease successfully.")},
                            status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def reserve(self, request, org_pk, lab_pk, **kwargs):
        """
        This action allows the reserved product creation by following data:
        required quantity, initial and final date validate through serializer,
        also user needs to have required access permission
        to do this action related to this specific organization and laboratory.

        :param request: http request
        :param org_pk: organization related to reserved product and user permissions
        :param lab_pk: laboratory related to reserved product and user permissions
        :param kwargs: extra params
        :return: save a reserved product instance, return success o error message
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "reserve")
        self.serializer_class = ReserveShelfObjectSerializer
        serializer = self.serializer_class(data=request.data, context={"source_laboratory_id": self.laboratory.pk})
        errors = {}
        changed_data = ["laboratory", "organization", "user", "created_by"]

        if serializer.is_valid():
            changed_data = changed_data + list(serializer.validated_data.keys())

            instance = serializer.save(
                laboratory=self.laboratory,
                organization=self.organization,
                user=request.user,
                created_by=request.user
            )

            utils.organilab_logentry(request.user, instance, ADDITION,
                                     'reserved product',
                                     changed_data=changed_data,
                                     relobj=[self.laboratory, instance])
        else:
            errors = serializer.errors

        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({"detail": _("Reservation was performed successfully.")},
                            status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def details(self, request, org_pk, lab_pk, pk, **kwargs):
        """
        Returns all the data from the specified Shelf Object including the Relations Fields

        :param request: http request
        :param org_pk: pk of the organization
        :param lab_pk: pk of the laboratory from which the shelf object is located
        :param pk: pk of the shelf object that the data must be extracted from
        :param kwargs: other extra params
        :return: JsonResponse with a modal containing the details from the shelf object
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "detail")
        shelfobject = self._get_shelfobject_with_check(pk, lab_pk)
        serializer = ShelfObjectDetailSerializer(shelfobject, context={"request":request})
        qr, url = get_or_create_qr_shelf_object(request, shelfobject, org_pk, lab_pk)
        context = {'object': serializer.data}
        if qr:
            image = qr.b64_image
            context['qr'] = image
            context['url'] = reverse('laboratory:download_shelfobject_qr',
                                     kwargs={'org_pk': org_pk, 'lab_pk': lab_pk,
                                             'pk': serializer.data['id']})
        return JsonResponse(context)

    @action(detail=False, methods=['post'])
    def tag(self, request, org_pk, lab_pk, **kwargs):
        """
        Return a tag on SVG format
        .. note:: Not available right now

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "tag")

    @action(detail=False, methods=['post'])
    def transfer_out(self, request, org_pk, lab_pk, **kwargs):
        """
        Creates the request to transfer a shelf object into a different laboratory

        :param request: http request
        :param org_pk: pk of the organization being updated
        :param lab_pk: pk of the laboratory from which the object will be transfer from
        :param kwargs: other extra params
        :return: JsonResponse with result information (success or errors)
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "transfer_out")
        self.serializer_class = TransferOutShelfObjectSerializer
        serializer = self.get_serializer(data=request.data, context={"source_laboratory_id": lab_pk})
        errors = {}

        if serializer.is_valid():
            shelf_object = serializer.validated_data["shelf_object"]
            amount_to_transfer = serializer.validated_data["amount_to_transfer"]
            if amount_to_transfer <= shelf_object.quantity:
                source_laboratory = get_object_or_404(Laboratory, pk=lab_pk)
                target_laboratory = serializer.validated_data["laboratory"]
                transfer_obj = TranferObject.objects.create(
                    object=shelf_object,
                    laboratory_send=source_laboratory,
                    laboratory_received=target_laboratory,
                    quantity=amount_to_transfer,
                    mark_as_discard=serializer.validated_data['mark_as_discard'],
                    created_by=request.user
                )
                utils.organilab_logentry(
                    request.user, transfer_obj, ADDITION, 'transferobject',
                    changed_data=['object', 'laboratory_send', 'laboratory_received',
                                  'quantity', 'mark_as_discard', 'created_by'],
                    relobj=[source_laboratory, target_laboratory]
                )
            else:
                errors["amount_to_transfer"] = [
                    _("This value cannot be greater than the quantity available for the object.")]
        else:
            errors = serializer.errors

        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({"detail": _("The transfer out was saved successfully.")},
                            status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def transfer_available_list(self, request, org_pk, lab_pk, **kwargs):
        """
        Returns the transfers that have the provided laboratory saved as laboratory_received, this for the ones that have not been approved yet.

        :param request: http request
        :param org_pk: pk of the organization being queried
        :param lab_pk: pk of the laboratory that can receive the transfer in
        :param kwargs: other extra params
        :return: JsonResponse with the transfer request information and the number of records
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk,
                                             "transfer_available_list")
        self.serializer_class = TransferObjectDataTableSerializer
        self.pagination_class = LimitOffsetPagination
        self.filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
        self.search_fields = ['object__object__name', 'quantity',
                              'laboratory_send__name', 'update_time',
                              'mark_as_discard']  # for the global search
        self.ordering_fields = ['object__object__name', 'quantity',
                                'laboratory_send__name', 'update_time',
                                'mark_as_discard']
        self.ordering = ('-update_time',)  # default order

        self.queryset = TranferObject.objects.filter(laboratory_received=lab_pk,
                                                     status=REQUESTED)
        queryset = self.filter_queryset(self.queryset)
        data = self.paginate_queryset(queryset)
        response_data = {'data': data, 'recordsTotal': self.queryset.count(),
                         'recordsFiltered': self.queryset.count(),
                         'draw': self.request.query_params.get('draw', 1)}
        return JsonResponse(self.get_serializer(response_data).data)

    @action(detail=False, methods=["delete"])
    def transfer_in_deny(self, request, org_pk, lab_pk, **kwargs):
        """
        Denies a transfer in, which means it will be deleted from database and the change added to the log

        :param request: http request
        :param org_pk: pk of the organization being queried
        :param lab_pk: pk of the laboratory that can receive the transfer in
        :param kwargs: other extra params
        :return: JsonResponse with result information (success or error info)
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "transfer_in_deny")
        self.serializer_class = TransferInShelfObjectSerializer
        serializer = self.get_serializer(data=request.data, context={"laboratory_id": lab_pk})
        if serializer.is_valid():
            utils.organilab_logentry(self.request.user,
                                    serializer.validated_data['transfer_object'], DELETION,
                                    relobj=self.laboratory)
            serializer.validated_data['transfer_object'].delete()
            return JsonResponse({'detail': _('The transfer in was denied successfully.')},
                                status=status.HTTP_200_OK)

        return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def transfer_in_approve(self, request, org_pk, lab_pk, **kwargs):
        """
        Approves a transfer in, which means it will be moved/added to the new laboratory and decrement/move it from the source laboratory

        :param request: http request
        :param org_pk: pk of the organization being queried
        :param lab_pk: pk of the laboratory that can receive the transfer in
        :param kwargs: other extra params
        :return: JsonResponse with result information (success or error info)
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "transfer_in_approve")
        transfer_obj = get_object_or_404(TranferObject, pk=request.data.get('transfer_object'))
        self.serializer_class = TransferInShelfObjectApproveWithContainerSerializer if transfer_obj.object.object.type == Object.REACTIVE else TransferInShelfObjectSerializer

        serializer = self.get_serializer(data=request.data, context={"laboratory_id": lab_pk, "organization_id": org_pk, "validate_for_approval": True})

        if serializer.is_valid():
            # once we get here everything is validated and ready for the transfer in to happen

            transfer_object = serializer.validated_data['transfer_object']
            if transfer_object.quantity == transfer_object.object.quantity:
                # move the entire shelfobject instead of copy it, so history is not lost
                new_shelf_object = move_shelfobject_to(transfer_object.object, org_pk, lab_pk, serializer.validated_data['shelf'], request)
            else:
                # partially transfer the shelfobject to the new laboratory - it will copy it with the required quantity and decrease the original one
                new_shelf_object = move_shelfobject_partial_quantity_to(transfer_object.object, org_pk, lab_pk, serializer.validated_data['shelf'],
                                                                        request, transfer_object.quantity)

            # setup the right option for mark as discard according to what the user selected for the transfer
            new_shelf_object.marked_as_discard = transfer_object.mark_as_discard

            # it is a transfer that has a container - get the container and assign it to the shelfobject, it will assign None if no container_select_option provided
            new_shelf_object.container = get_or_create_container_based_on_selected_option(serializer.validated_data.get('container_select_option'),
                                                                                            org_pk, lab_pk, serializer.validated_data['shelf'], request,
                                                                                            serializer.validated_data.get('container_for_cloning'),
                                                                                            serializer.validated_data.get('available_container'), transfer_object.object)
            new_shelf_object.save()
            utils.organilab_logentry(request.user, new_shelf_object, CHANGE, changed_data=['container', 'marked_as_discard'], relobj=lab_pk)

            # mark transfer as accepted
            transfer_object.status = ACCEPTED
            transfer_object.save()
            utils.organilab_logentry(request.user, transfer_object, CHANGE, changed_data=['status'], relobj=lab_pk)
        else:
            return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({"detail": _("The transfer in was approved successfully.")}, status=status.HTTP_200_OK)


    @action(detail=False, methods=['delete'])
    def delete(self, request, org_pk, lab_pk, **kwargs):
        """
        Deletes a specific shelf object from a shelf

        :param request: http request
        :param org_pk: pk of the organization
        :param lab_pk: pk of the laboratory from which the shelf object is located
        :param kwargs: other extra params
        :return: JsonResponse with the status of the DELETE request
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "delete")
        serializer = ShelfObjectDeleteSerializer(data=request.data, context={"laboratory_id": self.laboratory.pk})
        if serializer.is_valid():
            shelfobject = serializer.validated_data['shelfobj']
            utils.organilab_logentry(self.request.user, shelfobject, DELETION,
                                    relobj=self.laboratory)
            log_object_change(request.user, lab_pk, shelfobject, shelfobject.quantity, 0,
                            '', DELETION, _("Delete"))

            delete_container = serializer.validated_data.get('delete_container', False)

            if shelfobject.container and delete_container:
                shelfobject.container.delete()

            shelfobject.delete()

            return JsonResponse({'detail': _('The item was deleted successfully')}, status=status.HTTP_200_OK)

        return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['post'])
    def create_comments(self, request, org_pk, lab_pk, pk, **kwargs):
        """
        Creates a new observation for a specific shelf object

        :param request: http request
        :param org_pk: pk of the organization
        :param lab_pk: pk of the laboratory from which the shelf object is located
        :param pk: pk of the shelf object that the comment will be added to
        :param kwargs: other extra params
        :return: JsonResponse with the status of the creating
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "create_comments")
        shelf_object = self._get_shelfobject_with_check(pk, lab_pk)
        serializer_sho = CreateObservationShelfObjectSerializer(data=request.data)
        errors = {}
        if serializer_sho.is_valid():
            observation_instance = serializer_sho.save(shelf_object=shelf_object,
                                                       created_by=request.user)
            utils.organilab_logentry(request.user, observation_instance, ADDITION,
                                     'shelfobjectobservation', relobj=self.laboratory)
        else:
            errors = serializer_sho.errors

        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({"detail": _("Observation was created successfully.")},
                            status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def list_comments(self, request, org_pk, lab_pk, pk, **kwargs):
        """
        Returns all the observations related to a specific shelf object

        :param request: http request
        :param org_pk: pk of the organization
        :param lab_pk: pk of the laboratory from which the shelf object is located
        :param pk: pk of the shelf object that the data must be extracted from
        :param kwargs: other extra params
        :return: Response with the observations related to the shelf object and the number of records
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "list_comments")
        shelf_object = self._get_shelfobject_with_check(pk, lab_pk)
        self.serializer_class = ShelfObjectObservationDataTableSerializer
        self.pagination_class = LimitOffsetPagination
        self.filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
        self.search_fields = ['action_taken', 'description', 'created_by__first_name',
                              'created_by__last_name', 'creation_date']
        self.ordering = ('-creation_date',)
        self.queryset = shelf_object.shelfobjectobservation_set.all()
        queryset = self.filter_queryset(self.queryset)
        data = self.paginate_queryset(queryset)
        response_data = {'data': data, 'recordsTotal': self.queryset.count(),
                         'recordsFiltered': self.queryset.count(),
                         'draw': self.request.query_params.get('draw', 1)}

        return Response(self.get_serializer(response_data).data)

    @action(detail=True, methods=['put'])
    def update_status(self, request, org_pk, lab_pk, pk, **kwargs):
        """
        This action allows the change of shelfobject status, also user needs to have required access permission to do this action to change the state.
        Changes the status for a specific shelf object

        :param org_pk: pk of the organization
        :param lab_pk: pk of the laboratory from which the shelf object is located
        :param kwargs: other extra params
        :param pk: pk of the shelf object that is changing the status
        :return: JsonResponse with the description and detail of the shelfobject status if is a success or only the detail when is an error
        """

        self._check_permission_on_laboratory(request, org_pk, lab_pk, "update_status")
        self.serializer_class = UpdateShelfObjectStatusSerializer
        data = {'shelf_object': pk}
        data.update(request.data)
        serializer = self.serializer_class(data=data, context={'laboratory_id': lab_pk})

        if serializer.is_valid():
            shelfobject = serializer.validated_data['shelf_object']
            pre_status = shelfobject.status.description if shelfobject.status else _(
                "No status")
            shelfobject.status = serializer.validated_data['status']
            shelfobject.save()
            ShelfObjectObservation.objects.create(
                action_taken=
                _("Status Change of %(pre_status)s of %(description)s") % {
                    'pre_status': pre_status,
                    'description': shelfobject.status.description
                },
                description=serializer.validated_data[
                    'description'],
                shelf_object=shelfobject,
                created_by=request.user)
            utils.organilab_logentry(
                request.user, shelfobject, CHANGE,
                changed_data=['status'],
                relobj=self.laboratory
            )
            return JsonResponse(
                {"detail": _("The object status was updated successfully"),
                 'shelfobject_status': shelfobject.status.description},
                status=status.HTTP_200_OK)

        return JsonResponse({"errors": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def move_shelfobject_to_shelf(self, request, org_pk, lab_pk, **kwargs):
        """
        This action allows the shelf object movements to others shelves inside a same laboratory,
        also user needs to have required access permission to do this action and visualize only shelves
        related to this specific organization and laboratory.

        :param request: http request
        :param org_pk: organization related to shelf object and user permissions
        :param lab_pk: laboratory related to shelf object and user permissions
        :param kwargs: extra params
        :return: move shelf object to other shelf, return success o error message
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk,
                                             "move_shelfobject_to_shelf")

        self.serializer_class = MoveShelfObjectSerializer
        self.serializer_class_container = MoveShelfObjectWithContainerSerializer

        serializer = self.serializer_class(data=request.data, context={"laboratory_id": lab_pk, "organization_id": org_pk })
        serializer_container = self.serializer_class_container(data=request.data,
                                                               context={"laboratory_id": lab_pk, "organization_id": org_pk})
        errors = {}

        if serializer.is_valid():
            shelf = serializer.validated_data['shelf']
            shelf_object = serializer.validated_data['shelf_object']
            shelf_object.shelf = shelf
            changed_data = ['shelf']
            relobj = [self.laboratory, shelf_object]
            object_repr = 'shelf object'
            user = request.user

            if shelf_object.object.type == Object.REACTIVE:
                if serializer_container.is_valid():
                    container_option = serializer_container.validated_data.get(
                        'container_select_option')
                    if  container_option != "use_source":
                        changed_data.append("container")

                    shelf_object.container = get_or_create_container_based_on_selected_option(
                        container_option,
                        org_pk, lab_pk, shelf, request,
                        serializer_container.validated_data.get('container_for_cloning',
                                                                None),
                        serializer_container.validated_data.get('available_container',
                                                                None),
                        shelf_object)
                    save_object_by_action(user, shelf_object, relobj, changed_data,
                                          CHANGE, object_repr)
                else:
                    errors = serializer_container.errors
            else:
                save_object_by_action(user, shelf_object, relobj, changed_data, CHANGE,
                                      object_repr)
        else:
            errors = serializer.errors

        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({"detail": _("Object was moved successfully.")},
                            status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def shelf_availability_information(self, request, org_pk, lab_pk, **kwargs):
        """
        This action allows a shelf data request, also user needs to have required access permission
        to visualize shelf information related to this specific organization and laboratory.
        Moreover, it should be stressed that 'shelf info' field return a render_to_string template
        with all necessary shelf information by structured html code.

        :param request: http request
        :param org_pk: organization related to shelf object and user permissions
        :param lab_pk: laboratory related to shelf object and user permissions
        :param kwargs: extra params
        :return: JsonResponse with shelf availability information which contains following fields:
            name, type, quantity, discard, measurement_unit, quantity_storage_status,
            percentage_storage_status and shelf_info.
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk,
                                             "shelf_availability_information")
        self.serializer_class = ValidateShelfInformationPositionSerializer
        serializer = self.serializer_class(data=request.query_params, context={
            "laboratory_id": self.laboratory.pk})
        errors, data = {}, {}

        if serializer.is_valid():
            shelf = serializer.validated_data['shelf']
            position = serializer.validated_data.get('position', 'top')
            data = ShelfSerializer(shelf, context={'position': position}).data
        else:
            errors = serializer.errors

        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def create_status(self, request, org_pk, lab_pk, **kwargs):
        """
        Creates new status for shelfobjects

        :param request: http request
        :param org_pk: organization related to reserved product and user permissions
        :param lab_pk: laboratory related to reserved product and user permissions
        :param kwargs: extra params
        :return: save a status in it catalog, return success o error message
        """

        self._check_permission_on_laboratory(request, org_pk, lab_pk, "create_status")

        self.serializer_class = ShelfObjectStatusSerializer
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            Catalog.objects.create(key='shelfobject_status',
                                   description=serializer.data['description'])
            return JsonResponse({'detail': _('The item was created successfully')},
                                status=status.HTTP_200_OK)

        return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['post'])
    def manage_shelfobject_container(self, request, org_pk, lab_pk, **kwargs):
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "manage_shelfobject_container")
        self.serializer_class=ManageContainerSerializer
        serializer = self.serializer_class(data=request.data, context={'organization_id': org_pk, 'laboratory_id': lab_pk})

        if serializer.is_valid():
            shelf_object = serializer.validated_data['shelf_object']
            #old_container = shelf_object.container
            new_container_object=get_or_create_container_based_on_selected_option(
                    serializer.validated_data['container_select_option'],
                    org_pk, lab_pk,
                    serializer.validated_data['shelf'], request,
                    container_for_cloning = serializer.validated_data['container_for_cloning'],
                    available_container = serializer.validated_data['available_container']
                )
            shelf_object.container = new_container_object
            shelf_object.save()

            return JsonResponse({'detail': _('The item was updated successfully')},
                                    status=status.HTTP_200_OK)

        return JsonResponse({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'])
    def edit_equipment_shelfobject(self, request, org_pk, lab_pk, pk, **kwargs):

        self._check_permission_on_laboratory(request, org_pk, lab_pk, "edit_shelfobject")
        shelf_object = self._get_shelfobject_with_check(pk, lab_pk)
        context = {"lab_pk":lab_pk,"org_pk":org_pk}
        serializer_equipment = EditEquipmentShelfObjectSerializer(instance=shelf_object,
                                                                  data=request.data,
                                                                  context=context)
        data = request.data.copy()
        data.update({"shelfobject": shelf_object.pk})

        if hasattr(shelf_object,"shelfobjectequipmentcharacteristics"):
            serializer_equipment_charac = EditEquimentShelfobjectCharacteristicSerializer(instance=shelf_object.shelfobjectequipmentcharacteristics,
                                                                                          data=data,
                                                                                          context=context)
        else:
            serializer_equipment_charac = EditEquimentShelfobjectCharacteristicSerializer(data=data, context=context)

        errors = {}

        if serializer_equipment_charac.is_valid():
            obj_ch = serializer_equipment_charac.save()
            utils.organilab_logentry(request.user, obj_ch, CHANGE,
                                     'shelfobjectequipmentcharacteristics',
                                     relobj=lab_pk)

            if serializer_equipment.is_valid():
                obj = serializer_equipment.save()
                utils.organilab_logentry(request.user, obj, CHANGE,
                                         'shelfobject', relobj=lab_pk)
            else:
                errors = serializer_equipment.errors

        else:
            errors = serializer_equipment_charac.errors

        if errors:
            return JsonResponse(errors, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({"detail": _("Shelfobject was updated successfully.")},
                            status=status.HTTP_200_OK)


class SearchLabView(viewsets.GenericViewSet):
    """
This generic view set allows to find a specific element like a laboratory room,
furniture, shelf, shelf object or object by filters tags, those are compounds by
unique pk, value(join between pk and name), objtype and color.
User access will be checking on view permissions, laboratory and organization.

Priority search level:

1. Object
2. Shelf Object
3. Shelf
4. Furniture
5. Laboratory Room

Priority search level represents a value object on laboratory search elements.
An example is multiple search tags like a laboratory room tag and an object tag,
the second tag will modify laboratory room result as a first tag.
"""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def _check_permission_on_laboratory(self, request, org_pk, lab_pk):
        perms_list = ['laboratory.view_laboratory', 'laboratory.view_laboratoryroom',
                      'laboratory.view_furniture', 'laboratory.view_shelf',
                      'laboratory.view_shelfobject', 'laboratory.view_object']
        if request.user.has_perms(perms_list):
            self.organization = get_object_or_404(
                OrganizationStructure.objects.using(settings.READONLY_DATABASE),
                pk=org_pk)
            self.laboratory = get_object_or_404(
                Laboratory.objects.using(settings.READONLY_DATABASE), pk=lab_pk)
            user_is_allowed_on_organization(request.user, self.organization)
            organization_can_change_laboratory(self.laboratory, self.organization,
                                               raise_exec=True)
        else:
            raise PermissionDenied()

    def get_labroom(self, labroom):
        result = {}
        if labroom:
            result = self.get_pk_list(labroom)
        return result

    def get_furniture(self, furniture):
        result = {}
        if furniture:
            furniture = self.get_pk_list(furniture)
            furniture_list = Furniture.objects.filter(pk__in=furniture).using(
                settings.READONLY_DATABASE)

            if furniture_list:
                result = {
                    'furniture': furniture,
                    'labroom': list(
                        furniture_list.values_list('labroom__pk', flat=True))
                }
        return result

    def get_shelf(self, shelf):
        result = {}
        if shelf:
            shelf = self.get_pk_list(shelf)
            shelf_list = Shelf.objects.filter(pk__in=shelf).using(
                settings.READONLY_DATABASE)

            if shelf_list:
                result = {
                    'shelf': shelf,
                    'furniture': list(
                        shelf_list.values_list('furniture__pk', flat=True)),
                    'labroom': list(
                        shelf_list.values_list('furniture__labroom__pk', flat=True))
                }
        return result

    def get_shelfobject(self, shelfobject):
        shelfobj_base = shelfobject
        result = {}
        if shelfobject:
            shelfobject = self.get_pk_list(shelfobject)
            shelfobject_list = ShelfObject.objects.filter(pk__in=shelfobject).using(
                settings.READONLY_DATABASE)

            if shelfobject_list:
                shelf = []
                for shelfobj in shelfobj_base:
                    if shelfobject_list.filter(pk=shelfobj.pk).exists():
                        shelf.append(shelfobj.shelf.pk)
                result = {
                    'shelfobject': shelfobject,
                    'shelf': shelf,
                    'furniture': list(
                        shelfobject_list.values_list('shelf__furniture__pk',
                                                     flat=True)),
                    'labroom': list(
                        shelfobject_list.values_list('shelf__furniture__labroom__pk',
                                                     flat=True))
                }
        return result

    def get_object_param(self, object_param, lab_pk):
        result = {}
        if object_param:
            object_param_name = [obj.name for obj in object_param]
            object_list = Object.objects.filter(name__in=object_param_name).using(
                settings.READONLY_DATABASE)
            shelf = Shelf.objects.filter(shelfobject__object__in=object_list,
                                         furniture__labroom__laboratory=lab_pk).using(
                settings.READONLY_DATABASE).order_by('pk')
            shelf_pk_list = list(
                shelf.values_list('pk', flat=True).using(settings.READONLY_DATABASE))
            shelf_pk_list.reverse()
            object_param_name.reverse()
            result = {
                'object': object_param_name,
                'shelf': {
                    'shelf': shelf_pk_list,
                    'furniture': list(
                        shelf.values_list('furniture__pk', flat=True).distinct().using(
                            settings.READONLY_DATABASE)),
                    'labroom': list(shelf.values_list('furniture__labroom',
                                                      flat=True).distinct().using(
                        settings.READONLY_DATABASE))
                }
            }
        return result

    def get_pk_list(self, queryset):
        return [obj.pk for obj in queryset]

    @action(detail=False, methods=['get'])
    def get(self, request, org_pk, lab_pk):
        """
        Return an object with following structure

        .. code-block:: python

            search_list = {
                'labroom': [pk laboratory rooms],
                'furniture': {'furniture': [], 'labroom': []},
                'shelf': {'shelf': [], 'furniture': [], 'labroom': []},
                'shelfobject': {'shelfobject': [], 'shelf': [], 'furniture': [], 'labroom': []},
                'object': {'object': [], 'shelf': {'shelf': [], 'furniture': [], 'labroom': []}}
            }

        :param request: http request
        :param org_pk: organization related user permissions
        :param lab_pk: laboratory related to laboratory rooms, furniture, shelves,
         shelf objects and objects.
        :return: an object with possible matches related to get param
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk)
        search_list, errors = {}, {}
        serializer = SearchShelfObjectSerializerMany(data=request.query_params,
                                                     context={"source_laboratory_id": lab_pk})

        if serializer.is_valid():
            search_list = {
                'labroom': self.get_labroom(
                    serializer.validated_data.get('labroom', [])),
                'furniture': self.get_furniture(
                    serializer.validated_data.get('furniture', [])),
                'shelf': self.get_shelf(serializer.validated_data.get('shelf', [])),
                'shelfobject': self.get_shelfobject(
                    serializer.validated_data.get('shelfobject', [])),
                'object': self.get_object_param(
                    serializer.validated_data.get('object', []), lab_pk)
            }
        else:
            errors = serializer.errors

        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({'search_list': search_list}, status=status.HTTP_200_OK)


class AuthAllPermBaseObjectManagementShelfObjectBase(AuthAllPermBaseObjectManagement):
    permission_classes = (PermissionByLaboratoryInOrganization,)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    ordering_fields = ['pk']
    ordering = ('pk',)
    org_pk, lab_pk, shelfobject = None, None, None

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        if self.shelfobject:
            return queryset.filter(shelfobject=self.shelfobject).distinct()
        return queryset.none()

    def list(self, request, *args, **kwargs):
        self.org_pk = kwargs['org_pk']
        self.lab_pk = kwargs['lab_pk']
        self.shelfobject = kwargs['shelfobject']
        return super().list(request, *args, **kwargs)


class ShelfObjectMaintanenceViewset(AuthAllPermBaseObjectManagementShelfObjectBase):
    serializer_class = {
        'list': MaintenanceDatatableSerializer,
        'destroy': MaintenanceSerializer,
        'create': CreateMaintenanceSerializer,
        'update': UpdateMaintenanceSerializer,
    }
    perms = {
        "create": ["laboratory.add_shelfobjectmaintenance",
                   "laboratory.view_shelfobjectmaintenance"],
        "update": ["laboratory.change_shelfobjectmaintenance",
                   "laboratory.view_shelfobjectmaintenance"],
        "destroy": ["laboratory.delete_shelfobjectmaintenance",
                    "laboratory.view_shelfobjectmaintenance"],
        "detail": ["laboratory.view_shelfobjectmaintenance"]
    }

    queryset = ShelfObjectMaintenance.objects.all()
    search_fields = ['provider_of_maintenance__name', 'validator__user__first_name',
                     'validator__user__last_name','maintenance_observation']
    filterset_class = ShelfObjectMaintenanceFilter
    ordering_fields = ['maintenance_date']
    ordering = ('maintenance_date',)

    def create(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        self.shelfobject = kwargs['shelfobject']
        serializer = CreateMaintenanceSerializer(data=request.data, context={
            'org_pk': self.org_pk,
            'lab_pk': self.lab_pk,
            'shelfobject': self.shelfobject})
        if serializer.is_valid():
            maintenance = serializer.save()
            ShelfObjectObservation.objects.create(
                description=maintenance.maintenance_observation,
                action_taken=_("Maintenance created"),
                shelf_object=maintenance.shelfobject,
                created_by=self.request.user)
            utils.organilab_logentry(request.user, maintenance, ADDITION,
                                     'shelfobjectmaintenance',
                                     relobj=self.lab_pk)
            return JsonResponse({}, status=status.HTTP_201_CREATED)

        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):

        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        self.shelfobject = kwargs['shelfobject']

        instance = self.get_object()

        validate_shelfobject = ValidateShelfobjectEditSerializer(
            data={"shelfobject": self.shelfobject,
                  "organization": self.org_pk},
            context={'org_pk': self.org_pk,
                     'lab_pk': self.lab_pk,
                     'shelfobject': self.shelfobject})

        if validate_shelfobject.is_valid(raise_exception=True):
            ShelfObjectObservation.objects.create(description=
                                                  instance.maintenance_observation,
                                                  action_taken=_("Maintenance deleted"),
                                                  shelf_object=instance.shelfobject,
                                                  created_by=self.request.user)
            utils.organilab_logentry(request.user, instance, DELETION,
                                     'shelfobjectmaintenance', relobj=self.lab_pk)
            instance.delete()
            return JsonResponse({}, status=status.HTTP_200_OK)

        return JsonResponse({"detail": "Maintenance do not exists"},
                            status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        self.shelfobject = kwargs['shelfobject']
        request.data.update({"created_by": self.request.user.pk})

        instance = self.get_object()

        validate_shelfobject = UpdateMaintenanceSerializer(
            instance=instance, data=request.data,
            context={'org_pk': self.org_pk,
                     'lab_pk': self.lab_pk,
                     'shelfobject': self.shelfobject})

        if validate_shelfobject.is_valid():
            instance = validate_shelfobject.save()
            ShelfObjectObservation.objects.create(
                description=instance.maintenance_observation,
                action_taken=_("Maintenance updated"),
                shelf_object=instance.shelfobject,
                created_by=self.request.user)
            utils.organilab_logentry(request.user, instance, CHANGE,
                                     'shelfobjectmaintenance', relobj=self.lab_pk)
            return JsonResponse({}, status=status.HTTP_200_OK)

        return JsonResponse(validate_shelfobject.errors,
                            status=status.HTTP_400_BAD_REQUEST)

class ShelfObjectLogViewset(AuthAllPermBaseObjectManagementShelfObjectBase):
    serializer_class = {
        'list': ShelfObjectLogDatatableSerializer,
        'destroy': ShelfObjectLogSerializer,
        'create': ValidateShelfObjectLogSerializer,
        'update': ValidateShelfObjectLogSerializer,
    }
    perms = {
        "create": ["laboratory.add_shelfobjectlog",
                   "laboratory.view_shelfobjectlog"],
        "update": ["laboratory.change_shelfobjectlog",
                   "laboratory.view_shelfobjectlog"],
        "destroy": ["laboratory.delete_shelfobjectlog",
                    "laboratory.view_shelfobjectlog"],
        "detail": ["laboratory.view_shelfobjectlog"]
    }

    queryset = ShelfObjectLog.objects.all()
    search_fields = ['description','created_by__first_name', 'created_by__last_name']
    filterset_class = ShelfObjectLogtFilter

    def create(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        self.shelfobject = kwargs['shelfobject']

        serializer = ValidateShelfObjectLogSerializer(data=request.data, context={
            'org_pk': self.org_pk,
            'lab_pk': self.lab_pk,
            'shelfobject': self.shelfobject})
        if serializer.is_valid():
            log = serializer.save()

            utils.organilab_logentry(request.user, log, ADDITION,
                                     'shelfobjectlog',
                                     changed_data=[serializer.validated_data],
                                     relobj=self.lab_pk)
            return JsonResponse({}, status=status.HTTP_201_CREATED)

        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        self.shelfobject = kwargs['shelfobject']
        instance = self.get_object()

        validate_log = ValidateShelfobjectEditSerializer(
            data={"shelfobject": self.shelfobject,
                  "organization": self.org_pk},
            context={'org_pk': self.org_pk,
                     'lab_pk': self.lab_pk,
                     'shelfobject': self.shelfobject})

        if validate_log.is_valid(raise_exception=True):
            utils.organilab_logentry(request.user, instance, DELETION,
                                     'shelfobjectlog',
                                     relobj=self.lab_pk)
            instance.delete()
            return JsonResponse({}, status=status.HTTP_200_OK)

        return JsonResponse({"detail": "Log do not exists"},
                            status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        self.shelfobject = kwargs['shelfobject']
        request.data.update({"created_by": self.request.user.pk})
        instance = self.get_object()

        validate_log = ValidateShelfObjectLogSerializer(
            instance=instance, data=request.data,
            context={'org_pk': self.org_pk,
                     'lab_pk': self.lab_pk,
                     'shelfobject': self.shelfobject})

        if validate_log.is_valid():
            instance = validate_log.save()
            utils.organilab_logentry(request.user, instance, CHANGE,
                                     'shelfobjectlog',
                                     changed_data=[validate_log.validated_data],
                                     relobj=self.lab_pk)
            return JsonResponse({}, status=status.HTTP_200_OK)

        return JsonResponse(validate_log.errors,
                            status=status.HTTP_400_BAD_REQUEST)

class ShelfObjectCalibrateViewset(AuthAllPermBaseObjectManagementShelfObjectBase):
    serializer_class = {
        'list': ShelfObjectCalibrateDatatableSerializer,
        'destroy': ShelfObjectCalibrateSerializer,
        'create': ValidateShelfObjectCalibrateSerializer,
        'update': ValidateShelfObjectCalibrateSerializer,
    }
    perms = {
        "create": ["laboratory.add_shelfobjectcalibrate",
                   "laboratory.view_shelfobjectcalibrate"],
        "update": ["laboratory.change_shelfobjectcalibrate",
                   "laboratory.view_shelfobjectcalibrate"],
        "destroy": ["laboratory.delete_shelfobjectcalibrate",
                    "laboratory.view_shelfobjectcalibrate"],
        "detail": ["laboratory.view_shelfobjectcalibrate"]
    }

    queryset = ShelfObjectCalibrate.objects.all()
    search_fields = ['calibrate_name', 'observation', "validator__user__first_name",
                     "validator__user__last_name"]
    filterset_class = ShelfObjectCalibrateFilter
    ordering_fields = ['calibration_date']
    ordering = ('calibration_date',)

    def create(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        self.shelfobject = kwargs['shelfobject']
        serializer = ValidateShelfObjectCalibrateSerializer(data=request.data, context={
            'org_pk': self.org_pk,
            'lab_pk': self.lab_pk,
            'shelfobject': self.shelfobject})
        if serializer.is_valid():
            calibration = serializer.save()
            ShelfObjectObservation.objects.create(description=calibration.observation,
                                                  action_taken=_("Calibration created"),
                                                  shelf_object=calibration.shelfobject,
                                                  created_by=self.request.user)
            utils.organilab_logentry(request.user, calibration, ADDITION,
                                     'shelfobjectcalibrate',
                                     changed_data=[serializer.validated_data],
                                     relobj=self.lab_pk)

            return JsonResponse({}, status=status.HTTP_201_CREATED)

        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):

        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        self.shelfobject = kwargs['shelfobject']
        instance = self.get_object()

        validate_calibrate = ValidateShelfobjectEditSerializer(
            data={"shelfobject": self.shelfobject,
                  "organization": self.org_pk},
            context={'org_pk': self.org_pk,
                     'lab_pk': self.lab_pk,
                     'shelfobject': self.shelfobject})

        if validate_calibrate.is_valid(raise_exception=True):
            ShelfObjectObservation.objects.create(description=instance.observation,
                                                  action_taken=_("Calibration deleted"),
                                                  shelf_object=instance.shelfobject,
                                                  created_by=self.request.user)
            utils.organilab_logentry(request.user, instance, DELETION,
                                     'shelfobjectcalibrate', relobj=self.lab_pk)
            instance.delete()
            return JsonResponse({}, status=status.HTTP_200_OK)

        return JsonResponse({"detail": "Calibration do not exists"},
                            status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        self.org_pk = kwargs['org_pk']
        self.lab_pk = kwargs['lab_pk']
        self.shelfobject = kwargs['shelfobject']
        return super().list(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        self.shelfobject = kwargs['shelfobject']
        request.data.update({"created_by": self.request.user.pk})
        request.data.update({"validator": self.request.user.profile.pk})
        instance = self.get_object()

        validate_calibrate = ValidateShelfObjectCalibrateSerializer(
            instance=instance, data=request.data,
            context={'org_pk': self.org_pk,
                     'lab_pk': self.lab_pk,
                     'shelfobject': self.shelfobject})

        if validate_calibrate.is_valid():
            instance = validate_calibrate.save()
            ShelfObjectObservation.objects.create(description=instance.observation,
                                                  action_taken=_("Calibration updated"),
                                                  shelf_object=instance.shelfobject,
                                                  created_by=self.request.user)
            utils.organilab_logentry(request.user, instance, CHANGE,
                                     'shelfobjectcalibrate',
                                     changed_data=[validate_calibrate.validated_data],
                                     relobj=self.lab_pk)
            return JsonResponse({}, status=status.HTTP_200_OK)

        return JsonResponse(validate_calibrate.errors,
                            status=status.HTTP_400_BAD_REQUEST)

class ShelfObjectGuaranteeViewset(AuthAllPermBaseObjectManagementShelfObjectBase):
    serializer_class = {
        'list': ShelfObjectGuaranteeDatatableSerializer,
        'destroy': ShelfObjectGuaranteeSerializer,
        'create': ValidateShelfObjectGuaranteeSerializer,
        'update': ValidateShelfObjectGuaranteeSerializer,
    }
    perms = {
        "create": ["laboratory.add_shelfobjectguarantee",
                   "laboratory.view_shelfobjectguarantee"],
        "update": ["laboratory.change_shelfobjectguarantee",
                   "laboratory.view_shelfobjectguarantee"],
        "destroy": ["laboratory.delete_shelfobjectguarantee",
                    "laboratory.view_shelfobjectguarantee"],
        "detail": ["laboratory.view_shelfobjectguarantee"]
    }

    queryset = ShelfObjectGuarantee.objects.all()
    filterset_class = ShelfObjectGuarenteeFilter
    search_fields = ['created_by__first_name','created_by__last_name']

    def create(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        self.shelfobject = kwargs['shelfobject']
        serializer = ValidateShelfObjectGuaranteeSerializer(data=request.data, context={'org_pk':self.org_pk,
                                                                                        'lab_pk':self.lab_pk,
                                                                                        'shelfobject': self.shelfobject})
        if serializer.is_valid():
            guarentee = serializer.save()
            ShelfObjectObservation.objects.create(description=_("New Guarentee from %(initial_date)s to %(final_date)s") % {
                'initial_date': guarentee.guarantee_initial_date,
                'final_date': guarentee.guarantee_final_date,
            },

                                                  action_taken=_("Guarentee created"),
                                                  shelf_object=guarentee.shelfobject,
                                                  created_by=self.request.user)
            utils.organilab_logentry(request.user, guarentee, ADDITION,
                                     'shelfobjectguarantee',
                                     changed_data=[serializer.validated_data],
                                     relobj=self.lab_pk)
            return JsonResponse({},status=status.HTTP_201_CREATED)

        return JsonResponse(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):

        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        self.shelfobject = kwargs['shelfobject']
        guarantee = self.get_object()

        validate_shelfobject = ValidateShelfobjectEditSerializer(data = {"shelfobject":self.shelfobject,
                                                                         "organization": self.org_pk},
                                                                 context = {'org_pk':self.org_pk,
                                                                          'lab_pk':self.lab_pk,
                                                                          'shelfobject': self.shelfobject})

        if validate_shelfobject.is_valid(raise_exception=True):
            ShelfObjectObservation.objects.create(description = "",
                                                  action_taken = _("Guarentee deleted"),
                                                  shelf_object = validate_shelfobject.validated_data["shelfobject"],
                                                  created_by = self.request.user)
            utils.organilab_logentry(request.user, guarantee, DELETION,
                                     'shelfobjectguarantee', relobj=self.lab_pk)
            guarantee.delete()
            return JsonResponse({},status=status.HTTP_200_OK)

        return JsonResponse({"detail": "Guarantee do not exists"},status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        self.shelfobject = kwargs['shelfobject']
        request.data.update({"created_by": self.request.user.pk})
        guarantee = self.get_object()

        validate_shelfobject = ValidateShelfObjectGuaranteeSerializer(
            instance=guarantee, data=request.data,
            context={'org_pk': self.org_pk,
                     'lab_pk': self.lab_pk,
                     'shelfobject': self.shelfobject})

        if validate_shelfobject.is_valid():
            validate_shelfobject.save()
            ShelfObjectObservation.objects.create(description=_("Updating guarentee"),
                                                  action_taken=_("Guarentee updated"),
                                                  shelf_object=
                                                  validate_shelfobject.validated_data[
                                                      "shelfobject"],
                                                  created_by=self.request.user)
            utils.organilab_logentry(request.user, guarantee, CHANGE,
                                     'shelfobjectguarantee',
                                     changed_data=[validate_shelfobject.validated_data]
                                     , relobj=self.lab_pk)
            return JsonResponse({}, status=status.HTTP_200_OK)

        return JsonResponse(validate_shelfobject.errors,
                            status=status.HTTP_400_BAD_REQUEST)

class ShelfObjectTrainingViewset(AuthAllPermBaseObjectManagementShelfObjectBase):
    serializer_class = {
        'list': ShelfObjectTrainingeDatatableSerializer,
        'destroy': ShelfObjectTrainingSerializer,
        'create': ValidateShelfObjectTrainingSerializer,
        'update': ValidateShelfObjectTrainingSerializer,
    }
    perms = {
        "create": ["laboratory.add_shelfobjecttraining",
                   "laboratory.view_shelfobjecttraining"],
        "update": ["laboratory.change_shelfobjecttraining",
                   "laboratory.view_shelfobjecttraining"],
        "destroy": ["laboratory.delete_shelfobjecttraining",
                    "laboratory.view_shelfobjecttraining"],
        "detail": ["laboratory.view_shelfobjecttraining"]
    }

    queryset = ShelfObjectTraining.objects.all()
    search_fields = ['place','observation','number_of_hours']
    filterset_class = ShelfObjectTrainingFilter
    ordering_fields = ['training_initial_date']
    ordering = ('training_initial_date',)

    def create(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        self.shelfobject = kwargs['shelfobject']
        serializer = ValidateShelfObjectTrainingSerializer(data=request.data, context={
            'org_pk': self.org_pk,
            'lab_pk': self.lab_pk,
            'shelfobject': self.shelfobject})
        if serializer.is_valid():
            instance = serializer.save()
            ShelfObjectObservation.objects.create(description=instance.observation,
                                                  action_taken=_("Training created"),
                                                  shelf_object=instance.shelfobject,
                                                  created_by=self.request.user)
            utils.organilab_logentry(request.user, instance, ADDITION,
                                     'shelfobjecttraining',
                                     changed_data=[serializer.validated_data],
                                     relobj=self.lab_pk)
            return JsonResponse({}, status=status.HTTP_201_CREATED)

        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):

        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        self.shelfobject = kwargs['shelfobject']
        instance = self.get_object()

        validate_shelfobject = ValidateShelfobjectEditSerializer(
            data={"shelfobject": self.shelfobject,
                  "organization": self.org_pk},
            context={'org_pk': self.org_pk,
                     'lab_pk': self.lab_pk,
                     'shelfobject': self.shelfobject})

        if validate_shelfobject.is_valid(raise_exception=True):
            ShelfObjectObservation.objects.create(description=instance.observation,
                                                  action_taken=_("Training deleted"),
                                                  shelf_object=
                                                  validate_shelfobject.validated_data[
                                                      "shelfobject"],
                                                  created_by=self.request.user)
            utils.organilab_logentry(request.user, instance, DELETION,
                                     'shelfobjecttraining', relobj=self.lab_pk)
            instance.delete()
            return JsonResponse({}, status=status.HTTP_200_OK)

        return JsonResponse({"detail": "Training do not exists"},
                            status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        self.shelfobject = kwargs['shelfobject']
        request.data.update({"created_by": self.request.user.pk})
        instance = self.get_object()

        validate_shelfobject = ValidateShelfObjectTrainingSerializer(
            instance=instance, data=request.data, context={
                'org_pk': self.org_pk, 'lab_pk': self.lab_pk, 'shelfobject':
                    self.shelfobject})

        if validate_shelfobject.is_valid():
            validate_shelfobject.save()
            ShelfObjectObservation.objects.create(description=instance.observation,
                                                  action_taken=_("Training updated"),
                                                  shelf_object=
                                                  validate_shelfobject.validated_data[
                                                      "shelfobject"],
                                                  created_by=self.request.user)
            utils.organilab_logentry(request.user, instance, CHANGE,
                                     'shelfobjecttraining',
                                     changed_data=[validate_shelfobject.validated_data],
                                     relobj=self.lab_pk)
            return JsonResponse({}, status=status.HTTP_200_OK)

        return JsonResponse(validate_shelfobject.errors,
                            status=status.HTTP_400_BAD_REQUEST)
