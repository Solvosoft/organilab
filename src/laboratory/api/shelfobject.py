from django.conf import settings
from django.contrib.admin.models import CHANGE, ADDITION, DELETION
from django.http import JsonResponse, Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
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
from laboratory.models import Catalog, ShelfObjectObservation, Object
from laboratory.models import OrganizationStructure, ShelfObject, Laboratory, TranferObject
from laboratory.models import REQUESTED, ACCEPTED
from laboratory.qr_utils import get_or_create_qr_shelf_object
from laboratory.shelfobject import serializers as shelfobject_serializers
from laboratory.shelfobject.serializers import IncreaseShelfObjectSerializer, \
    DecreaseShelfObjectSerializer, \
    ReserveShelfObjectSerializer, UpdateShelfObjectStatusSerializer, \
    ShelfObjectObservationDataTableSerializer, \
    MoveShelfObjectSerializer, ShelfObjectDetailSerializer, ShelfSerializer, \
    ValidateShelfSerializer, \
    TransferInSerializer, \
    ShelfObjectLimitsSerializer, ShelfObjectStatusSerializer, \
    ShelfObjectDeleteSerializer, \
    TransferOutShelfObjectSerializer, TransferObjectDataTableSerializer, \
    TransferInApproveWithContainerSerializer
from laboratory.shelfobject.serializers import ShelfObjectPk, \
    SearchShelfObjectSerializerMany
from laboratory.shelfobject.utils import save_increase_decrease_shelf_object, \
    move_shelfobject_partial_quantity_to, build_shelfobject_qr, \
    save_shelfobject_limits_from_serializer, \
    create_shelfobject_observation
from laboratory.utils import organilab_logentry


class ShelfObjectTableViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
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
                pk=int(serializer_so.validated_data['search'].split('=')[1]))
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
        # it will create a new container in the destination shelf with quantity of 1 and decrease the quantity by 1 on the original shelfobject
        new_container = move_shelfobject_partial_quantity_to(
            serializer.validated_data['container'], organization_id, laboratory_id,
            serializer.validated_data['shelf'], request, quantity=1)

        shelfobject = serializer.save(
            created_by=created_by,
            in_where_laboratory_id=laboratory_id,
            limits=limits,
            container=new_container
        )

        build_shelfobject_qr(self.context['request'], shelfobject, organization_id, laboratory_id)

        log_object_change(created_by, laboratory_id, shelfobject, 0, shelfobject.quantity, '', 0, "Create", create=True)
        utils.organilab_logentry(created_by, shelfobject, ADDITION,
                                 changed_data=['object', 'shelf', 'status', 'quantity', 'measurement_unit', 'limit_quantity', 'course_name',
                                               'marked_as_discard', 'batch', 'container', 'created_by', 'in_where_laboratory', 'limits'],
                                 relobj=laboratory_id)

        return shelfobject

    def create_refuse_reactive(self, serializer, limits_serializer):
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
        # it will create a new container in the destination shelf with quantity of 1 and decrease the quantity by 1 on the original shelfobject
        new_container = move_shelfobject_partial_quantity_to(
            serializer.validated_data['container'],
            organization_id, laboratory_id, serializer.validated_data['shelf'], request,
            quantity=1)

        shelfobject = serializer.save(
            created_by=created_by,
            in_where_laboratory_id=laboratory_id,
            limits=limits,
            container=new_container
        )

        build_shelfobject_qr(self.context['request'], shelfobject, organization_id,
                             laboratory_id)

        log_object_change(created_by, laboratory_id, shelfobject, 0,
                          shelfobject.quantity, '',
                          0, "Create", create=True, organization=organization_id)
        utils.organilab_logentry(created_by, shelfobject, ADDITION,
                                 changed_data=['object', 'shelf', 'status', 'quantity',
                                               'measurement_unit', 'marked_as_discard',
                                               'course_name', 'batch', 'container',
                                               'created_by', 'in_where_laboratory',
                                               'limits'],
                                 relobj=laboratory_id)

        return shelfobject

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

        shelfobject = serializer.save(
            created_by=created_by,
            in_where_laboratory_id=laboratory_id,
            limits=limits
        )

        build_shelfobject_qr(self.context['request'], shelfobject, organization_id,
                             laboratory_id)

        log_object_change(created_by, laboratory_id, shelfobject, 0,
                          shelfobject.quantity, '',
                          0, "Create", create=True, organization=organization_id)
        utils.organilab_logentry(created_by, shelfobject, ADDITION,
                                 changed_data=['object', 'shelf', 'status', 'quantity',
                                               'limit_quantity', 'measurement_unit',
                                               'marked_as_discard', 'course_name',
                                               'created_by', 'in_where_laboratory',
                                               'limits'],
                                 relobj=laboratory_id)

        return shelfobject

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

        shelfobject = serializer.save(
            created_by=created_by,
            in_where_laboratory_id=laboratory_id,
            limits=limits
        )

        build_shelfobject_qr(self.context['request'], shelfobject, organization_id,
                             laboratory_id)

        log_object_change(created_by, laboratory_id, shelfobject, 0,
                          shelfobject.quantity, '',
                          0, "Create", create=True, organization=organization_id)
        utils.organilab_logentry(created_by, shelfobject, ADDITION,
                                 changed_data=['object', 'shelf', 'status', 'quantity',
                                               'limit_quantity', 'measurement_unit',
                                               'marked_as_discard', 'course_name',
                                               'created_by', 'in_where_laboratory',
                                               'limits'],
                                 relobj=laboratory_id)

        return shelfobject

    def create_equipment(self, serializer, limits_serializer):
        """
        Create equipment type Shelfobject .
        :param serializer:  ShelfObjectSerializer to create equipment type shelfobject
        :param limits_serializer: Serializer with the data to create ShelfObjectLimits
        :return: equipment type shelfobject was created
        """
        created_by = self.context['request'].user
        laboratory_id = self.context['laboratory_id']
        organization_id = self.context['organization_id']
        limits = save_shelfobject_limits_from_serializer(limits_serializer, created_by)

        shelfobject = serializer.save(
            created_by=created_by,
            in_where_laboratory_id=laboratory_id,
            limits=limits
        )

        build_shelfobject_qr(self.context['request'], shelfobject, organization_id,
                             laboratory_id)

        log_object_change(created_by, laboratory_id, shelfobject, 0,
                          shelfobject.quantity, '',
                          0, "Create", create=True, organization=organization_id)
        utils.organilab_logentry(created_by, shelfobject, ADDITION,
                                 changed_data=['object', 'shelf', 'status', 'quantity',
                                               'limit_quantity', 'measurement_unit',
                                               'marked_as_discard', 'course_name',
                                               'created_by', 'in_where_laboratory',
                                               'limits'],
                                 relobj=laboratory_id)

        return shelfobject

    def create_refuse_equipment(self, serializer, limits_serializer):
        """
        Create refuse equipment type Shelfobject .
        :param serializer:  ShelfObjectSerializer to create refuse equipment type shelfobject
        :param limits_serializer: Serializer with the data to create ShelfObjectLimits
        :return: refuse equipment type shelfobject was created
        """
        created_by = self.context['request'].user
        laboratory_id = self.context['laboratory_id']
        organization_id = self.context['organization_id']
        limits = save_shelfobject_limits_from_serializer(limits_serializer, created_by)

        shelfobject = serializer.save(
            created_by=created_by,
            in_where_laboratory_id=laboratory_id,
            limits=limits
        )

        build_shelfobject_qr(self.context['request'], shelfobject, organization_id,
                             laboratory_id)

        log_object_change(created_by, laboratory_id, shelfobject, 0,
                          shelfobject.quantity, '',
                          0, "Create", create=True, organization=organization_id)
        utils.organilab_logentry(created_by, shelfobject, ADDITION,
                                 changed_data=['object', 'shelf', 'status', 'quantity',
                                               'limit_quantity', 'measurement_unit',
                                               'marked_as_discard', 'course_name',
                                               'created_by', 'in_where_laboratory',
                                               'limits'],
                                 relobj=laboratory_id)

        return shelfobject


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
        self._check_permission_on_laboratory(request, org_pk, lab_pk,
                                             "create_shelfobject")
        self.serializer_class = self._get_create_shelfobject_serializer(request, org_pk,
                                                                        lab_pk)

        serializer = self.serializer_class['serializer'](data=request.data,
                                                         context={"org_pk": org_pk,
                                                                  "lab_pk": lab_pk})
        limit_serializer = ShelfObjectLimitsSerializer(data=request.data)
        errors = {}
        if serializer.is_valid():
            if limit_serializer.is_valid(raise_exception=True):
                shelfobject = self.serializer_class['method'](serializer,
                                                              limit_serializer)
                create_shelfobject_observation(shelfobject, shelfobject.course_name,
                                               _("Created Object"), request.user,
                                               lab_pk)
                return Response(
                    {"detail": _("The creation was performed successfully.")},
                    status=status.HTTP_201_CREATED)
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
        serializer = self.serializer_class(data=request.data, context={
            "source_laboratory_id": self.laboratory.pk})
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
        serializer = self.serializer_class(data=request.data, context={
            "source_laboratory_id": self.laboratory.pk})
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
        serializer = self.serializer_class(data=request.data, context={
            "source_laboratory_id": self.laboratory.pk})
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

            utils.organilab_logentry(request.user, instance, ADDITION, 'reserved product',
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
        serializer = ShelfObjectDetailSerializer(shelfobject)
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
        Devuelve la etiqueta en formato svg
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
        serializer = self.get_serializer(data=request.data,
                                         context={"source_laboratory_id": lab_pk})
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
        self._check_permission_on_laboratory(request, org_pk, lab_pk,
                                             "transfer_in_deny")
        self.serializer_class = TransferInSerializer
        serializer = self.get_serializer(data=request.data,
                                         context={"laboratory_id": lab_pk})
        serializer.is_valid(raise_exception=True)
        utils.organilab_logentry(self.request.user,
                                 serializer.validated_data['transfer_object'], DELETION,
                                 relobj=self.laboratory)
        serializer.validated_data['transfer_object'].delete()
        return JsonResponse({'detail': _('The transfer in was denied successfully.')},
                            status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def transfer_in_approve(self, request, org_pk, lab_pk, **kwargs):
        """
        Approves a transfer in, which means it will be moved/added to the new laboratory and decrement it/move it from the source laboratory
        :param request: http request
        :param org_pk: pk of the organization being queried
        :param lab_pk: pk of the laboratory that can receive the transfer in
        :param kwargs: other extra params
        :return: JsonResponse with result information (success or error info)
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk,
                                             "transfer_in_approve")
        transfer_obj = get_object_or_404(TranferObject,
                                         pk=request.data.get('transfer_object'))
        self.serializer_class = TransferInApproveWithContainerSerializer if transfer_obj.object.object.type == Object.REACTIVE else TransferInSerializer
        serializer = self.get_serializer(data=request.data,
                                         context={"laboratory_id": lab_pk,
                                                  "organization_id": org_pk,
                                                  "validate_for_approval": True})
        errors = {}
        if serializer.is_valid():
            transfer_object = serializer.validated_data['transfer_object']
            if transfer_object.quantity <= transfer_object.object.quantity:
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
                return JsonResponse({"detail": _(
                    "This transfer cannot be accepted since the transfer quantity is bigger " \
                    "than the quantity available in the source object.")},
                                    status=status.HTTP_400_BAD_REQUEST)
        else:
            errors = serializer.errors
        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({"detail": _("The transfer in was approved successfully.")},
                            status=status.HTTP_200_OK)

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
        serializer = ShelfObjectDeleteSerializer(data=request.data, context={
            "laboratory_id": self.laboratory.pk})
        serializer.is_valid(raise_exception=True)
        shelfobject = serializer.validated_data['shelfobj']

        utils.organilab_logentry(self.request.user, serializer.validated_data['shelfobj'], DELETION, relobj=self.laboratory)
        log_object_change(request.user, lab_pk, shelfobject, shelfobject.quantity, 0, '', DELETION, _("Delete"))

        shelfobject.delete()

        return JsonResponse({'detail': _('The item was deleted successfully')}, status=200)

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
        serializer = self.serializer_class(data=request.data, context={
            "source_laboratory_id": self.laboratory.pk})
        errors = {}

        if serializer.is_valid():
            shelf_object = serializer.validated_data['shelf_object']
            shelf_object.shelf = serializer.validated_data['shelf']
            shelf_object.save()
            utils.organilab_logentry(request.user, shelf_object, CHANGE, 'shelf object', changed_data=['shelf'],
                               relobj=[self.laboratory, shelf_object])
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
        self.serializer_class = ValidateShelfSerializer
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
        if serializer.is_valid(raise_exception=True):
            Catalog.objects.create(key='shelfobject_status',
                                   description=serializer.data['description'])
            return JsonResponse({'detail': _('The item was created successfully')},
                                status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SearchLabView(viewsets.GenericViewSet):
    """
    This generic view set allows to find a specific element like a laboratory room,
     furniture, shelf, shelf object or object by filters tags, those are compounds by
     unique pk, value(join between pk and name), objtype and color.

     User access will be checking on view permissions, laboratory and organization.

     Priority search level:
     1 - Object
     2 - Shelf Object
     3 - Shelf
     4 - Furniture
     5 - Laboratory Room

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
        result = {}
        if shelfobject:
            shelfobject = self.get_pk_list(shelfobject)
            shelfobject_list = ShelfObject.objects.filter(pk__in=shelfobject).using(
                settings.READONLY_DATABASE)

            if shelfobject_list:
                result = {
                    'shelfobject': shelfobject,
                    'shelf': list(shelfobject_list.values_list('shelf__pk', flat=True)),
                    'furniture': list(
                        shelfobject_list.values_list('shelf__furniture__pk',
                                                     flat=True)),
                    'labroom': list(
                        shelfobject_list.values_list('shelf__furniture__labroom__pk',
                                                     flat=True))
                }
        return result

    def get_object_param(self, object_param):
        result = {}
        if object_param:
            object_param_name = [obj.name for obj in object_param]
            object_list = Object.objects.filter(name__in=object_param_name).using(
                settings.READONLY_DATABASE)
            shelf = Shelf.objects.filter(shelfobject__object__in=object_list).using(
                settings.READONLY_DATABASE)
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
                                                     context={
                                                         "source_laboratory_id": lab_pk})

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
                    serializer.validated_data.get('object', []))
            }
        else:
            errors = serializer.errors

        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({'search_list': search_list}, status=status.HTTP_200_OK)
