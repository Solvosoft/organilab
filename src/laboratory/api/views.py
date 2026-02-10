import logging

from django.conf import settings
from django.contrib.admin.models import LogEntry, DELETION, CHANGE, ADDITION
from laboratory.utils import organilab_logentry
from django.contrib.auth.decorators import permission_required
from django.db.models import Value, DateField, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from djgentelella.objectmanagement import AuthAllPermBaseObjectManagement
from rest_framework import status, viewsets, mixins
from rest_framework.authentication import SessionAuthentication, BaseAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger("organilab")

from api.utils import AllPermissionOrganizationByAction
from auth_and_perms.organization_utils import (
    user_is_allowed_on_organization,
    organization_can_change_laboratory,
)
from laboratory.api import serializers, filterset

from laboratory.api.filterset import (
    ProtocolFilterSet,
    LogEntryFilterSet,
    ProviderFilter,
    ObjectFeatureFilter,
    ObjectFilter,
    ShelObjectReactiveFilter,
)

from laboratory.api.forms import CommentInformForm
from laboratory.api.serializers import (
    ReservedProductsSerializer,
    ReservationSerializer,
    ReservedProductsSerializerUpdate,
    CommentsSerializer,
    ShelfObjectSerialize,
    LogEntryUserDataTableSerializer,
    ValidateEquipmentCharacteristicsSerializer,
    ValidateReactiveCharacteristicsSerializer,
    GetReactiveLimitSerializer,
    ProviderSerializer,
    ProviderDataTableSerializer,
    ProviderValidateSerializer,
    ObjectFeatureSerializer,
    ObjectFeatureDataTableSerializer,
    ObjectFeatureValidateSerializer,
    ObjectSerializer,
    ObjectDataTableSerializer,
    ObjectValidateSerializer,
)
from laboratory.forms import ObservationShelfObjectForm
from laboratory.models import (
    CommentInform,
    Inform,
    Protocol,
    OrganizationStructure,
    Laboratory,
    InformsPeriod,
    ShelfObject,
    Shelf,
    Object,
    Catalog,
    EquipmentType,
    ReactiveLimit,
    LaboratoryProcess,
    Provider,
    ObjectFeatures,
)
from laboratory.qr_utils import get_or_create_qr_shelf_object
from laboratory.shelfobject.forms import ShelfObjectStatusForm
from laboratory.shelfobject.serializers import (
    IncreaseReactiveShelfObjectSerializer,
    DecreaseReactiveShelfObjectSerializer,
    ShelObjectReactiveDataTableSerializer,
)
from laboratory.shelfobject.utils import save_increase_decrease_shelf_object
from laboratory.utils import (
    get_logentries_org_management,
    get_pk_org_ancestors_decendants,
    PermissionByLaboratoryInOrganization,
    organilab_logentry,
)
from reservations_management.models import ReservedProducts
from rest_framework.exceptions import PermissionDenied


