from django.conf import settings
from django.contrib.admin.models import LogEntry, DELETION, CHANGE, ADDITION
from django.contrib.auth.decorators import permission_required
from django.db.models import Value, DateField, Q
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from djgentelella.objectmanagement import AuthAllPermBaseObjectManagement
from rest_framework import status, viewsets, mixins
from rest_framework.authentication import SessionAuthentication, BaseAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.utils import AllPermissionOrganizationByAction
from auth_and_perms.organization_utils import user_is_allowed_on_organization, \
    organization_can_change_laboratory
from laboratory.api import serializers, filterset
from laboratory.api.filterset import ProtocolFilterSet, LogEntryFilterSet
from laboratory.api.forms import CommentInformForm
from laboratory.api.serializers import ReservedProductsSerializer, \
    ReservationSerializer, \
    ReservedProductsSerializerUpdate, CommentsSerializer, \
    ShelfObjectSerialize, \
    LogEntryUserDataTableSerializer, ValidateEquipmentCharacteristicsSerializer, \
    ValidateMaterialCapacitySerializer
from laboratory.forms import ObservationShelfObjectForm
from laboratory.models import CommentInform, Inform, Protocol, OrganizationStructure, \
    Laboratory, InformsPeriod, ShelfObject, Shelf, Object, Catalog, EquipmentType, \
    MaterialCapacity
from laboratory.qr_utils import get_or_create_qr_shelf_object
from laboratory.shelfobject.forms import ShelfObjectStatusForm
from laboratory.utils import get_logentries_org_management, \
    get_pk_org_ancestors_decendants, PermissionByLaboratoryInOrganization, \
    organilab_logentry
from reservations_management.models import ReservedProducts


