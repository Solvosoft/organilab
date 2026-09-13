"""CRUDs por nivel, operaciones de cuadrícula y el árbol.

Cada operación de cuadrícula es **una llamada que muta ``dataconfig`` en el
servidor y devuelve el estado nuevo completo**.  Los índices de fila y columna
dejan de ser un dato del DOM: la posición nace atómica junto al estante y
después se opera siempre por ``shelf_pk``.  Las operaciones destructivas se
niegan con motivo (409) en vez de corromper el layout, y no hay "guardar",
porque no existe un estado intermedio que se pueda perder.
"""

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from djgentelella.objectmanagement import BaseInlineObjectManagement
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from laboratory import dataconfig
from laboratory.api.labview import serializers as labview_serializers
from laboratory.api.labview.permissions import LABVIEW_PERMISSIONS, LabviewScopedMixin
from laboratory.api.labview.tree_builder import TreeBuilder
from laboratory.api.serializers import ShelfLabViewSerializer
from laboratory.models import (
    Furniture,
    Laboratory,
    LaboratoryRoom,
    Shelf,
    ShelfObject,
)
from laboratory.shelfobject.serializers import ShelfObjectPk
from laboratory.utils import organilab_logentry


class LabviewBaseManagement(LabviewScopedMixin, BaseInlineObjectManagement):
    """Base común de los tres CRUDs.

    El padre se resuelve desde la URL y ``get_parent_queryset`` lo acota al
    laboratorio del prefijo: sin eso, cualquier usuario con permiso sobre el
    modelo podría nombrar el pk de otro laboratorio.
    """

    authentication_classes = (SessionAuthentication,)
    permission_classes = LABVIEW_PERMISSIONS
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    ordering_fields = ["pk"]
    ordering = ("pk",)

    #: Acciones que operan sobre un objeto ya identificado y por tanto no
    #: necesitan el padre en la URL: exigirlo daría un 404 espurio.
    detail_actions = ()

    def get_parent_object(self):
        if self.action in self.detail_actions:
            return None
        return super().get_parent_object()

    def log(self, instance, action_flag, message):
        organilab_logentry(
            self.request.user,
            instance,
            action_flag,
            instance._meta.model_name,
            change_message=message,
            relobj=self.lab_pk,
        )


class LabRoomManagement(LabviewBaseManagement):
    parent_model = Laboratory
    parent_field = "laboratory"
    parent_url_kwarg = "lab_pk"

    serializer_class = {
        "list": labview_serializers.LabRoomSerializer,
        "retrieve": labview_serializers.LabRoomSerializer,
        "create": labview_serializers.ValidateLabRoomSerializer,
        "update": labview_serializers.ValidateLabRoomSerializer,
        "partial_update": labview_serializers.ValidateLabRoomSerializer,
        "destroy": labview_serializers.LabRoomSerializer,
    }
    perms = {
        "list": ["laboratory.view_laboratoryroom"],
        "retrieve": ["laboratory.view_laboratoryroom"],
        "create": ["laboratory.add_laboratoryroom"],
        "update": ["laboratory.change_laboratoryroom"],
        "partial_update": ["laboratory.change_laboratoryroom"],
        "destroy": ["laboratory.delete_laboratoryroom"],
    }
    queryset = LaboratoryRoom.objects.all()

    def get_parent_queryset(self):
        return Laboratory.objects.filter(pk=self.lab_pk)

    def perform_create(self, serializer):
        instance = serializer.save(
            laboratory=self.get_parent_object(), created_by=self.request.user
        )
        self.log(instance, ADDITION, _("Created laboratory room"))

    def perform_update(self, serializer):
        instance = serializer.save(laboratory=self.get_parent_object())
        self.log(instance, CHANGE, _("Updated laboratory room"))

    def perform_destroy(self, instance):
        self.log(instance, DELETION, _("Deleted laboratory room"))
        instance.delete()


