from django.conf import settings
from django.contrib.admin.models import CHANGE, ADDITION, DELETION
from django.http import JsonResponse
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

from auth_and_perms.organization_utils import user_is_allowed_on_organization, organization_can_change_laboratory
from laboratory import utils
from laboratory.api import serializers
from laboratory.api.serializers import ShelfLabViewSerializer
from laboratory.logsustances import log_object_change
from laboratory.models import Catalog
from laboratory.models import OrganizationStructure, ShelfObject, Laboratory, TranferObject
from laboratory.models import REQUESTED
from laboratory.shelfobject import serializers as shelfobject_serializers
from laboratory.shelfobject.serializers import IncreaseShelfObjectSerializer, DecreaseShelfObjectSerializer, \
    ReserveShelfObjectSerializer
from laboratory.shelfobject.serializers import TransferObjectDenySerializer, ShelfObjectContainerSerializer, \
    ShelfObjectLimitsSerializer, ShelfObjectStatusSerializer, ShelfObjectDeleteSerializer, \
    TransferOutShelfObjectSerializer, TransferObjectDataTableSerializer, ContainerShelfObjectSerializer
from laboratory.shelfobject.utils import save_shelf_object, status_shelfobject
from laboratory.utils import organilab_logentry
from presentation.utils import update_qr_instance


class ShelfObjectTableViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ShelfObjectTableSerializer
    queryset = ShelfObject.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['name', 'last_update', ]  # for the global search
    filterset_class = serializers.ShelfObjectFilterSet
    ordering_fields = ['last_update']
    ordering = ('-last_update',)  # default order

    def get_queryset(self):
        if not self.data['shelf'] :
            return self.queryset.none()
        return self.queryset.filter(
            in_where_laboratory=self.laboratory,
            shelf=self.data['shelf']

        )

    def list(self, request, org_pk, lab_pk, **kwargs):
        self.organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
        self.laboratory = get_object_or_404(Laboratory.objects.using(settings.READONLY_DATABASE), pk=lab_pk)
        user_is_allowed_on_organization(request.user, self.organization)
        organization_can_change_laboratory(self.laboratory, self.organization, raise_exec= True)
        validate_serializer = ShelfLabViewSerializer(data=request.GET, laboratory=self.laboratory)
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
        self.context=context

    def _build_qr(self, shelfobject):
        schema = self.context['request'].scheme + "://"
        domain = schema + self.context['request'].get_host()
        url = domain + reverse('laboratory:rooms_list', kwargs={"org_pk": self.context['organization'],
                                                                "lab_pk": self.context['laboratory']})
        url = url + "?labroom=%d&furniture=%d&shelf=%d&shelfobject=%d" % \
              (shelfobject.shelf.furniture.labroom.pk, shelfobject.shelf.furniture.pk, shelfobject.shelf.pk,
               shelfobject.pk)

        update_qr_instance(url, shelfobject, self.context['organization'])
        shelfobject.shelf_object_url = url

    def create_shelfobject_container(self, data):
        serializer= ShelfObjectContainerSerializer(data=data)
        if serializer.is_valid():
            container = serializer.save(creator=self.context['request'].user)
            utils.organilab_logentry(self.context['request'].user, container, ADDITION,
                                         changed_data=['object','shelfobject'], relobj=self.context['laboratory'])

    def create_reactive(self, serializer, limits_serializer):
        shelfobject = serializer.save()
        shelfobject.creator = self.context['request'].user
        shelfobject.in_where_laboratory_id = self.context['laboratory']
        shelfobject.limits= limits_serializer.save()
        shelfobject.save()
        self._build_qr(shelfobject)
        shelfobject.save()
        log_object_change(self.context['request'].user, self.context['laboratory'], shelfobject, 0,
                          shelfobject.quantity, '', 0, "Create",
                          create=True)
        utils.organilab_logentry(self.context['request'].user, shelfobject, ADDITION,
                                 changed_data=None, relobj=self.context['laboratory'])
        self.create_shelfobject_container(data={'shelf_object':shelfobject.pk,
                                                'container': self.context['request'].data['container']})

        return shelfobject

    def create_refuse_reactive(self, serializer, limits_serializer):
        shelfobject = serializer.save(
            creator=self.context['request'].user,
            in_where_laboratory_id=self.context['laboratory']
        )
        shelfobject.limits = limits_serializer.save()
        self._build_qr(shelfobject)
        shelfobject.save()
        log_object_change(self.context['request'].user, self.context['laboratory'], shelfobject, 0,
                          shelfobject.quantity, '', 0, "Create",
                          create=True)
        utils.organilab_logentry(self.context['request'].user, shelfobject, ADDITION,
                                 changed_data=None, relobj=self.context['laboratory'])
        self.create_shelfobject_container(data={'shelf_object': shelfobject.pk,
                                                'container': self.context['request'].data['container']})

        return shelfobject

    def create_material(self, serializer, limits_serializer):
        shelfobject = serializer.save()
        shelfobject.creator = self.context['request'].user
        shelfobject.in_where_laboratory_id = self.context['laboratory']
        shelfobject.save()
        shelfobject.limits= limits_serializer.save()
        self._build_qr(shelfobject)
        shelfobject.save()
        log_object_change(self.context['request'].user, self.context['laboratory'], shelfobject, 0,
                          shelfobject.quantity, '', 0, "Create",
                          create=True)
        utils.organilab_logentry(self.context['request'].user, shelfobject, ADDITION,
                                 changed_data=None, relobj=self.context['laboratory'])
        return shelfobject

    def create_refuse_material(self, serializer,limits_serializer):
        shelfobject = serializer.save()
        shelfobject.creator = self.context['request'].user
        shelfobject.in_where_laboratory_id = self.context['laboratory']
        shelfobject.save()
        shelfobject.limits= limits_serializer.save()
        self._build_qr(shelfobject)
        shelfobject.save()
        log_object_change(self.context['request'].user, self.context['laboratory'], shelfobject, 0,
                          shelfobject.quantity, '', 0, "Create",
                          create=True)
        utils.organilab_logentry(self.context['request'].user, shelfobject, ADDITION,
                                 changed_data=None, relobj=self.context['laboratory'])
        return shelfobject

    def create_equipment(self, serializer,limits_serializer):
        shelfobject = serializer.save()
        shelfobject.creator = self.context['request'].user
        shelfobject.in_where_laboratory_id = self.context['laboratory']
        shelfobject.save()
        self._build_qr(shelfobject)
        shelfobject.save()
        shelfobject.limits= limits_serializer.save()
        log_object_change(self.context['request'].user, self.context['laboratory'], shelfobject, 0,
                          shelfobject.quantity, '', 0, "Create",
                          create=True)
        utils.organilab_logentry(self.context['request'].user, shelfobject, ADDITION,
                                 changed_data=None, relobj=self.context['laboratory'])
        return shelfobject

    def create_refuse_equipement(self, serializer,limits_serializer):
        shelfobject = serializer.save()
        shelfobject.creator = self.context['request'].user
        shelfobject.in_where_laboratory_id = self.context['laboratory']
        shelfobject.save()
        shelfobject.limits= limits_serializer.save()
        self._build_qr(shelfobject)
        shelfobject.save()
        log_object_change(self.context['request'].user, self.context['laboratory'], shelfobject, 0,
                          shelfobject.quantity, '', 0, "Create",
                          create=True)
        utils.organilab_logentry(self.context['request'].user, shelfobject, ADDITION,
                                 changed_data=None, relobj=self.context['laboratory'])
        return shelfobject


class ShelfObjectViewSet(viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    permissions_by_endpoint = {
        "transfer_out": ["laboratory.add_tranferobject", "laboratory.view_shelfobject", "laboratory.change_shelfobject"], 
        "transfer_in": ["laboratory.add_shelfobject", "laboratory.change_shelfobject", "laboratory.view_shelfobject",
                        "laboratory.change_tranferobject", "laboratory.view_tranferobject"],
        "transfer_available_list": ["laboratory.view_tranferobject"],
        "transfer_in_deny": ["laboratory.view_tranferobject", "laboratory.delete_tranferobject"],
         "create_shelfobject": ["laboratory.add_shelfobject"],
        "fill_increase_shelfobject": ["laboratory.change_shelfobject"],
        "fill_decrease_shelfobject": ["laboratory.change_shelfobject"],
        "reserve": ["reservations_management.add_reservedproducts"],
        "detail": ["laboratory.view_shelfobject"],
        "tag": [],
        "detail_pdf": [],
        "delete": ["laboratory.delete_shelfobject"],
        "chart_graphic": [],
        "create_comments": [],
        "list_comments": [],
        "create_status": ["laboratory.add_catalog"],
        "update_status": [],
        "move_shelfobject_to_shelf": [],
        "shelf_availability_information": [],
    }
    

    # This is not an API endpoint 
    def _check_permission_on_laboratory(self, request, org_pk, lab_pk, method_name):
        if request.user.has_perms(self.permissions_by_endpoint[method_name]):  # user can actually perform the requested action, then check object access permissions
            self.organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
            self.laboratory = get_object_or_404(Laboratory.objects.using(settings.READONLY_DATABASE), pk=lab_pk)
            user_is_allowed_on_organization(request.user, self.organization)
            organization_can_change_laboratory(self.laboratory, self.organization, raise_exec= True)
        else:
            raise PermissionDenied()

    def _get_create_shelfobject_serializer(self, request, org_pk, lab_pk):
        name = ""
        serializer=shelfobject_serializers.ValidateShelfSerializer(data=request.data,
                                                                   context={"org_pk": org_pk, "lab_pk": lab_pk})
        serializer.is_valid(raise_exception=True)
        key_name=serializer.get_key_descriptor()
        methods_class=ShelfObjectCreateMethods(context={
            "organization": org_pk,
            "laboratory": lab_pk,
            "request": request
        })
        serializers_class={
            "reactive": {'serializer': shelfobject_serializers.ReactiveShelfObjectSerializer,
                 'method': methods_class.create_reactive},
            "reactive_refuse": {'serializer': shelfobject_serializers.ReactiveRefuseShelfObjectSerializer,
                 'method': methods_class.create_refuse_reactive},
            "material": {'serializer': shelfobject_serializers.MaterialShelfObjectSerializer,
                 'method': methods_class.create_material},
            "material_refuse": {'serializer': shelfobject_serializers.MaterialRefuseShelfObjectSerializer,
                 'method': methods_class.create_refuse_material},
            "equipment": {'serializer': shelfobject_serializers.EquipmentShelfObjectSerializer,
                 'method': methods_class.create_equipment},
            "equipment_refuse": {'serializer': shelfobject_serializers.EquipmentRefuseShelfObjectSerializer,
                 'method': methods_class.create_refuse_equipement},
        }
        return serializers_class[key_name], key_name

    @action(detail=False, methods=['post'])
    def create_shelfobject(self, request, org_pk, lab_pk, **kwargs):
        """
        Kendric
        :param request:
        :param org_pk:
        :param lab_pk:
        :param kwargs:
        :return:
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "create_shelfobject")
        self.serializer_class, keyname = self._get_create_shelfobject_serializer(request, org_pk, lab_pk)

        if keyname in ['reactive', 'reactive_refuse']:
            serializercontainer=ContainerShelfObjectSerializer(data=request.data)
            if not serializercontainer.is_valid():
                return JsonResponse({"errors": serializercontainer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class['serializer'](data=request.data, context={"org_pk": org_pk, "lab_pk": lab_pk})
        limit_serializer=ShelfObjectLimitsSerializer(data=request.data)

        errors={}
        if serializer.is_valid():
            if limit_serializer.is_valid(raise_exception=True):
                self.serializer_class['method'](serializer, limit_serializer)
                return Response({"detail": _("The creation was performed successfully.")}, status=status.HTTP_201_CREATED)
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
        :param request: http request
        :param org_pk: organization related user permissions
        :param lab_pk: laboratory related to shelfobject and user permissions
        :param kwargs: extra params
        :return: increase shelf object quantity, return success o error message
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "fill_increase_shelfobject")
        self.serializer_class = IncreaseShelfObjectSerializer
        serializer = self.serializer_class(data=request.data, context={"source_laboratory_id": lab_pk})
        errors = {}
        provider = None

        if serializer.is_valid():
            shelfobject = serializer.validated_data['shelf_object']
            shelf = shelfobject.shelf

            if 'provider' in serializer.validated_data:
                provider = serializer.validated_data['provider']

            changed_data = list(serializer.validated_data.keys())
            bill = serializer.validated_data.get('bill', '')
            amount = serializer.validated_data['amount']
            laboratory = get_object_or_404(Laboratory, pk=lab_pk)

            if shelf.discard:
                total = shelf.get_total_refuse()
                new_total = total + amount
                if shelf.quantity >= new_total or shelf.quantity == -1:
                    save_shelf_object(shelfobject, request.user, shelfobject.pk, amount, provider, bill, changed_data, laboratory)
                else:
                    errors['amount'] = [_('The quantity is much larger than the shelf limit %(limit)s')]
            else:
                status_shelf_obj = status_shelfobject(shelfobject, shelf, amount)

                if status_shelf_obj:
                    save_shelf_object(shelfobject, request.user, shelfobject.pk, amount, provider, bill, changed_data, laboratory)
                else:
                    errors['amount'] = [_('The quantity is more than the shelf has')]
        else:
            errors = serializer.errors

        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({"detail": _("Shelf object substract was performed successfully.")},
                            status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def fill_decrease_shelfobject(self, request, org_pk, lab_pk, **kwargs):
        """
        :param request: http request
        :param org_pk: organization related user permissions
        :param lab_pk: laboratory related to shelfobject and user permissions
        :param kwargs: extra params
        :return: decrease shelf object quantity, return success o error message
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "fill_decrease_shelfobject")
        self.serializer_class = DecreaseShelfObjectSerializer
        serializer = self.serializer_class(data=request.data, context={"source_laboratory_id": lab_pk})
        errors = {}

        if serializer.is_valid():
            shelfobject = serializer.validated_data['shelf_object']
            old = shelfobject.quantity
            discount = serializer.validated_data['discount']
            description = serializer.validated_data.get('description', '')
            changed_data = list(serializer.validated_data.keys())
            laboratory = get_object_or_404(Laboratory, pk=lab_pk)

            if old >= discount:
                new = old - discount
                shelfobject.quantity = new
                shelfobject.save()
                log_object_change(request.user, lab_pk, shelfobject, old, new, description, 2, "Substract", create=False)
                organilab_logentry(request.user, shelfobject, CHANGE, 'shelfobject', changed_data=changed_data, relobj=[laboratory, shelfobject])
            else:
                errors['discount'] = [_('The amount to be subtracted is more than the shelf has')]
        else:
            errors = serializer.errors

        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({"detail": _("Shelf object substract was performed successfully.")}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def reserve(self, request, org_pk, lab_pk, **kwargs):
        """
        :param request: http request
        :param org_pk: organization related to reserved product and user permissions
        :param lab_pk: laboratory related to reserved product and user permissions
        :param kwargs: extra params
        :return: save a reserved product instance, return success o error message
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "reserve")
        self.serializer_class = ReserveShelfObjectSerializer
        serializer = self.serializer_class(data=request.data, context={"source_laboratory_id": lab_pk})
        errors = {}
        changed_data = ["laboratory", "organization", "user", "created_by"]

        if serializer.is_valid():
            changed_data = changed_data + list(serializer.validated_data.keys())
            laboratory = get_object_or_404(Laboratory, pk=lab_pk)
            organization = get_object_or_404(OrganizationStructure, pk=org_pk)
            instance = serializer.save()
            instance.laboratory = laboratory
            instance.organization = organization
            instance.user = request.user
            instance.created_by = request.user
            instance.save()
            organilab_logentry(request.user, instance, ADDITION, 'reserved product', changed_data=changed_data, relobj=[laboratory, instance])
        else:
            errors = serializer.errors

        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse({"detail": _("Reservation was performed successfully.")}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def detail(self, request, org_pk, lab_pk, **kwargs):
        """
        Daniel
        :param request:
        :param org_pk:
        :param lab_pk:
        :param kwargs:
        :return:
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "detail")

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
        serializer = self.serializer_class(data=request.data, context={"source_laboratory_id": lab_pk})
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
                    creator=request.user
                )
                organilab_logentry(
                    request.user, transfer_obj, ADDITION, 'transferobject', 
                    changed_data=['object', 'laboratory_send', 'laboratory_received', 'quantity'], 
                    relobj=[transfer_obj, source_laboratory, target_laboratory]
                )
            else:
                errors["amount_to_transfer"] = [_("This value cannot be greater than the quantity available for the object.")]
        else:
            errors = serializer.errors

        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        
        return JsonResponse({"detail": _("The transfer out was performed successfully.")}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def transfer_in(self, request, org_pk, lab_pk, **kwargs):
        """
        Marta
        :param request:
        :param org_pk:
        :param lab_pk:
        :param kwargs:
        :return:
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "transfer_in")

    @action(detail=False, methods=['get'])
    def transfer_available_list(self, request, org_pk, lab_pk, **kwargs):
        """
        Returns the transfers that have the provided laboratory saved as laboratory_received, this for the ones that have not been approved yet.
        :param org_pk: pk of the organization being queried
        :param lab_pk: pk of the laboratory that can receive the transfer in
        :param kwargs: other extra params
        :return: JsonResponse with the transfer request information and the number of records
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "transfer_available_list")
        
        self.serializer_class = TransferObjectDataTableSerializer
        self.pagination_class = LimitOffsetPagination
        self.filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
        self.search_fields = ['object__object__name', 'quantity', 'laboratory_send__name', 'update_time', 'mark_as_discard']  # for the global search
        self.ordering_fields = ['object__object__name', 'quantity', 'laboratory_send__name', 'update_time', 'mark_as_discard']
        self.ordering = ('-update_time',)  # default order
        
        self.queryset = TranferObject.objects.filter(laboratory_received=lab_pk, status=REQUESTED)
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
        :param org_pk: pk of the organization being queried
        :param lab_pk: pk of the laboratory that can receive the transfer in
        :param kwargs: other extra params
        :return: JsonResponse with result information (success or error info) 
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "transfer_in_deny")
        serializer = TransferObjectDenySerializer(data=request.data, context={"laboratory_id": lab_pk})
        serializer.is_valid(raise_exception=True)
        utils.organilab_logentry(self.request.user, serializer.validated_data['transfer_object'], DELETION, relobj=self.laboratory)
        serializer.validated_data['transfer_object'].delete()
        return JsonResponse({'detail': _('The transfer in was denied successfully.')}, status=status.HTTP_200_OK)
        
        
    @action(detail=False, methods=['get'])
    def detail_pdf(self, request, org_pk, lab_pk, **kwargs):
        """
        Kendric
        :param request:
        :param org_pk:
        :param lab_pk:
        :param kwargs:
        :return:
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "detail_pdf")

    @action(detail=False, methods=['delete'])
    def delete(self, request, org_pk, lab_pk, **kwargs):
        """
        Daniel
        :param request:
        :param org_pk:
        :param lab_pk:
        :param kwargs:
        :return:
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "delete")
        serializer = ShelfObjectDeleteSerializer(data=request.data, context={"laboratory_id":self.laboratory.pk})
        serializer.is_valid(raise_exception=True)
        utils.organilab_logentry(self.request.user, serializer.validated_data['shelfobj'], DELETION, relobj=self.laboratory)
        serializer.validated_data['shelfobj'].delete()
        return JsonResponse({'detail': _('The item was deleted successfully')}, status=200)

    @action(detail=False, methods=['get'])
    def chart_graphic(self, request, org_pk, lab_pk, **kwargs):
        """
        Luis Z
            def get(self, request):
        queryset = ShelfObject.objects.filter(shelf__pk=request.GET['shelf'])
        labels = []
        data = []
        if queryset:
            self.show_chart = True
            for obj in queryset:
               data.append(obj.quantity)
               labels.append(obj.object.name)

        return Response({'labels':labels,'data':data})
        :return:
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "chart_graphic")


    @action(detail=False, methods=['post'])
    def create_comments(self, request, org_pk, lab_pk, **kwargs):
        """
        Daniel
        :param request:
        :param org_pk:
        :param lab_pk:
        :param kwargs:
        :return:
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "create_comments")
        pass

    @action(detail=False, methods=['post'])
    def list_comments(self, request, org_pk, lab_pk, **kwargs):
        """
        Daniel
        :param request:
        :param org_pk:
        :param lab_pk:
        :param kwargs:
        :return:
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "list_comments")
        pass

    @action(detail=False, methods=['put'])
    def update_status(self, request, org_pk, lab_pk, **kwargs):
        """
        Kendric
        :param request:
        :param org_pk:
        :param lab_pk:
        :param kwargs:
        :return:
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "update_status")
        pass

    @action(detail=False, methods=['put'])
    def move_shelfobject_to_shelf(self, request, org_pk, lab_pk, **kwargs):
        """
        Marcela
        :param request:
        :param org_pk:
        :param lab_pk:
        :param kwargs:
        :return:
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "move_shelfobject_to_shelf")
        pass

    @action(detail=False, methods=['get'])
    def shelf_availability_information(self, request, org_pk, lab_pk, **kwargs):
        """
        Marcela
        :param request:
        :param org_pk:
        :param lab_pk:
        :param kwargs:
        :return:
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "shelf_availability_information")
        pass

    @action(detail=False, methods=['post'])
    def create_status(self, request, org_pk, lab_pk, **kwargs):
        """
        Kendric
        :param request:
        :param org_pk:
        :param lab_pk:
        :param kwargs:
        :return:
        """
        """
            Se necesita agregar el permiso laboratory.add_catalog
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "create_shelfobject")

        self.serializer_class=ShelfObjectStatusSerializer
        serializer =self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
          Catalog.objects.create(key='shelfobject_status', description=serializer.data['description'])
          return JsonResponse({'detail': _('The item was created successfully')}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

"""
- Búsqueda e interfaz gráfica Marta 
- Marce Agregar columnas a la tabla  (Tipo de ShelfObject, Sustance)
- Kendric Edit shelf para poner el -1 como infinito

"""