class ApiReservedProductsCRUD(APIView):
    def get_object(self, pk):
        try:
            return ReservedProducts.objects.get(pk=pk)
        except ReservedProducts.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        serializer = ReservedProductsSerializer(data=request.data)

        if serializer.is_valid():
            laboratory = get_object_or_404(Laboratory, pk=int(request.data['lab']))
            instance = serializer.save()
            instance.laboratory = laboratory
            instance.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        solicitud = self.get_object(pk)
        serializer = ReservedProductsSerializer(solicitud)
        return Response(serializer.data)

    def put(self, request, pk):
        solicitud = self.get_object(pk)
        serializer = ReservedProductsSerializerUpdate(solicitud, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        solicitud = self.get_object(pk)
        solicitud.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ApiReservationCRUD(APIView):
    def post(self, request):
        serializer = ReservationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentAPI(viewsets.ModelViewSet):
    perms = {
        "create": ["laboratory.add_commentinform"],
        "list": ['laboratory.view_commentinform'],
        "retrieve": ['laboratory.view_commentinform'],
        "update": ['laboratory.change_commentinform'],
        "destroy": ['laboratory.delete_commentinform'],
    }
    authentication_classes = [SessionAuthentication, BaseAuthentication]
    permission_classes = [IsAuthenticated, AllPermissionOrganizationByAction]
    queryset = CommentInform.objects.all()
    serializer_class = CommentsSerializer

    def get_comment(self, pk):
        try:
            return self.get_queryset().get(pk=pk)
        except CommentInform.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        serializer = CommentsSerializer(data=request.data)
        if serializer.is_valid():
            inform = Inform.objects.filter(pk=request.data['inform']).first()

            CommentInform.objects.create(
                created_by=request.user,
                comment=serializer.data['comment'],
                inform=inform
            )
            comments = self.get_queryset().filter(inform=inform).order_by('pk')
            template = render_to_string('laboratory/comment.html',
                                        {'comments': comments, 'user': request.user},
                                        request)
            return Response({'data': template}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        comments = queryset.none()

        if request.method == "GET":
            form = CommentInformForm(request.GET)

            if form.is_valid():
                comments = queryset.filter(
                    inform__pk=form.cleaned_data['inform']).order_by('pk')

        template = render_to_string('laboratory/comment.html',
                                    {'comments': comments, 'user': request.user},
                                    request)
        return Response({'data': template})

    def update(self, request, pk=None, *args, **kwargs):
        comment = None
        serializer = None
        if pk:
            serializer = CommentsSerializer(data=request.data)
            if serializer.is_valid():
                comment = CommentInform.objects.filter(pk=pk).first()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            if comment.created_by == self.request.user:
                comment.comment = request.data['comment']
                comment.save()
                template = render_to_string('laboratory/comment.html',
                                            {'comments': self.get_queryset().filter(
                                                inform=comment.inform).order_by('pk'),
                                             'user': request.user}, request)

                return Response({'data': template}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Only the user that create this observation can update"},
                    status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None, *args, **kwargs):
        if pk:
            comment = self.get_comment(pk)
            inform = comment.inform
            if comment.created_by == self.request.user:
                comment.delete()
                template = render_to_string('laboratory/comment.html', {
                    'comments': self.get_queryset().filter(inform=inform).order_by(
                        'pk'), 'user': request.user}, request)

                return Response({'data': template}, status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ProtocolViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ProtocolDataTableSerializer
    queryset = Protocol.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['name', 'short_description']
    filterset_class = ProtocolFilterSet
    ordering_fields = ['pk']
    ordering = ('pk',)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        lab_pk = self.request.GET.get('lab_pk', None)
        if lab_pk:
            queryset = queryset.filter(laboratory__pk=lab_pk)
        else:
            queryset = queryset.none()
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {'data': data, 'recordsTotal': Protocol.objects.count(),
                    'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}
        return Response(self.get_serializer(response).data)


class LogEntryViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.LogEntryDataTableSerializer
    queryset = LogEntry.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['object_repr', 'action_flag']
    filterset_class = LogEntryFilterSet
    ordering_fields = ['pk']
    ordering = ('pk',)
    can_use_inactive_organization = True

    def get_queryset(self):
        filters = {}
        org = self.request.GET.get('org_pk', None)
        qr_obj = self.request.GET.get('qr_obj', None)
        queryset = self.queryset.none()

        if not qr_obj:
            log_entries = get_logentries_org_management(self, org)
            filters.update({'pk__in': log_entries})
        else:
            if qr_obj.isnumeric():
                self.serializer_class = LogEntryUserDataTableSerializer
                qr_obj = int(qr_obj)
                detail = [
                    "[{'changed': {'fields': ['Login', %d]}}]" % (qr_obj),
                    "[{'added': {'fields': ['Register', %d]}}]" % (qr_obj)
                ]

                filters.update({
                    'action_flag__in': [1, 2],
                    'content_type__app_label': 'auth',
                    'content_type__model': 'user',
                    'change_message__in': detail
                })

        if filters:
            queryset = self.queryset.filter(**filters).distinct()

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {'data': data, 'recordsTotal': LogEntry.objects.count(),
                    'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}
        return Response(self.get_serializer(response).data)


class InformViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.InformDataTableSerializer
    queryset = Inform.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['name', 'creation_date', ]  # for the global search
    filterset_class = filterset.InformFilterSet
    ordering_fields = ['creation_date']
    ordering = ('-creation_date',)  # default order

    def get_queryset(self):
        period = self.request.GET.get('period', None)
        if not period:
            return self.queryset.none()
        period = get_object_or_404(InformsPeriod, pk=period)
        queryset = super().get_queryset().filter(
            pk__in=period.informs.values_list('pk', flat=True),
            organization=self.organization)
        queryset = queryset.annotate(
            start_application_date=Value(period.start_application_date, DateField()),
            close_application_date=Value(period.close_application_date, DateField())
        )
        return queryset

    def retrieve(self, request, pk, **kwargs):
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {'data': data, 'recordsTotal': Inform.objects.count(),
                    'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}
        return Response(self.get_serializer(response).data)


class ShelfObjectAPI(APIView):
    def get_object(self, pk):
        try:
            return ShelfObject.objects.filter(shelf__pk=pk)
        except ShelfObject.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, request, org_pk):
        solicitud = self.get_object(request.GET['shelf'])
        serializer = ShelfObjectSerialize(solicitud, context={'org_pk': org_pk},
                                          many=True)
        return Response(serializer.data)


class ShelfObjectGraphicAPI(APIView):
    def get(self, request):
        queryset = ShelfObject.objects.filter(shelf__pk=request.GET['shelf'])
        labels = []
        data = []
        if queryset:
            self.show_chart = True
            for obj in queryset:
                data.append(obj.quantity)
                labels.append(obj.object.name)

        return Response({'labels': labels, 'data': data})


@method_decorator(permission_required('laboratory.delete_shelf'), name='dispatch')
class ShelfList(APIView):
    def post(self, request):
        serializer = serializers.ShelfPkList(data=request.data)
        if serializer.is_valid(raise_exception=True):
            shelfs = Shelf.objects.filter(pk__in=serializer.data['shelfs'])
            data = render_to_string(
                template_name="laboratory/components/shelfdetail.html",
                context={'shelfs': shelfs}, request=request)
        return Response({'data': data})


@permission_required('laboratory.view_shelfobject')
def ShelfObjectObservationView(request, org_pk, lab_pk, pk):
    template = 'laboratory/shelfobject/shelfobject_observations.html'
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
    laboratory = get_object_or_404(Laboratory.objects.using(settings.READONLY_DATABASE),
                                   pk=lab_pk)
    user_is_allowed_on_organization(request.user, organization)
    organization_can_change_laboratory(laboratory, organization, raise_exec=True)
    shelfobject = get_object_or_404(
        ShelfObject.objects.using(settings.READONLY_DATABASE), pk=pk)
    qr, url = get_or_create_qr_shelf_object(request, shelfobject, org_pk, lab_pk)
    status_form = ShelfObjectStatusForm(org_pk=org_pk)
    observation_form = ObservationShelfObjectForm()
    return render(request, template, {'org_pk': org_pk,
                                      'laboratory': lab_pk,
                                      'object': shelfobject,
                                      'observation_form': observation_form,
                                      'status_form': status_form,
                                      'qr': qr,
                                      'pk': pk})


class EquipmentManagementViewset(AuthAllPermBaseObjectManagement):
    serializer_class = {
        'list': serializers.EquipmentDataTableSerializer,
        'destroy': serializers.EquipmentSerializer,
        'create': serializers.ValidateEquipmentSerializer,
        'update': serializers.ValidateEquipmentSerializer
    }
    perms = {
        'list': ["laboratory.view_object"],
        'create': ["laboratory.add_object", "laboratory.view_object"],
        'update': ["laboratory.change_object", "laboratory.view_object"],
        'destroy': ["laboratory.delete_object", "laboratory.view_object"]
    }

    permission_classes = (PermissionByLaboratoryInOrganization,)

    queryset = Object.objects.filter(type=Object.EQUIPMENT)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['code', 'name']  # for the global search
    filterset_class = filterset.EquipmentFilter
    ordering_fields = ['code']
    ordering = ('code',)  # default order
    operation_type = ''
    org_pk, lab_pk, org = None, None, None

    def get_response_validate_data(self, equipment_serializer, equipment_ch_serializer):
        equipment_changed_data = list(
            equipment_serializer.validated_data.keys())
        equipment_ch_changed_data = list(
            equipment_ch_serializer.validated_data.keys())

        # Multiple response data
        response_data = equipment_serializer.data
        equipment_ch_data = equipment_ch_serializer.data

        # THIS ID SHOULDN'T REPLACE THE MAIN ID(EQUIPMENT OBJECT)
        del equipment_ch_data['id']
        response_data.update(equipment_ch_data)

        return response_data, equipment_changed_data, equipment_ch_changed_data

    def get_equipment_ch_serializer(self, instance, request, partial, lab_pk):
        if hasattr(instance, 'equipmentcharacteristics'):
            equipment_ch_instance = instance.equipmentcharacteristics
            equipment_ch_serializer = ValidateEquipmentCharacteristicsSerializer(
                equipment_ch_instance, data=request.data, partial=partial,
                context={"lab_pk": lab_pk})
        else:
            data = request.data
            data.update({"object": instance.pk})
            equipment_ch_serializer = ValidateEquipmentCharacteristicsSerializer(
                data=data, partial=partial, context={"lab_pk": lab_pk})

        return equipment_ch_serializer

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        filters = (Q(organization__in=get_pk_org_ancestors_decendants(self.request.user,
                                                                      self.org_pk),
                     is_public=True)
                   | Q(organization__pk=self.org_pk, is_public=False))

        return queryset.filter(filters).distinct()

    def create(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=self.org_pk)
        errors, response_data, headers = {}, {}, self.get_success_headers({})

        # Serializers
        equipment_serializer = self.get_serializer(data=request.data)
        equipment_ch_serializer = ValidateEquipmentCharacteristicsSerializer(
            data=request.data, context={"lab_pk": self.lab_pk})

        if equipment_serializer.is_valid():
            if equipment_ch_serializer.is_valid():
                instance = equipment_serializer.save()
                equipment_ch_serializer.save(object=instance)

                response_data, equipment_changed_data, equipment_ch_changed_data = self.get_response_validate_data(
                    equipment_serializer, equipment_ch_serializer)

                # Multiple headers
                headers = self.get_success_headers(response_data)

                # Log Entry Create Action
                organilab_logentry(request.user, instance, ADDITION, "equipment object",
                                   changed_data=equipment_changed_data,
                                   relobj=organization)

                if hasattr(instance, 'equipmentcharacteristics'):
                    organilab_logentry(request.user, instance, ADDITION,
                                       "equipment characteristics",
                                       changed_data=equipment_ch_changed_data,
                                       relobj=organization)

                return Response(response_data, status=status.HTTP_201_CREATED,
                                headers=headers)
            else:
                errors.update(equipment_ch_serializer.errors)
        else:
            errors.update(equipment_serializer.errors)
            if not equipment_ch_serializer.is_valid():
                errors.update(equipment_ch_serializer.errors)

        if errors:
            raise ValidationError(errors)

    def destroy(self, request, *args, **kwargs):
        # EquipmentCharacteristics has OnetoOne relation with Object(Equipment) -->
        # ON DELETE CASCADE
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=self.org_pk)
        instance = self.get_object()
        equipment_ch_instance = None

        if hasattr(instance, 'equipmentcharacteristics'):
            equipment_ch_instance = instance.equipmentcharacteristics

        destroy = super().destroy(request, *args, **kwargs)

        # Log Entry Destroy Action
        organilab_logentry(request.user, instance, DELETION, "equipment object",
                           relobj=organization)

        if equipment_ch_instance:
            organilab_logentry(request.user, equipment_ch_instance, DELETION,
                               "equipment characteristics",
                               relobj=organization)
        return destroy

    def update(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=self.org_pk)
        errors, response_data = {}, {}
        equipment_ch_action = CHANGE
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        equipment_serializer = self.get_serializer(instance, data=request.data,
                                                   partial=partial)
        equipment_ch_serializer = self.get_equipment_ch_serializer(
            instance, request, partial, self.lab_pk)

        if equipment_serializer.is_valid():
            if equipment_ch_serializer.is_valid():
                instance = equipment_serializer.save()
                equipment_ch = equipment_ch_serializer.save()

                if getattr(instance, '_prefetched_objects_cache', None):
                    # If 'prefetch_related' has been applied to a queryset, we need to
                    # forcibly invalidate the prefetch cache on the instance.
                    instance._prefetched_objects_cache = {}

                response_data, equipment_changed_data, equipment_ch_changed_data = self.get_response_validate_data(
                    equipment_serializer, equipment_ch_serializer)

                # Log Entry Update Action
                organilab_logentry(request.user, instance, CHANGE, "equipment object",
                                   changed_data=equipment_changed_data,
                                   relobj=organization)

                if not hasattr(instance, 'equipmentcharacteristics'):
                    equipment_ch_action = ADDITION

                organilab_logentry(request.user, equipment_ch, equipment_ch_action,
                                   "equipment characteristics",
                                   changed_data=equipment_ch_changed_data,
                                   relobj=organization)

            else:
                errors.update(equipment_ch_serializer.errors)
        else:
            errors.update(equipment_serializer.errors)
            if not equipment_ch_serializer.is_valid():
                errors.update(equipment_ch_serializer.errors)

        if errors:
            raise ValidationError(errors)

        return Response(response_data)

    def list(self, request, *args, **kwargs):
        self.org_pk = kwargs['org_pk']
        self.lab_pk = kwargs['lab_pk']
        return super().list(request, *args, **kwargs)


class InstrumentalFamilyManagementViewset(AuthAllPermBaseObjectManagement):
    serializer_class = {
        'list': serializers.InstrumentalFamilyDataTableSerializer,
        'destroy': serializers.InstrumentalFamilySerializer,
        'create': serializers.InstrumentalFamilySerializer,
        'update': serializers.InstrumentalFamilySerializer
    }
    perms = {
        'list': ["laboratory.view_catalog"],
        'create': ["laboratory.add_catalog", "laboratory.view_catalog"],
        'update': ["laboratory.change_catalog", "laboratory.view_catalog"],
        'destroy': ["laboratory.delete_catalog", "laboratory.view_catalog"]
    }

    permission_classes = (PermissionByLaboratoryInOrganization,)

    queryset = Catalog.objects.filter(key="instrumental_family")
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['id', 'description']  # for the global search
    filterset_class = filterset.InstrumentalFamilyFilter
    ordering_fields = ['description']
    ordering = ('id',)  # default order
    operation_type = ''
    org_pk, lab_pk, org = None, None, None

    def create(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        create = super().create(request, *args, **kwargs)
        if create.status_code == 201:
            if 'id' in create.data.keys():
                instance = get_object_or_404(Catalog.objects.using(
                    settings.READONLY_DATABASE), pk=create.data['id'])
                organilab_logentry(request.user, instance, ADDITION, "catalog",
                                   changed_data=["key", "description"])
        return create

    def perform_create(self, serializer):
        serializer.save(key="instrumental_family")

    def destroy(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        instance = self.get_object()
        organilab_logentry(request.user, instance, DELETION, "catalog")
        destroy = super().destroy(request, *args, **kwargs)
        return destroy

    def update(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        update = super().update(request, *args, **kwargs)
        instance = self.get_object()
        organilab_logentry(request.user, instance, CHANGE, "catalog",
                           changed_data=["key", "description"])
        return update

    def list(self, request, *args, **kwargs):
        self.org_pk = kwargs['org_pk']
        self.lab_pk = kwargs['lab_pk']
        return super().list(request, *args, **kwargs)


class EquipmentTypeManagementViewset(AuthAllPermBaseObjectManagement):
    serializer_class = {
        'list': serializers.EquipmentTypeDataTableSerializer,
        'destroy': serializers.EquipmentTypeSerializer,
        'create': serializers.EquipmentTypeSerializer,
        'update': serializers.EquipmentTypeSerializer
    }
    perms = {
        'list': ["laboratory.view_equipmenttype"],
        'create': ["laboratory.add_equipmenttype"],
        'update': ["laboratory.change_equipmenttype"],
        'destroy': ["laboratory.delete_equipmenttype"]
    }

    permission_classes = (PermissionByLaboratoryInOrganization,)

    queryset = EquipmentType.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['id', 'description', 'name']  # for the global search
    filterset_class = filterset.EquipmentTypeFilter
    ordering_fields = ['description', 'name']
    ordering = ('id',)  # default order
    operation_type = ''
    org_pk, lab_pk, org = None, None, None

    def create(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        organization = get_object_or_404(OrganizationStructure.objects.using(
            settings.READONLY_DATABASE), pk=self.org_pk)
        create = super().create(request, *args, **kwargs)

        if create.status_code == 201:
            if 'id' in create.data.keys():
                instance = get_object_or_404(EquipmentType.objects.using(
                    settings.READONLY_DATABASE), pk=create.data['id'])
                organilab_logentry(request.user, instance, ADDITION, "equipment type",
                                   changed_data=["name", "description"],
                                   relobj=organization)
        return create

    def destroy(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        instance = self.get_object()
        organization = get_object_or_404(OrganizationStructure.objects.using(
            settings.READONLY_DATABASE), pk=self.org_pk)

        delete_equipment_list = list(Object.objects.filter(type=Object.EQUIPMENT,
                                                           equipmentcharacteristics__equipment_type=instance).values_list(
            'pk', flat=True))

        organilab_logentry(request.user, instance, DELETION,
                           "equipment type",
                           relobj=organization)

        destroy = super().destroy(request, *args, **kwargs)
        equipment_list = Object.objects.filter(pk__in=delete_equipment_list)
        shelfobject_equipment_list = ShelfObject.objects.filter(
            object__in=equipment_list)

        for obj_equipment in equipment_list:
            organilab_logentry(request.user, obj_equipment, DELETION,
                               "equipment object",
                               relobj=organization)

        for shelfobj_equipment in shelfobject_equipment_list:
            organilab_logentry(request.user, shelfobj_equipment, DELETION,
                               "shelfobject equipment",
                               relobj=organization)

        equipment_list.delete()

        return destroy

    def update(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        organization = get_object_or_404(OrganizationStructure.objects.using(
            settings.READONLY_DATABASE), pk=self.org_pk)
        update = super().update(request, *args, **kwargs)
        instance = self.get_object()
        organilab_logentry(request.user, instance, CHANGE, "equipment type",
                           changed_data=["name", "description"],
                           relobj=organization)
        return update

    def list(self, request, *args, **kwargs):
        self.org_pk = kwargs['org_pk']
        self.lab_pk = kwargs['lab_pk']
        return super().list(request, *args, **kwargs)


class MaterialManagementViewset(AuthAllPermBaseObjectManagement):
    serializer_class = {
        'list': serializers.MaterialDataTableSerializer,
        'destroy': serializers.MaterialSerializer,
        'create': serializers.ValidateMaterialSerializer,
        'update': serializers.ValidateMaterialSerializer
    }
    perms = {
        'list': ["laboratory.view_object"],
        'create': ["laboratory.add_object", "laboratory.view_object"],
        'update': ["laboratory.change_object", "laboratory.view_object"],
        'destroy': ["laboratory.delete_object", "laboratory.view_object"]
    }

    permission_classes = (PermissionByLaboratoryInOrganization,)

    queryset = Object.objects.filter(type=Object.MATERIAL)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['code', 'name']  # for the global search
    filterset_class = filterset.MaterialFilter
    ordering_fields = ['code']
    ordering = ('code',)  # default order
    operation_type = ''
    org_pk, lab_pk, org = None, None, None

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        filters = (Q(organization__in=get_pk_org_ancestors_decendants(self.request.user,
                                                                      self.org_pk),
                     is_public=True)
                   | Q(organization__pk=self.org_pk, is_public=False))
        return queryset.filter(filters).distinct()

    def get_response_validate_data(self, material_serializer, material_ca_serializer):
        material_changed_data = list(
            material_serializer.validated_data.keys())
        material_ca_changed_data = list(
            material_ca_serializer.validated_data.keys())

        # Multiple response data
        response_data = material_serializer.data
        material_ca_data = material_ca_serializer.data

        # THIS ID SHOULDN'T REPLACE THE MAIN ID(EQUIPMENT OBJECT)
        del material_ca_data['id']
        response_data.update(material_ca_data)

        return response_data, material_changed_data, material_ca_changed_data

    def create(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=self.org_pk)
        errors, response_data, headers = {}, {}, self.get_success_headers({})

        # Serializers
        material_serializer = self.get_serializer(data=request.data)
        material_ca_serializer = ValidateMaterialCapacitySerializer(
            data=request.data, context={"lab_pk": self.lab_pk})

        if material_serializer.is_valid():
            if material_ca_serializer.is_valid():
                instance = material_serializer.save()
                material_ca_serializer.save(object=instance)

                response_data, material_changed_data, material_ca_changed_data = self.get_response_validate_data(
                    material_serializer, material_ca_serializer)

                # Multiple headers
                headers = self.get_success_headers(response_data)

                # Log Entry Create Action
                organilab_logentry(request.user, instance, ADDITION, "material object",
                                   changed_data=material_changed_data,
                                   relobj=organization)

                if hasattr(instance, 'materialcapacity'):
                    organilab_logentry(request.user, instance, ADDITION,
                                       "material capacity",
                                       changed_data=material_ca_changed_data,
                                       relobj=organization)

                return Response(response_data, status=status.HTTP_201_CREATED,
                                headers=headers)
            else:
                errors.update(material_ca_serializer.errors)
        else:
            errors.update(material_serializer.errors)
            if not material_ca_serializer.is_valid():
                errors.update(material_ca_serializer.errors)

        if errors:
            raise ValidationError(errors)

    def get_material_ca_serializer(self, instance, request, partial, lab_pk):
        data = request.data

        if hasattr(instance, 'materialcapacity'):
            data['object'] = instance.pk
            material_ca_instance = instance.materialcapacity
            material_ca_serializer = ValidateMaterialCapacitySerializer(
                material_ca_instance, data=data, partial=partial,
                context={"lab_pk": lab_pk})
        else:
            data.update({"object": instance.pk})
            material_ca_serializer = ValidateMaterialCapacitySerializer(
                data=data, partial=partial, context={"lab_pk": lab_pk})

        return material_ca_serializer

    def update(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=self.org_pk)
        errors, response_data = {}, {}
        material_ca_action = CHANGE
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        material_serializer = self.get_serializer(instance, data=request.data,
                                                   partial=partial)
        material_ca_serializer = self.get_material_ca_serializer(
            instance, request, partial, self.lab_pk)

        if material_serializer.is_valid():
            if material_ca_serializer.is_valid():
                instance = material_serializer.save()
                material_ca = material_ca_serializer.save()

                if getattr(instance, '_prefetched_objects_cache', None):
                    # If 'prefetch_related' has been applied to a queryset, we need to
                    # forcibly invalidate the prefetch cache on the instance.
                    instance._prefetched_objects_cache = {}

                response_data, material_changed_data, material_ca_changed_data = self.get_response_validate_data(
                    material_serializer, material_ca_serializer)

                # Log Entry Update Action
                organilab_logentry(request.user, instance, CHANGE, "material object",
                                   changed_data=material_changed_data,
                                   relobj=organization)

                if not hasattr(instance, 'materialcapacity'):
                    material_ca_action = ADDITION

                organilab_logentry(request.user, material_ca, material_ca_action,
                                   "material capacity",
                                   changed_data=material_ca_changed_data,
                                   relobj=organization)

            else:
                errors.update(material_ca_serializer.errors)
        else:
            errors.update(material_serializer.errors)
            if not material_ca_serializer.is_valid():
                errors.update(material_ca_serializer.errors)

        if errors:
            raise ValidationError(errors)

        return Response(response_data)

    def destroy(self, request, *args, **kwargs):
        # MaterialCapacity has OnetoOne relation with Object(Material) -->
        # ON DELETE CASCADE
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=self.org_pk)
        instance = self.get_object()
        material_ca_instance = instance.materialcapacity

        if hasattr(instance, 'materialcapacity'):
            instance.materialcapacity.delete()
        destroy = super().destroy(request, *args, **kwargs)

        # Log Entry Destroy Action
        organilab_logentry(request.user, instance, DELETION, "material object",
                           relobj=organization)

        if material_ca_instance:
            organilab_logentry(request.user, material_ca_instance, DELETION,
                               "material capacity",
                               relobj=organization)
        return destroy

    def list(self, request, *args, **kwargs):
        self.org_pk = kwargs['org_pk']
        self.lab_pk = kwargs['lab_pk']
        return super().list(request, *args, **kwargs)