class FurnitureManagement(LabviewBaseManagement):
    parent_model = LaboratoryRoom
    parent_field = "labroom"
    parent_url_kwarg = "labroom"
    accept_parent_pk_from_request = True
    detail_actions = (
        "add_row", "remove_row", "add_col", "remove_col",
        "retrieve", "update", "partial_update", "destroy",
    )

    serializer_class = {
        "list": labview_serializers.FurnitureSerializer,
        "retrieve": labview_serializers.FurnitureSerializer,
        "create": labview_serializers.ValidateFurnitureSerializer,
        "update": labview_serializers.ValidateFurnitureSerializer,
        "partial_update": labview_serializers.ValidateFurnitureSerializer,
        "destroy": labview_serializers.FurnitureSerializer,
    }
    perms = {
        "list": ["laboratory.view_furniture"],
        "retrieve": ["laboratory.view_furniture"],
        "create": ["laboratory.add_furniture"],
        "update": ["laboratory.change_furniture"],
        "partial_update": ["laboratory.change_furniture"],
        "destroy": ["laboratory.delete_furniture"],
        "add_row": ["laboratory.change_furniture"],
        "remove_row": ["laboratory.change_furniture"],
        "add_col": ["laboratory.change_furniture"],
        "remove_col": ["laboratory.change_furniture"],
    }
    queryset = Furniture.objects.all()

    def get_parent_queryset(self):
        return LaboratoryRoom.objects.filter(laboratory__pk=self.lab_pk)

    def get_queryset(self):
        # Las acciones de cuadrícula operan sobre un mueble concreto y no
        # necesitan el padre en la URL: basta con acotarlas al laboratorio.
        if self.action in self.detail_actions:
            return Furniture.objects.filter(
                labroom__laboratory__pk=self.lab_pk
            ).select_related("type", "labroom")
        return super().get_queryset()

    def perform_create(self, serializer):
        instance = serializer.save(
            labroom=self.get_parent_object(), created_by=self.request.user
        )
        self.log(instance, ADDITION, _("Created furniture"))

    def retrieve(self, request, *args, **kwargs):
        """El mueble con su cuadricula y sus estantes.

        El editor lo usa para repintarse despues de cada operacion sin tener
        que rehacer el arbol entero, que destruiria la instancia del widget en
        plena edicion.
        """
        furniture = self.get_object()
        data = labview_serializers.FurnitureSerializer(furniture).data
        state = self.grid_state(furniture).data
        data.update(state)
        return Response(data)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.log(instance, CHANGE, _("Updated furniture"))

    def perform_destroy(self, instance):
        self.log(instance, DELETION, _("Deleted furniture"))
        instance.delete()

    # -- cuadrícula --------------------------------------------------------

    def grid_state(self, furniture):
        """``{grid, shelves}``: el estado nuevo completo, no un delta.

        El widget se repinta con lo que responde el servidor y nunca acumula
        estado propio, así que devolver el estado entero es lo que impide que
        cliente y base de datos diverjan.

        Los nodos los arma ``TreeBuilder``, el mismo que pinta el árbol: si
        aquí se serializara el estante de otra forma, al repintar faltarían
        campos que la tarjeta lee y la pantalla se quedaría mostrando un estado
        que la base de datos ya no tiene.
        """
        builder = TreeBuilder(
            self.get_organization(),
            self.get_laboratory(),
            self.request.user,
            request=self.request,
        )
        return Response(builder.build_shelves_of(furniture))

    def grid_conflict(self, error):
        return Response(
            {"detail": str(error.message), "shelves": error.shelves},
            status=status.HTTP_409_CONFLICT,
        )

    def grid_index(self, request):
        serializer = labview_serializers.GridIndexSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data.get("index")

    @action(detail=True, methods=["post"], url_path="grid/row")
    def add_row(self, request, *args, **kwargs):
        furniture = self.get_object()
        dataconfig.DataconfigService(furniture).add_row(self.grid_index(request))
        self.log(furniture, CHANGE, _("Added a row to the furniture grid"))
        return self.grid_state(furniture)

    @action(detail=True, methods=["post"], url_path="grid/row/remove")
    def remove_row(self, request, *args, **kwargs):
        furniture = self.get_object()
        try:
            dataconfig.DataconfigService(furniture).remove_row(
                self.grid_index(request)
            )
        except dataconfig.DataconfigConflict as error:
            return self.grid_conflict(error)
        self.log(furniture, CHANGE, _("Removed a row from the furniture grid"))
        return self.grid_state(furniture)

    @action(detail=True, methods=["post"], url_path="grid/col")
    def add_col(self, request, *args, **kwargs):
        furniture = self.get_object()
        dataconfig.DataconfigService(furniture).add_col(self.grid_index(request))
        self.log(furniture, CHANGE, _("Added a column to the furniture grid"))
        return self.grid_state(furniture)

    @action(detail=True, methods=["post"], url_path="grid/col/remove")
    def remove_col(self, request, *args, **kwargs):
        furniture = self.get_object()
        try:
            dataconfig.DataconfigService(furniture).remove_col(
                self.grid_index(request)
            )
        except dataconfig.DataconfigConflict as error:
            return self.grid_conflict(error)
        self.log(furniture, CHANGE, _("Removed a column from the furniture grid"))
        return self.grid_state(furniture)