class ApiReservedProductsCRUD(APIView):
    def get_object(self, pk):
        try:
            return ReservedProducts.objects.get(pk=pk)
        except ReservedProducts.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        serializer = ReservedProductsSerializer(data=request.data)

        if serializer.is_valid():
            laboratory = get_object_or_404(Laboratory, pk=int(request.data["lab"]))
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
        "list": ["laboratory.view_commentinform"],
        "retrieve": ["laboratory.view_commentinform"],
        "update": ["laboratory.change_commentinform"],
        "destroy": ["laboratory.delete_commentinform"],
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
            inform = Inform.objects.filter(pk=request.data["inform"]).first()

            CommentInform.objects.create(
                created_by=request.user,
                comment=serializer.data["comment"],
                inform=inform,
            )
            comments = self.get_queryset().filter(inform=inform).order_by("pk")
            template = render_to_string(
                "laboratory/comment.html",
                {"comments": comments, "user": request.user},
                request,
            )
            return Response({"data": template}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        comments = queryset.none()

        if request.method == "GET":
            form = CommentInformForm(request.GET)

            if form.is_valid():
                comments = queryset.filter(
                    inform__pk=form.cleaned_data["inform"]
                ).order_by("pk")

        template = render_to_string(
            "laboratory/comment.html",
            {"comments": comments, "user": request.user},
            request,
        )
        return Response({"data": template})

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
                comment.comment = request.data["comment"]
                comment.save()
                template = render_to_string(
                    "laboratory/comment.html",
                    {
                        "comments": self.get_queryset()
                        .filter(inform=comment.inform)
                        .order_by("pk"),
                        "user": request.user,
                    },
                    request,
                )

                return Response({"data": template}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Only the user that create this observation can update"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None, *args, **kwargs):
        if pk:
            comment = self.get_comment(pk)
            inform = comment.inform
            if comment.created_by == self.request.user:
                comment.delete()
                template = render_to_string(
                    "laboratory/comment.html",
                    {
                        "comments": self.get_queryset()
                        .filter(inform=inform)
                        .order_by("pk"),
                        "user": request.user,
                    },
                    request,
                )

                return Response({"data": template}, status=status.HTTP_200_OK)
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
    search_fields = ["name", "short_description"]
    filterset_class = ProtocolFilterSet
    ordering_fields = ["pk"]
    ordering = ("pk",)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        lab_pk = self.request.GET.get("lab_pk", None)
        if lab_pk:
            queryset = queryset.filter(laboratory__pk=lab_pk)
        else:
            queryset = queryset.none()
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {
            "data": data,
            "recordsTotal": Protocol.objects.count(),
            "recordsFiltered": queryset.count(),
            "draw": self.request.GET.get("draw", 1),
        }
        return Response(self.get_serializer(response).data)


class LogEntryViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.LogEntryDataTableSerializer
    queryset = LogEntry.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["object_repr", "action_flag"]
    filterset_class = LogEntryFilterSet
    ordering_fields = ["pk"]
    ordering = ("pk",)
    can_use_inactive_organization = True

    def get_queryset(self):
        filters = {}
        org = self.request.GET.get("org_pk", None)
        qr_obj = self.request.GET.get("qr_obj", None)
        queryset = self.queryset.none()

        if not qr_obj:
            log_entries = get_logentries_org_management(self, org)
            filters.update({"pk__in": log_entries})
        else:
            if qr_obj.isnumeric():
                self.serializer_class = LogEntryUserDataTableSerializer
                qr_obj = int(qr_obj)
                detail = [
                    "[{'changed': {'fields': ['Login', %d]}}]" % (qr_obj),
                    "[{'added': {'fields': ['Register', %d]}}]" % (qr_obj),
                ]

                filters.update(
                    {
                        "action_flag__in": [1, 2],
                        "content_type__app_label": "auth",
                        "content_type__model": "user",
                        "change_message__in": detail,
                    }
                )

        if filters:
            queryset = self.queryset.filter(**filters).distinct()

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {
            "data": data,
            "recordsTotal": LogEntry.objects.count(),
            "recordsFiltered": queryset.count(),
            "draw": self.request.GET.get("draw", 1),
        }
        return Response(self.get_serializer(response).data)


class InformViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.InformDataTableSerializer
    queryset = Inform.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = [
        "name",
        "creation_date",
    ]  # for the global search
    filterset_class = filterset.InformFilterSet
    ordering_fields = ["creation_date"]
    ordering = ("-creation_date",)  # default order

    def get_queryset(self):
        period = self.request.GET.get("period", None)
        if not period:
            return self.queryset.none()
        period = get_object_or_404(InformsPeriod, pk=period)
        queryset = (
            super()
            .get_queryset()
            .filter(
                pk__in=period.informs.values_list("pk", flat=True),
                organization=self.organization,
            )
        )
        queryset = queryset.annotate(
            start_application_date=Value(period.start_application_date, DateField()),
            close_application_date=Value(period.close_application_date, DateField()),
        )
        return queryset

    def retrieve(self, request, pk, **kwargs):
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {
            "data": data,
            "recordsTotal": Inform.objects.count(),
            "recordsFiltered": queryset.count(),
            "draw": self.request.GET.get("draw", 1),
        }
        return Response(self.get_serializer(response).data)


class ShelfObjectAPI(APIView):
    def get_object(self, pk):
        try:
            return ShelfObject.objects.filter(shelf__pk=pk)
        except ShelfObject.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, request, org_pk):
        solicitud = self.get_object(request.GET["shelf"])
        serializer = ShelfObjectSerialize(
            solicitud, context={"org_pk": org_pk}, many=True
        )
        return Response(serializer.data)


class ShelfObjectGraphicAPI(APIView):
    def get(self, request):
        queryset = ShelfObject.objects.filter(shelf__pk=request.GET["shelf"])
        labels = []
        data = []
        if queryset:
            self.show_chart = True
            for obj in queryset:
                data.append(obj.quantity)
                labels.append(obj.object.name)

        return Response({"labels": labels, "data": data})


@method_decorator(permission_required("laboratory.delete_shelf"), name="dispatch")
class ShelfList(APIView):
    def post(self, request):
        serializer = serializers.ShelfPkList(data=request.data)
        if serializer.is_valid(raise_exception=True):
            shelfs = Shelf.objects.filter(pk__in=serializer.data["shelfs"])
            data = render_to_string(
                template_name="laboratory/components/shelfdetail.html",
                context={"shelfs": shelfs},
                request=request,
            )
        return Response({"data": data})


@permission_required("laboratory.view_shelfobject")
def ShelfObjectObservationView(request, org_pk, lab_pk, pk):
    template = "laboratory/shelfobject/shelfobject_observations.html"
    organization = get_object_or_404(
        OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
    )
    laboratory = get_object_or_404(
        Laboratory.objects.using(settings.READONLY_DATABASE), pk=lab_pk
    )
    user_is_allowed_on_organization(request.user, organization)
    organization_can_change_laboratory(laboratory, organization, raise_exec=True)
    shelfobject = get_object_or_404(
        ShelfObject.objects.using(settings.READONLY_DATABASE), pk=pk
    )
    qr, url = get_or_create_qr_shelf_object(request, shelfobject, org_pk, lab_pk)
    status_form = ShelfObjectStatusForm(org_pk=org_pk)
    observation_form = ObservationShelfObjectForm()
    return render(
        request,
        template,
        {
            "org_pk": org_pk,
            "laboratory": lab_pk,
            "object": shelfobject,
            "observation_form": observation_form,
            "status_form": status_form,
            "qr": qr,
            "pk": pk,
        },
    )


class EquipmentManagementViewset(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": serializers.EquipmentDataTableSerializer,
        "destroy": serializers.EquipmentSerializer,
        "create": serializers.ValidateEquipmentSerializer,
        "update": serializers.ValidateEquipmentSerializer,
    }
    perms = {
        "list": ["laboratory.view_object"],
        "create": ["laboratory.add_object", "laboratory.view_object"],
        "update": ["laboratory.change_object", "laboratory.view_object"],
        "destroy": ["laboratory.delete_object", "laboratory.view_object"],
    }

    permission_classes = (PermissionByLaboratoryInOrganization,)

    queryset = Object.objects.filter(type=Object.EQUIPMENT)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["code", "name", "synonym"]  # for the global search
    filterset_class = filterset.EquipmentFilter
    ordering_fields = ["code"]
    ordering = ("code",)  # default order
    operation_type = ""
    org_pk, lab_pk, org = None, None, None

    def get_response_validate_data(self, equipment_serializer, equipment_ch_serializer):
        equipment_changed_data = list(equipment_serializer.validated_data.keys())
        equipment_ch_changed_data = list(equipment_ch_serializer.validated_data.keys())
        # Multiple response data
        response_data = equipment_serializer.data
        equipment_ch_data = equipment_ch_serializer.data

        # THIS ID SHOULDN'T REPLACE THE MAIN ID(REACTIVE OBJECT)
        del equipment_ch_data["id"]
        response_data.update(equipment_ch_data)

        return response_data, equipment_changed_data, equipment_ch_changed_data

    def get_equipment_ch_serializer(self, instance, request, partial, lab_pk):
        if hasattr(instance, "equipmentcharacteristics"):
            equipment_ch_instance = instance.equipmentcharacteristics
            equipment_ch_serializer = ValidateEquipmentCharacteristicsSerializer(
                equipment_ch_instance,
                data=request.data,
                partial=partial,
                context={"lab_pk": lab_pk},
            )
        else:
            data = request.data
            data.update({"object": instance.pk})
            equipment_ch_serializer = ValidateEquipmentCharacteristicsSerializer(
                data=data, partial=partial, context={"lab_pk": lab_pk}
            )

        return equipment_ch_serializer

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        filters = Q(
            organization__in=get_pk_org_ancestors_decendants(
                self.request.user, self.org_pk
            ),
            is_public=True,
        ) | Q(organization__pk=self.org_pk, is_public=False)

        return queryset.filter(filters).distinct()

    def create(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=self.org_pk,
        )
        errors, response_data, headers = {}, {}, self.get_success_headers({})

        # Serializers
        equipment_serializer = self.get_serializer(data=request.data)
        equipment_ch_serializer = ValidateEquipmentCharacteristicsSerializer(
            data=request.data, context={"lab_pk": self.lab_pk}
        )

        if equipment_serializer.is_valid():
            if equipment_ch_serializer.is_valid():
                instance = equipment_serializer.save()
                equipment_ch_serializer.save(object=instance)

                response_data, equipment_changed_data, equipment_ch_changed_data = (
                    self.get_response_validate_data(
                        equipment_serializer, equipment_ch_serializer
                    )
                )

                # Multiple headers
                headers = self.get_success_headers(response_data)

                # Log Entry Create Action
                organilab_logentry(
                    request.user,
                    instance,
                    ADDITION,
                    "equipment object",
                    changed_data=equipment_changed_data,
                    relobj=organization,
                )

                if hasattr(instance, "equipmentcharacteristics"):
                    organilab_logentry(
                        request.user,
                        instance,
                        ADDITION,
                        "equipment characteristics",
                        changed_data=equipment_ch_changed_data,
                        relobj=organization,
                    )

                return Response(
                    response_data, status=status.HTTP_201_CREATED, headers=headers
                )
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
            pk=self.org_pk,
        )
        instance = self.get_object()
        equipment_ch_instance = None

        if hasattr(instance, "equipmentcharacteristics"):
            equipment_ch_instance = instance.equipmentcharacteristics

        destroy = super().destroy(request, *args, **kwargs)

        # Log Entry Destroy Action
        organilab_logentry(
            request.user, instance, DELETION, "equipment object", relobj=organization
        )

        if equipment_ch_instance:
            organilab_logentry(
                request.user,
                equipment_ch_instance,
                DELETION,
                "equipment characteristics",
                relobj=organization,
            )
        return destroy

    def update(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=self.org_pk,
        )
        errors, response_data = {}, {}
        equipment_ch_action = CHANGE
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        equipment_serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        equipment_ch_serializer = self.get_equipment_ch_serializer(
            instance, request, partial, self.lab_pk
        )

        if equipment_serializer.is_valid():
            if equipment_ch_serializer.is_valid():
                instance = equipment_serializer.save()
                equipment_ch = equipment_ch_serializer.save()

                if getattr(instance, "_prefetched_objects_cache", None):
                    # If 'prefetch_related' has been applied to a queryset, we need to
                    # forcibly invalidate the prefetch cache on the instance.
                    instance._prefetched_objects_cache = {}

                response_data, equipment_changed_data, equipment_ch_changed_data = (
                    self.get_response_validate_data(
                        equipment_serializer, equipment_ch_serializer
                    )
                )

                # Log Entry Update Action
                organilab_logentry(
                    request.user,
                    instance,
                    CHANGE,
                    "equipment object",
                    changed_data=equipment_changed_data,
                    relobj=organization,
                )

                if not hasattr(instance, "equipmentcharacteristics"):
                    equipment_ch_action = ADDITION

                organilab_logentry(
                    request.user,
                    equipment_ch,
                    equipment_ch_action,
                    "equipment characteristics",
                    changed_data=equipment_ch_changed_data,
                    relobj=organization,
                )

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
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        return super().list(request, *args, **kwargs)


