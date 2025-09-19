from django.conf import settings
from djgentelella.groute import register_lookups
from djgentelella.views.select2autocomplete import BaseSelect2View, GPaginator
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from auth_and_perms.api.serializers import ValidateUserAccessOrgLabSerializer
from laboratory.models import LaboratoryRoom, Furniture, Shelf
from laboratory.shelfobject.utils import (
    get_available_objs_by_shelfobject,
    get_lab_room_queryset_by_filters,
    get_furniture_queryset_by_filters,
    get_shelf_queryset_by_filters,
)
from laboratory.utils import get_laboratories_from_organization
from laboratory.utils_base_unit import get_base_unit, get_related_units_from_laboratory
from report.api.serializers import ValidateUserAccessLabRoomSerializer
from django.db.models import Q, Sum


class GPaginatorMoreElements(GPaginator):
    page_size = 100


@register_lookups(prefix="lab_room", basename="lab_room")
class LabRoomLookup(BaseSelect2View):
    model = LaboratoryRoom
    fields = ["name"]
    ordering = ["name"]
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    organization, laboratory, lab_room, serializer, all_labs_org, shelfobject = (
        None,
        None,
        None,
        None,
        False,
        None,
    )

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.all_labs_org:
            labs_by_org = get_laboratories_from_organization(self.organization.pk)
            queryset = LaboratoryRoom.objects.filter(
                laboratory__in=labs_by_org.filter(
                    profile__user=self.request.user
                ).using(settings.READONLY_DATABASE)
            )
        else:
            if self.laboratory:
                queryset = queryset.filter(laboratory=self.laboratory)

                if self.shelfobject:
                    units = get_related_units_from_laboratory(
                        self.shelfobject.measurement_unit
                    )
                    filters = {"furniture__shelf__measurement_unit__in": units}
                    queryset = get_lab_room_queryset_by_filters(
                        queryset, self.shelfobject, "furniture__shelf", filters
                    )

        if self.lab_room:
            id_list = [lab_room.pk for lab_room in self.lab_room]
            self.selected = list(map(str, id_list))
        return queryset

    def list(self, request, *args, **kwargs):
        self.serializer = ValidateUserAccessLabRoomSerializer(
            data=request.GET, context={"user": request.user}
        )

        if self.serializer.is_valid():
            self.lab_room = self.serializer.validated_data["lab_room"]
            self.laboratory = self.serializer.validated_data["laboratory"]
            self.organization = self.serializer.validated_data["organization"]
            self.all_labs_org = self.serializer.validated_data["all_labs_org"]
            self.shelfobject = self.serializer.validated_data.get("shelfobject", None)
            return super().list(request, *args, **kwargs)

        return Response(
            {
                "status": "Bad request",
                "errors": self.serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


@register_lookups(prefix="furniture", basename="furniture")
class FurnitureLookup(BaseSelect2View):
    model = Furniture
    fields = ["name"]
    ref_field = "labroom"
    ordering = ["name"]
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer, shelfobject = None, None

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.shelfobject:
            units = get_related_units_from_laboratory(self.shelfobject.measurement_unit)
            filters = {"shelf__measurement_unit__in": units}
            queryset = get_furniture_queryset_by_filters(
                queryset, self.shelfobject, "shelf", filters
            )
        return queryset

    def list(self, request, *args, **kwargs):
        self.serializer = ValidateUserAccessOrgLabSerializer(
            data=request.GET, context={"user": request.user}
        )

        if self.serializer.is_valid():
            self.shelfobject = self.serializer.validated_data.get("shelfobject", None)
            return super().list(request, *args, **kwargs)

        return Response(
            {
                "status": "Bad request",
                "errors": self.serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


@register_lookups(prefix="shelf", basename="shelf")
class ShelfLookup(BaseSelect2View):
    model = Shelf
    fields = ["name"]
    ref_field = "furniture"
    ordering = ["name"]
    pagination_class = GPaginatorMoreElements
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer, shelfobject = None, None

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.shelfobject:
            units = get_related_units_from_laboratory(self.shelfobject.measurement_unit)
            filters = {"measurement_unit__in": units}
            queryset = get_shelf_queryset_by_filters(
                queryset, self.shelfobject, "pk", filters
            )
        return queryset

    def list(self, request, *args, **kwargs):
        self.serializer = ValidateUserAccessOrgLabSerializer(
            data=request.GET, context={"user": request.user}
        )
        if self.serializer.is_valid():
            self.shelfobject = self.serializer.validated_data.get("shelfobject", None)
            return super().list(request, *args, **kwargs)

        return Response(
            {
                "status": "Bad request",
                "errors": self.serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
