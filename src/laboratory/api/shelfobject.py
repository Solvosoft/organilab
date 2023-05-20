import json

from django.conf import settings
from django.contrib.admin.models import CHANGE, ADDITION, DELETION
from django.http import JsonResponse
from django.template.loader import render_to_string
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
from laboratory.api import serializers, views
from laboratory.api.serializers import ShelfLabViewSerializer, ReservedProductsSerializer
from laboratory.logsustances import log_object_change
from laboratory.models import OrganizationStructure, \
    ShelfObject, Laboratory
from laboratory.models import OrganizationStructure, ShelfObject, Laboratory, TranferObject
from laboratory.models import REQUESTED
from laboratory.shelfobject.serializers import AddShelfObjectSerializer, SubstractShelfObjectSerializer, \
    ShelfObjectDeleteSerializer, TransferOutShelfObjectSerializer, TransferObjectDataTableSerializer, \
    ShelfObjectDetailSerializer, ShelfObjectObservationSerializer, ShelfObjectObservationDataTableSerializer
from laboratory.shelfobject.utils import save_shelf_object, get_clean_shelfobject_data, status_shelfobject, \
    validate_reservation_dates
from laboratory.utils import organilab_logentry
from presentation.models import QRModel


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


class ShelfObjectViewSet(viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    permissions_by_endpoint = {
        "transfer_out": ["laboratory.add_tranferobject", "laboratory.view_shelfobject"], 
        "transfer_in": ["laboratory.add_shelfobject", "laboratory.change_shelfobject", 
                        "laboratory.change_transferobject", "laboratory.view_transferobject"],
        "transfer_available_list": ["laboratory.view_tranferobject"],
        "create_shelfobject": [],
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

    @action(detail=False, methods=['post'])
    def fill_increase_shelfobject(self, request, org_pk, lab_pk, **kwargs):
        """
        Marcela
        :param request:
        :param org_pk:
        :param lab_pk:
        :param kwargs:
        :return:
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "fill_increase_shelfobject")
        self.serializer_class = AddShelfObjectSerializer
        serializer = self.serializer_class(data=request.data)
        errors = {'amount': [_('The quantity is more than the shelf has')]}
        status_code = status.HTTP_200_OK
        changed_data = ["amount"]

        if serializer.is_valid():
            bill, amount, shelfobject, provider = get_clean_shelfobject_data(serializer, changed_data, lab_pk)
            shelf = shelfobject.shelf

            if shelf.discard:
                total = shelf.get_total_refuse()
                new_total = total + amount
                if shelf.quantity >= new_total or shelf.quantity == -1:
                    status_code = save_shelf_object(shelfobject, request.user, shelfobject.pk, amount, provider, bill,
                                                    changed_data)
                else:
                    errors.update({'amount': [_('The quantity is much larger than the shelf limit %(limit)s')]})
            else:
                status_shelf_obj = status_shelfobject(shelfobject, shelf, amount)

                if status_shelf_obj:
                    status_code = save_shelf_object(shelfobject, request.user, shelfobject.pk, amount, provider, bill,
                                                    changed_data)
        else:
            errors = serializer.errors

        if status_code == 201:
            return Response(status=status_code)
        return Response(errors, status=status_code)

    @action(detail=False, methods=['post'])
    def fill_decrease_shelfobject(self, request, org_pk, lab_pk, **kwargs):
        """
        Marcela
        :param request:
        :param org_pk:
        :param lab_pk:
        :param kwargs:
        :return:
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "fill_decrease_shelfobject")
        self.serializer_class = SubstractShelfObjectSerializer
        serializer = self.serializer_class(data=request.data)
        errors = {'discount': [_('The amount to be subtracted is more than the shelf has')]}
        status_code = status.HTTP_200_OK
        changed_data = ["discount"]

        if serializer.is_valid():
            shelfobject = get_object_or_404(ShelfObject, pk=serializer.data['shelf_object'])
            old = shelfobject.quantity
            discount = serializer.data['discount']
            description = serializer.data.get('description', '')

            if description:
                changed_data.append("description")

            if old >= discount:
                new = old - discount
                shelfobject.quantity = new
                shelfobject.save()
                log_object_change(request.user, shelfobject.pk, shelfobject, old, new, description, 2, "Substract",
                                  create=False)
                organilab_logentry(request.user, shelfobject, CHANGE, 'shelfobject', changed_data=changed_data)
                status_code = status.HTTP_201_CREATED
        else:
            errors = serializer.errors

        if status_code == 201:
            return Response(status=status_code)
        return Response(errors, status=status_code)

    @action(detail=False, methods=['post'])
    def reserve(self, request, org_pk, lab_pk, **kwargs):
        """
        Marcela
        :param request:
        :param org_pk:
        :param lab_pk:
        :param kwargs:
        :return:
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "reserve")
        self.serializer_class = ReservedProductsSerializer
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            initial_date = serializer.validated_data['initial_date']
            final_date = serializer.validated_data['final_date']
            validate_dates, errors_dates = validate_reservation_dates(initial_date, final_date)
            if validate_dates:
                laboratory = get_object_or_404(Laboratory, pk=lab_pk)
                organization = get_object_or_404(OrganizationStructure, pk=org_pk)
                instance = serializer.save()
                instance.laboratory = laboratory
                instance.organization = organization
                instance.user = request.user
                instance.created_by = request.user
                instance.save()
                return Response(status=status.HTTP_201_CREATED)
            else:
                errors = errors_dates
        else:
            errors = serializer.errors
        return Response(errors, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def details(self, request, org_pk, lab_pk, pk, **kwargs):
        """
        Daniel
        :param request:
        :param org_pk:
        :param lab_pk:
        :param kwargs:
        :return:
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "detail")
        queryset = get_object_or_404(ShelfObject, pk=pk)
        serializer = ShelfObjectDetailSerializer(queryset)
        qr = QRModel.objects.get(content_type__app_label=queryset._meta.app_label,
                                 object_id=queryset.id,
                                 organization=org_pk,
                                 content_type__model= queryset._meta.model_name)
        context = {'object': serializer.data, 'org_pk': org_pk, 'lab_pk': lab_pk}
        if qr:
            image = qr.b64_image
            context['qr'] = image
        render_str = render_to_string('laboratory/shelfobject/detail_modal.html', context)
        return JsonResponse({'detail': render_str})

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
        :param lab_pk: pk of the laboratory being queried
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
        return Response(self.get_serializer(response_data).data)
        
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

    @action(detail=True, methods=['get'])
    def list_comments(self, request, org_pk, lab_pk, pk, **kwargs):
        """
        Daniel
        :param request:
        :param org_pk:
        :param lab_pk:
        :param kwargs:
        :return:
        """
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "list_comments")
        shelf_object = get_object_or_404(ShelfObject, pk=pk)
        self.serializer_class = ShelfObjectObservationDataTableSerializer
        self.pagination_class = LimitOffsetPagination
        self.filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
        self.search_fields = ['action_taken', 'description']
        self.ordering_fields = ['action_taken']
        self.ordering = ('action_taken',)
        self.queryset = shelf_object.shelfobjectobservation_set.all()
        queryset = self.filter_queryset(self.queryset)
        data = self.paginate_queryset(queryset)
        response_data = {'data': data, 'recordsTotal': self.queryset.count(),
                         'recordsFiltered': self.queryset.count(),
                         'draw': self.request.query_params.get('draw', 1)}

        return Response(self.get_serializer(response_data).data)

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

"""
- Búsqueda e interfaz gráfica Marta 
- Marce Agregar columnas a la tabla  (Tipo de ShelfObject, Sustance)
- Kendric Edit shelf para poner el -1 como infinito

"""