class ShelfManagement(LabviewBaseManagement):
    parent_model = Furniture
    parent_field = "furniture"
    parent_url_kwarg = "furniture"
    accept_parent_pk_from_request = True
    detail_actions = (
        "move", "availability", "retrieve", "update", "partial_update", "destroy",
    )

    serializer_class = {
        "list": labview_serializers.ShelfSerializer,
        "retrieve": labview_serializers.ShelfSerializer,
        "create": labview_serializers.ValidateShelfSerializer,
        "update": labview_serializers.ValidateShelfSerializer,
        "partial_update": labview_serializers.ValidateShelfSerializer,
        "destroy": labview_serializers.ShelfSerializer,
        "move": labview_serializers.ShelfMoveSerializer,
        "availability": labview_serializers.ShelfAvailabilitySerializer,
    }
    perms = {
        "list": ["laboratory.view_shelf"],
        "retrieve": ["laboratory.view_shelf"],
        "create": ["laboratory.add_shelf"],
        "update": ["laboratory.change_shelf"],
        "partial_update": ["laboratory.change_shelf"],
        "destroy": ["laboratory.delete_shelf"],
        "move": ["laboratory.change_shelf"],
        "availability": ["laboratory.view_shelf"],
    }
    queryset = Shelf.objects.all()

    def get_parent_queryset(self):
        return Furniture.objects.filter(labroom__laboratory__pk=self.lab_pk)

    def get_queryset(self):
        if self.action in self.detail_actions:
            return Shelf.objects.filter(
                furniture__labroom__laboratory__pk=self.lab_pk
            ).select_related("type", "measurement_unit", "furniture")
        return super().get_queryset()

    def create(self, request, *args, **kwargs):
        """``row`` y ``col`` son obligatorios: la posición nace con el estante.

        Antes el estante se guardaba sin posición y sólo entraba a la
        cuadrícula cuando el usuario guardaba el mueble entero; si no lo hacía,
        una tarea programada lo borraba.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        furniture = self.get_parent_object()
        row = serializer.validated_data.pop("row")
        col = serializer.validated_data.pop("col")
        objects = serializer.validated_data.pop("available_objects_when_limit", [])

        instance = Shelf.objects.create(
            furniture=furniture,
            created_by=request.user,
            **serializer.validated_data,
        )
        if objects:
            instance.available_objects_when_limit.set(objects)
        dataconfig.DataconfigService(furniture).place_shelf(instance.pk, row, col)
        self.log(instance, ADDITION, _("Created shelf"))
        return Response(
            labview_serializers.ShelfSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        self.log(instance, CHANGE, _("Updated shelf"))

    def destroy(self, request, *args, **kwargs):
        """409 si el estante todavía guarda objetos.

        Es la misma guarda que ya tenía el borrado antiguo, pero explícita: se
        responde con motivo en vez de arrastrar los objetos.
        """
        instance = self.get_object()
        total = ShelfObject.objects.filter(shelf=instance).count()
        if total:
            return Response(
                {
                    "detail": _("The shelf still contains objects"),
                    "shelfobjects": total,
                },
                status=status.HTTP_409_CONFLICT,
            )
        furniture = instance.furniture
        self.log(instance, DELETION, _("Deleted shelf"))
        dataconfig.DataconfigService(furniture).remove_shelf(instance.pk)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["put"])
    def move(self, request, *args, **kwargs):
        """Siempre por ``shelf_pk``, nunca por índices del DOM."""
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = dataconfig.DataconfigService(instance.furniture)
        service.move_shelf(
            instance.pk,
            serializer.validated_data["row"],
            serializer.validated_data["col"],
        )
        self.log(instance, CHANGE, _("Moved shelf"))
        return Response({"grid": {"cells": instance.furniture.get_grid()}})

    @action(detail=True, methods=["get"])
    def availability(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.get_object()).data)


class LabviewTreeViewSet(LabviewScopedMixin, viewsets.GenericViewSet):
    """El mapa completo del laboratorio en una sola respuesta."""

    authentication_classes = (SessionAuthentication,)
    permission_classes = LABVIEW_PERMISSIONS
    queryset = LaboratoryRoom.objects.none()
    serializer_class = labview_serializers.LabRoomSerializer
    perms = {"list": ["laboratory.view_laboratoryroom"]}

    def list(self, request, *args, **kwargs):
        builder = TreeBuilder(
            self.get_organization(),
            self.get_laboratory(),
            request.user,
            risk=request.GET.get("risk") in ("1", "true", "True"),
            request=request,
        )
        return Response(builder.build())


class LabviewShelfObjectTableViewSet(LabviewScopedMixin, viewsets.GenericViewSet):
    """La tabla de objetos del estante seleccionado.

    A diferencia de ``ShelfObjectTableViewSet``, que no exigía
    ``view_shelfobject``, aquí el permiso es obligatorio y las acciones de cada
    fila viajan como diccionario.
    """

    authentication_classes = (SessionAuthentication,)
    permission_classes = LABVIEW_PERMISSIONS
    serializer_class = labview_serializers.LabviewShelfObjectTableSerializer
    queryset = ShelfObject.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = [
        "shelfobject_code",
        "object__name",
        "object__type",
        "quantity",
        "measurement_unit__description",
        "container__object__name",
    ]
    ordering_fields = [
        "shelfobject_code",
        "object__name",
        "object__type",
        "quantity",
        "measurement_unit__description",
        "container__object__name",
    ]
    ordering = ("-last_update",)
    perms = {"list": ["laboratory.view_shelfobject"]}

    def get_queryset(self):
        if not self.data["shelf"]:
            return ShelfObject.objects.none()
        return (
            ShelfObject.objects.filter(
                in_where_laboratory=self.get_laboratory(),
                shelf=self.data["shelf"],
                containershelfobject=None,
            )
            .select_related("object", "shelf", "measurement_unit", "container__object")
        )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        serializer_so = ShelfObjectPk(data=self.request.GET)
        if not queryset and serializer_so.is_valid():
            queryset = self.get_queryset().filter(
                pk=serializer_so.validated_data["search"].split("=")[1]
            )
        return queryset

    def list(self, request, *args, **kwargs):
        laboratory = self.get_laboratory()
        validate_serializer = ShelfLabViewSerializer(
            data=request.GET, laboratory=laboratory
        )
        validate_serializer.is_valid(raise_exception=True)
        self.data = validate_serializer.data

        base_queryset = self.get_queryset()
        queryset = self.filter_queryset(base_queryset)
        data = self.paginate_queryset(queryset)
        response = {
            "data": data,
            "recordsTotal": base_queryset.count(),
            "recordsFiltered": queryset.count(),
            "draw": request.GET.get("draw", 1),
        }
        return Response(self.get_serializer(response).data)