class InstrumentalFamilyManagementViewset(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": serializers.InstrumentalFamilyDataTableSerializer,
        "destroy": serializers.InstrumentalFamilySerializer,
        "create": serializers.InstrumentalFamilySerializer,
        "update": serializers.InstrumentalFamilySerializer,
    }
    perms = {
        "list": ["laboratory.view_catalog"],
        "create": ["laboratory.add_catalog", "laboratory.view_catalog"],
        "update": ["laboratory.change_catalog", "laboratory.view_catalog"],
        "destroy": ["laboratory.delete_catalog", "laboratory.view_catalog"],
    }

    permission_classes = (PermissionByLaboratoryInOrganization,)

    queryset = Catalog.objects.filter(key="instrumental_family")
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["id", "description"]  # for the global search
    filterset_class = filterset.InstrumentalFamilyFilter
    ordering_fields = ["description"]
    ordering = ("id",)  # default order
    operation_type = ""
    org_pk, lab_pk, org = None, None, None

    def create(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        create = super().create(request, *args, **kwargs)
        if create.status_code == 201:
            if "id" in create.data.keys():
                instance = get_object_or_404(
                    Catalog.objects.using(settings.READONLY_DATABASE),
                    pk=create.data["id"],
                )
                organilab_logentry(
                    request.user,
                    instance,
                    ADDITION,
                    "catalog",
                    changed_data=["key", "description"],
                )
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
        organilab_logentry(
            request.user,
            instance,
            CHANGE,
            "catalog",
            changed_data=["key", "description"],
        )
        return update

    def list(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        return super().list(request, *args, **kwargs)


class EquipmentTypeManagementViewset(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": serializers.EquipmentTypeDataTableSerializer,
        "destroy": serializers.EquipmentTypeSerializer,
        "create": serializers.EquipmentTypeSerializer,
        "update": serializers.EquipmentTypeSerializer,
    }
    perms = {
        "list": ["laboratory.view_equipmenttype"],
        "create": ["laboratory.add_equipmenttype"],
        "update": ["laboratory.change_equipmenttype"],
        "destroy": ["laboratory.delete_equipmenttype"],
    }

    permission_classes = (PermissionByLaboratoryInOrganization,)

    queryset = EquipmentType.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["id", "description", "name"]  # for the global search
    filterset_class = filterset.EquipmentTypeFilter
    ordering_fields = ["description", "name"]
    ordering = ("id",)  # default order
    operation_type = ""
    org_pk, lab_pk, org = None, None, None

    def create(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=self.org_pk,
        )
        create = super().create(request, *args, **kwargs)

        if create.status_code == 201:
            if "id" in create.data.keys():
                instance = get_object_or_404(
                    EquipmentType.objects.using(settings.READONLY_DATABASE),
                    pk=create.data["id"],
                )
                organilab_logentry(
                    request.user,
                    instance,
                    ADDITION,
                    "equipment type",
                    changed_data=["name", "description"],
                    relobj=organization,
                )
        return create

    def destroy(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        instance = self.get_object()
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=self.org_pk,
        )

        delete_equipment_list = list(
            Object.objects.filter(
                type=Object.EQUIPMENT, equipmentcharacteristics__equipment_type=instance
            ).values_list("pk", flat=True)
        )

        organilab_logentry(
            request.user, instance, DELETION, "equipment type", relobj=organization
        )

        destroy = super().destroy(request, *args, **kwargs)
        equipment_list = Object.objects.filter(pk__in=delete_equipment_list)
        shelfobject_equipment_list = ShelfObject.objects.filter(
            object__in=equipment_list
        )

        for obj_equipment in equipment_list:
            organilab_logentry(
                request.user,
                obj_equipment,
                DELETION,
                "equipment object",
                relobj=organization,
            )

        for shelfobj_equipment in shelfobject_equipment_list:
            organilab_logentry(
                request.user,
                shelfobj_equipment,
                DELETION,
                "shelfobject equipment",
                relobj=organization,
            )

        equipment_list.delete()

        return destroy

    def update(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=self.org_pk,
        )
        update = super().update(request, *args, **kwargs)
        instance = self.get_object()
        organilab_logentry(
            request.user,
            instance,
            CHANGE,
            "equipment type",
            changed_data=["name", "description"],
            relobj=organization,
        )
        return update

    def list(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        return super().list(request, *args, **kwargs)


class ReactiveManagementViewset(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": serializers.ReactiveDataTableSerializer,
        "destroy": serializers.ReactiveSerializer,
        "create": serializers.ValidateReactiveSerializer,
        "update": serializers.ValidateReactiveSerializer,
        "add_limits": serializers.ReactiveLimitSerializer,
    }
    perms = {
        "list": ["laboratory.view_object"],
        "create": ["laboratory.add_object", "laboratory.view_object"],
        "update": ["laboratory.change_object", "laboratory.view_object"],
        "destroy": ["laboratory.delete_object", "laboratory.view_object"],
        "add_limits": ["laboratory.add_object", "laboratory.view_object"],
        "get_reactive_limits": ["laboratory.view_object"],
    }

    permission_classes = (PermissionByLaboratoryInOrganization,)

    queryset = Object.objects.filter(type=Object.REACTIVE)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["code", "name", "synonym"]  # for the global search
    filterset_class = filterset.ReactiveFilter
    ordering_fields = ["code"]
    ordering = ("code",)  # default order
    operation_type = ""
    org_pk, org = None, None

    def get_response_validate_data(self, reactive_serializer, reactive_ch_serializer):
        reactive_changed_data = list(reactive_serializer.validated_data.keys())
        reactive_ch_changed_data = list(reactive_ch_serializer.validated_data.keys())

        # Multiple response data
        response_data = reactive_serializer.data
        reactive_ch_data = reactive_ch_serializer.data

        # THIS ID SHOULDN'T REPLACE THE MAIN ID(EQUIPMENT OBJECT)
        del reactive_ch_data["id"]
        response_data.update(reactive_ch_data)

        return response_data, reactive_changed_data, reactive_ch_changed_data

    def get_reactive_ch_serializer(self, instance, request, partial):
        if hasattr(instance, "sustancecharacteristics"):
            reactive_ch_instance = instance.sustancecharacteristics
            reactive_ch_serializer = ValidateReactiveCharacteristicsSerializer(
                reactive_ch_instance, data=request.data, partial=partial
            )
        else:
            data = request.data
            data.update({"object": instance.pk})
            reactive_ch_serializer = ValidateReactiveCharacteristicsSerializer(
                data=data, partial=partial
            )

        return reactive_ch_serializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["kwargs"] = self.kwargs
        return context

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        filters = Q(
            organization__in=get_pk_org_ancestors_decendants(
                self.request.user, self.org_pk
            ),
            is_public=True,
        ) | Q(organization__pk=self.org_pk, is_public=False)

        return queryset.filter(filters).distinct()

    def create(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=self.org_pk,
        )
        errors, response_data, headers = {}, {}, self.get_success_headers({})

        # Serializers
        reactive_serializer = self.get_serializer(data=request.data)
        reactive_ch_serializer = ValidateReactiveCharacteristicsSerializer(
            data=request.data
        )

        if reactive_serializer.is_valid():
            if reactive_ch_serializer.is_valid():
                instance = reactive_serializer.save()
                reactive_ch_serializer.save(obj=instance)

                response_data, reactive_changed_data, reactive_ch_changed_data = (
                    self.get_response_validate_data(
                        reactive_serializer, reactive_ch_serializer
                    )
                )

                # Multiple headers
                headers = self.get_success_headers(response_data)

                # Log Entry Create Action
                organilab_logentry(
                    request.user,
                    instance,
                    ADDITION,
                    "reactive object",
                    changed_data=reactive_changed_data,
                    relobj=organization,
                )

                if hasattr(instance, "sustancecharacteristics"):
                    organilab_logentry(
                        request.user,
                        instance,
                        ADDITION,
                        "sustance characteristics",
                        changed_data=reactive_ch_changed_data,
                        relobj=organization,
                    )

                return Response(
                    response_data, status=status.HTTP_201_CREATED, headers=headers
                )
            else:
                errors.update(reactive_ch_serializer.errors)
        else:
            errors.update(reactive_serializer.errors)
            if not reactive_ch_serializer.is_valid():
                errors.update(reactive_ch_serializer.errors)

        if errors:
            raise ValidationError(errors)

    def destroy(self, request, *args, **kwargs):
        # ReactiveCharacteristics has OnetoOne relation with Object(Equipment) -->
        # ON DELETE CASCADE
        self.org_pk = kwargs["org_pk"]
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=self.org_pk,
        )
        instance = self.get_object()
        reactive_ch_instance = None

        if hasattr(instance, "sustancecharacteristics"):
            reactive_ch_instance = instance.sustancecharacteristics

        destroy = super().destroy(request, *args, **kwargs)

        # Log Entry Destroy Action
        organilab_logentry(
            request.user, instance, DELETION, "reactive object", relobj=organization
        )

        if reactive_ch_instance:
            organilab_logentry(
                request.user,
                reactive_ch_instance,
                DELETION,
                "sustance characteristics",
                relobj=organization,
            )
        return destroy

    def update(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=self.org_pk,
        )
        errors, response_data = {}, {}
        reactive_ch_action = CHANGE
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        reactive_serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        reactive_ch_serializer = self.get_reactive_ch_serializer(
            instance, request, partial
        )

        if reactive_serializer.is_valid():
            if reactive_ch_serializer.is_valid():
                instance = reactive_serializer.save()
                reactive_ch = reactive_ch_serializer.save()

                if getattr(instance, "_prefetched_objects_cache", None):
                    # If 'prefetch_related' has been applied to a queryset, we need to
                    # forcibly invalidate the prefetch cache on the instance.
                    instance._prefetched_objects_cache = {}

                response_data, reactive_changed_data, reactive_ch_changed_data = (
                    self.get_response_validate_data(
                        reactive_serializer, reactive_ch_serializer
                    )
                )

                # Log Entry Update Action
                organilab_logentry(
                    request.user,
                    instance,
                    CHANGE,
                    "reactive object",
                    changed_data=reactive_changed_data,
                    relobj=organization,
                )

                if not hasattr(instance, "sustancecharacteristics"):
                    reactive_ch_action = ADDITION

                organilab_logentry(
                    request.user,
                    reactive_ch,
                    reactive_ch_action,
                    "sustance characteristics",
                    changed_data=reactive_ch_changed_data,
                    relobj=organization,
                )

            else:
                errors.update(reactive_ch_serializer.errors)
        else:
            errors.update(reactive_serializer.errors)
            if not reactive_ch_serializer.is_valid():
                errors.update(reactive_ch_serializer.errors)

        if errors:
            raise ValidationError(errors)

        return Response(response_data)

    def list(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab_pk = kwargs["lab_pk"]
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=["get"])
    def get_reactive_limits(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        reactive = kwargs.get("pk")
        lab = kwargs.get("lab_pk")

        if reactive:
            obj = ReactiveLimit.objects.filter(
                object__id=reactive, laboratory__pk=lab
            ).first()

            serializer = GetReactiveLimitSerializer(instance=obj, many=False)
            return Response(serializer.data)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def add_limits(self, request, *args, **kwargs):
        self.org_pk = kwargs["org_pk"]
        self.lab = kwargs["lab_pk"]
        reactive = self.request.GET.get("reactive", None)
        serializer = None
        if reactive:
            obj = ReactiveLimit.objects.filter(
                object__id=reactive, laboratory__pk=self.lab
            ).first()
            serializer = serializers.ReactiveLimitSerializer(
                data=request.data, instance=obj
            )
        else:
            serializer = serializers.ReactiveLimitSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LaboratoryProcessViewset(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": serializers.LaboratoryProcessDataTableSerializer,
        "destroy": serializers.LaboratoryProcessSerializer,
        "create": serializers.LaboratoryProcessSerializer,
        "update": serializers.LaboratoryProcessUpdateSerializer,
    }
    perms = {
        "list": ["laboratory.view_laboratory_process"],
        "create": ["laboratory.add_laboratory_process"],
        "update": ["laboratory.change_laboratory_process"],
        "destroy": ["laboratory.delete_laboratory_process"],
    }

    permission_classes = (PermissionByLaboratoryInOrganization,)

    queryset = LaboratoryProcess.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["description"]
    ordering_fields = ["pk"]
    filterset_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        lab = self.kwargs.get("lab_pk", 0)
        if lab:
            # self.lab = get_object_or_404(Laboratory, pk=lab)
            return queryset.filter(laboratory__pk=lab)

        return queryset.none()

    def perform_create(self, serializer):

        serializer.save(created_by=self.request.user)
        return super().perform_create(serializer)


#  Provider
class ProviderViewSet(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": ProviderDataTableSerializer,
        "destroy": ProviderSerializer,
        "create": ProviderValidateSerializer,
        "update": ProviderValidateSerializer,
    }

    perms = {
        "list": ["laboratory.view_provider"],
        "create": ["laboratory.add_provider"],
        "update": ["laboratory.change_provider"],
        "destroy": ["laboratory.delete_provider"],
    }

    queryset = Provider.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["name", "email", "phone_number", "legal_identity"]
    filterset_class = ProviderFilter
    ordering_fields = ["name"]
    ordering = ("-creation_date",)

    def get_queryset(self):
        lab_pk = self.kwargs.get("lab_pk")

        qs = Provider.objects.all()

        if lab_pk:
            qs = qs.filter(laboratory_id=lab_pk)

        return qs

    def get_lab_pk_or_error(self):
        lab_pk = self.kwargs.get("lab_pk")
        if not lab_pk:
            raise ValidationError(
                {"lab_pk": _("This endpoint requires lab_pk in the URL.")}
            )
        return lab_pk

    def perform_create(self, serializer):
        lab_pk = self.get_lab_pk_or_error()

        provider = serializer.save(
            laboratory_id=lab_pk,
            created_by=self.request.user,
        )

        organilab_logentry(
            self.request.user,
            provider,
            ADDITION,
            "provider",
            changed_data=[],  # no necesaria en create
            relobj=lab_pk,  # para LabOrgLogEntry
        )

    def perform_update(self, serializer):
        lab_pk = self.get_lab_pk_or_error()

        provider_before = self.get_object()
        before = {
            "name": provider_before.name,
            "phone_number": provider_before.phone_number,
            "email": provider_before.email,
            "legal_identity": provider_before.legal_identity,
            "laboratory_id": provider_before.laboratory_id,
        }

        provider = serializer.save(laboratory_id=lab_pk)

        after = {
            "name": provider.name,
            "phone_number": provider.phone_number,
            "email": provider.email,
            "legal_identity": provider.legal_identity,
            "laboratory_id": provider.laboratory_id,
        }

        changed_fields = [k for k in after.keys() if before.get(k) != after.get(k)]

        organilab_logentry(
            self.request.user,
            provider,
            CHANGE,
            "provider",
            changed_data=changed_fields,
            relobj=lab_pk,
        )

    def perform_destroy(self, instance):
        lab_pk = self.get_lab_pk_or_error()

        provider_id = instance.pk
        provider_repr = str(instance)

        organilab_logentry(
            self.request.user,
            instance,
            DELETION,
            "provider",
            changed_data=[],  # no aplica en delete
            object_repr=provider_repr,
            relobj=lab_pk,
        )

        instance.delete()


#  ObjectFeature
class ObjectFeatureViewSet(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": ObjectFeatureDataTableSerializer,
        "destroy": ObjectFeatureSerializer,
        "create": ObjectFeatureValidateSerializer,
        "update": ObjectFeatureValidateSerializer,
    }

    perms = {
        "list": ["laboratory.view_objectfeatures"],
        "create": ["laboratory.add_objectfeatures"],
        "update": ["laboratory.change_objectfeatures"],
        "destroy": ["laboratory.delete_objectfeatures"],
    }

    queryset = ObjectFeatures.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["name", "description"]
    filterset_class = ObjectFeatureFilter
    ordering_fields = ["name"]
    ordering = ("id",)

    def get_lab_pk_or_error(self):
        lab_pk = self.kwargs.get("lab_pk")
        if not lab_pk:
            raise ValidationError(
                {"lab_pk": _("This endpoint requires lab_pk in the URL.")}
            )
        return lab_pk

    def perform_create(self, serializer):
        lab_pk = self.get_lab_pk_or_error()

        objectfeatures = serializer.save()

        organilab_logentry(
            self.request.user,
            objectfeatures,
            ADDITION,
            "objectfeatures",
            changed_data=[],  # no necesaria en create
            relobj=lab_pk,  # para LabOrgLogEntry
        )

    def perform_update(self, serializer):
        lab_pk = self.get_lab_pk_or_error()

        objectfeatures_before = self.get_object()

        before = {
            "name": objectfeatures_before.name,
            "description": objectfeatures_before.description,
        }

        objectfeatures = serializer.save()

        after = {
            "name": objectfeatures.name,
            "description": objectfeatures.description,
        }

        changed_fields = [k for k in after.keys() if before.get(k) != after.get(k)]

        organilab_logentry(
            self.request.user,
            objectfeatures,
            CHANGE,
            "objectfeatures",
            changed_data=changed_fields,
            relobj=lab_pk,
        )

    def perform_destroy(self, instance):
        lab_pk = self.get_lab_pk_or_error()

        objectfeatures_id = instance.pk
        objectfeatures_repr = str(instance)

        organilab_logentry(
            self.request.user,
            instance,
            DELETION,
            "objectfeatures",
            changed_data=[],  # no aplica en delete
            object_repr=objectfeatures_repr,
            relobj=lab_pk,
        )

        instance.delete()


#  Object
class ObjectViewSet(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": ObjectDataTableSerializer,
        "destroy": ObjectSerializer,
        "create": ObjectValidateSerializer,
        "update": ObjectValidateSerializer,
    }

    perms = {
        "list": ["laboratory.view_object"],
        "create": ["laboratory.add_object"],
        "update": ["laboratory.change_object"],
        "destroy": ["laboratory.delete_object"],
    }

    queryset = Object.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["name", "code", "model", "serie", "plaque"]
    filterset_class = ObjectFilter
    ordering_fields = ["name"]
    ordering = ("-creation_date",)

    def get_queryset(self):
        org_pk = self.kwargs.get("org_pk")
        qs = Object.objects.all()

        if org_pk:
            qs = qs.filter(organization_id=org_pk, type=Object.MATERIAL)

        return qs

    def get_org_pk_or_error(self):
        org_pk = self.kwargs.get("org_pk")
        if not org_pk:
            raise ValidationError(
                {"org_pk": _("This endpoint requires org_pk in the URL.")}
            )
        return org_pk

    def perform_create(self, serializer):
        org_pk = self.get_org_pk_or_error()

        object = serializer.save(
            organization_id=org_pk,
            created_by=self.request.user,
        )

        organilab_logentry(
            self.request.user,
            object,
            ADDITION,
            "object",
            changed_data=[],  # no necesaria en create
            relobj=org_pk,  # para LabOrgLogEntry
        )

    def perform_update(self, serializer):
        org_pk = self.get_org_pk_or_error()

        object_before = self.get_object()
        before = {
            "code": object_before.code,
            "name": object_before.name,
            "synonym": object_before.synonym,
            "description": object_before.description,
            "is_public": object_before.is_public,
            "is_container": object_before.is_container,
            "type": object_before.type,
            "features": list(object_before.features.values_list("pk", flat=True)),
        }

        object = serializer.save()

        after = {
            "code": object.code,
            "name": object.name,
            "synonym": object.synonym,
            "description": object.description,
            "is_public": object.is_public,
            "is_container": object.is_container,
            "type": object.type,
            "features": list(object.features.values_list("pk", flat=True)),
        }

        changed_fields = [k for k in after.keys() if before.get(k) != after.get(k)]

        organilab_logentry(
            self.request.user,
            object,
            CHANGE,
            "object",
            changed_data=changed_fields,
            relobj=org_pk,
        )

    def perform_destroy(self, instance):
        org_pk = self.get_org_pk_or_error()

        object_id = instance.pk
        object_repr = str(instance)

        organilab_logentry(
            self.request.user,
            instance,
            DELETION,
            "object",
            changed_data=[],  # no aplica en delete
            object_repr=object_repr,
            relobj=org_pk,
        )

        instance.delete()


class ShelObjectReactiveViewset(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": ShelObjectReactiveDataTableSerializer,
    }
    perms = {
        "list": ["laboratory.view_shelfobject"],
        "increase": ["laboratory.change_shelfobject"],
        "decrease": ["laboratory.change_shelfobject"],
    }
    permission_classes = (PermissionByLaboratoryInOrganization,)
    queryset = ShelfObject.objects.filter(object__type=Object.REACTIVE)
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = [
        "id",
        "object__name",
        "shelf__furniture__labroom__name",
        "shelf__name",
        "shelf__furniture__name",
        "container__object__name",
        "quantity",
        "measurement_unit__description",
        "measurement_unit__key",
    ]
    filterset_class = filterset.ShelObjectReactiveFilter
    ordering_fields = ["id"]

    def get_queryset(self):
        queryset = super().get_queryset()
        lab = self.kwargs.get("lab_pk", 0)
        if lab:
            return queryset.filter(in_where_laboratory=lab)
        return queryset.none()

    def _check_permission_on_laboratory(self, request, org_pk, lab_pk, method_name):
        if request.user.has_perms(
            self.perms[method_name]
        ):  # user can actually perform the requested action, then check object access permissions
            self.organization = get_object_or_404(
                OrganizationStructure.objects.using(settings.READONLY_DATABASE),
                pk=org_pk,
            )
            self.laboratory = get_object_or_404(
                Laboratory.objects.using(settings.READONLY_DATABASE), pk=lab_pk
            )
            user_is_allowed_on_organization(request.user, self.organization)
            organization_can_change_laboratory(
                self.laboratory, self.organization, raise_exec=True
            )
        else:
            raise PermissionDenied()

    @action(detail=False, methods=["post"])
    def increase(self, request, org_pk, lab_pk, **kwargs):
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "increase")
        self.serializer_class = IncreaseReactiveShelfObjectSerializer
        data = request.data.copy()
        if "shelfobject" in data and "shelf_object" not in data:
            data["shelf_object"] = data["shelfobject"]
        serializer = self.serializer_class(
            data=data, context={"request": request, "source_laboratory_id": lab_pk}
        )
        errors = {}
        if serializer.is_valid():
            save_increase_decrease_shelf_object(
                request.user,
                serializer.validated_data,
                self.laboratory,
                self.organization,
                is_increase_process=True,
            )
        else:
            errors = serializer.errors
            logger.error(f"Error in increase reactive shelf object: {errors}")
        if errors:
            return JsonResponse({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse(
            {"detail": _("Shelf object was increased successfully.")},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def decrease(self, request, org_pk, lab_pk, **kwargs):
        self._check_permission_on_laboratory(request, org_pk, lab_pk, "decrease")

        data = request.data.copy()

        if "shelfobject" in data and "shelf_object" not in data:
            data["shelf_object"] = data["shelfobject"]

        serializer = DecreaseReactiveShelfObjectSerializer(
            data=data, context={"request": request, "source_laboratory_id": lab_pk}
        )

        if serializer.is_valid():
            validated_data = serializer.validated_data.copy()

            if "reason" in validated_data:
                validated_data["description"] = validated_data.pop("reason")

            save_increase_decrease_shelf_object(
                request.user,
                validated_data,
                self.laboratory,
                self.organization,
                is_increase_process=False,
            )

            return JsonResponse(
                {"detail": _("Shelf object was decreased successfully.")},
                status=status.HTTP_200_OK,
            )
        logger.error(f"Error in decrease reactive shelf object: {serializer.errors}")
        return JsonResponse(
            {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )
