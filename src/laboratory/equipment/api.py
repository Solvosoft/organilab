"""API de los registros nuevos del equipo (programa, verificaciones, fallas, documentos).

Una sola clase base hace lo que los viewsets anteriores repetían a mano: toma
organización y equipo de la URL, deja la observación en la línea de tiempo del equipo
y la entrada en la bitácora de cambios.
"""
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from laboratory import utils
from laboratory.api.shelfobject import (
    AuthAllPermBaseObjectManagementShelfObjectBase,
    equipment_record_perms,
)
from laboratory.equipment import serializers as eqs

from laboratory.models import (
    ControlMeasurement,
    ControlPoint,
    EquipmentActivityPlan,
    EquipmentDocument,
    ShelfObjectFailure,
    ShelfObjectObservation,
    ShelfObjectVerification,
)


class EquipmentRecordViewSet(AuthAllPermBaseObjectManagementShelfObjectBase):
    model_name = ""
    #: textos de la línea de tiempo: (creado, actualizado, eliminado)
    observation_texts = ("", "", "")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            {
                "org_pk": self.kwargs.get("org_pk"),
                "lab_pk": self.kwargs.get("lab_pk"),
                "shelfobject": self.kwargs.get("shelfobject"),
            }
        )
        return context

    def get_serializer(self, *args, **kwargs):
        # Organización y equipo salen de la URL, nunca del cuerpo de la petición.
        if "data" in kwargs:
            data = kwargs["data"].copy() if hasattr(kwargs["data"], "copy") else dict(kwargs["data"])
            data["organization"] = self.kwargs.get("org_pk")
            data["shelfobject"] = self.kwargs.get("shelfobject")
            kwargs["data"] = data
        return super().get_serializer(*args, **kwargs)

    def shelfobject_id_of(self, instance):
        return instance.shelfobject_id

    def observe(self, instance, index):
        ShelfObjectObservation.objects.create(
            description=str(instance),
            action_taken=str(self.observation_texts[index])[:50],
            shelf_object_id=self.shelfobject_id_of(instance),
            created_by=self.request.user,
        )

    def log(self, instance, flag, changed_data):
        utils.organilab_logentry(
            self.request.user,
            instance,
            flag,
            self.model_name,
            changed_data=changed_data,
            change_message="%s: %s" % (self.observation_texts[{ADDITION: 0, CHANGE: 1, DELETION: 2}[flag]], instance),
            relobj=self.kwargs.get("lab_pk"),
        )

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        self.observe(instance, 0)
        self.log(instance, ADDITION, list(serializer.validated_data.keys()))

    def perform_update(self, serializer):
        instance = serializer.save()
        self.observe(instance, 1)
        self.log(instance, CHANGE, list(serializer.validated_data.keys()))

    def perform_destroy(self, instance):
        self.observe(instance, 2)
        self.log(instance, DELETION, [])
        instance.delete()


class EquipmentActivityPlanViewSet(EquipmentRecordViewSet):
    model_name = "equipmentactivityplan"
    perms = equipment_record_perms(model_name)
    queryset = EquipmentActivityPlan.objects.select_related("responsible__user")
    serializer_class = {
        "list": eqs.datatable(eqs.ActivityPlanRowSerializer),
        "create": eqs.ActivityPlanWriteSerializer,
        "update": eqs.ActivityPlanWriteSerializer,
        "get_values_for_update": eqs.ActivityPlanValuesSerializer,
    }
    search_fields = ["name", "notes"]
    ordering = ("activity_kind", "pk")
    observation_texts = (_("Program created"), _("Program updated"), _("Program deleted"))


class ShelfObjectVerificationViewSet(EquipmentRecordViewSet):
    model_name = "shelfobjectverification"
    perms = equipment_record_perms(model_name)
    queryset = ShelfObjectVerification.objects.select_related("responsible__user")
    serializer_class = {
        "list": eqs.datatable(eqs.VerificationRowSerializer),
        "create": eqs.VerificationWriteSerializer,
        "update": eqs.VerificationWriteSerializer,
        "get_values_for_update": eqs.VerificationValuesSerializer,
    }
    search_fields = ["verification_type", "result", "observation"]
    ordering = ("-verification_date",)
    observation_texts = (_("Verification created"), _("Verification updated"), _("Verification deleted"))


class ShelfObjectFailureViewSet(EquipmentRecordViewSet):
    model_name = "shelfobjectfailure"
    perms = equipment_record_perms(model_name)
    queryset = ShelfObjectFailure.objects.select_related("provider")
    serializer_class = {
        "list": eqs.datatable(eqs.FailureRowSerializer),
        "create": eqs.FailureWriteSerializer,
        "update": eqs.FailureWriteSerializer,
        "get_values_for_update": eqs.FailureValuesSerializer,
    }
    search_fields = ["description", "repair_done", "modifications"]
    ordering = ("-failure_date",)
    observation_texts = (_("Failure registered"), _("Failure updated"), _("Failure deleted"))


class EquipmentDocumentViewSet(EquipmentRecordViewSet):
    model_name = "equipmentdocument"
    perms = equipment_record_perms(model_name)
    queryset = EquipmentDocument.objects.select_related("document_type")
    serializer_class = {
        "list": eqs.datatable(eqs.DocumentRowSerializer),
        "create": eqs.DocumentWriteSerializer,
        "update": eqs.DocumentWriteSerializer,
        "get_values_for_update": eqs.DocumentValuesSerializer,
    }
    search_fields = ["title", "version", "document_type__description"]
    ordering = ("-valid_from", "-pk")
    observation_texts = (_("Document added"), _("Document updated"), _("Document deleted"))


# --- Cartas de control (F3) ----------------------------------------------------------

class ControlMethodViewSet(EquipmentRecordViewSet):
    """Métodos de la organización y de sus ancestros (no cuelgan de un equipo)."""

    model_name = "controlmethod"
    perms = equipment_record_perms(model_name)
    serializer_class = {
        "list": eqs.datatable(eqs.ControlMethodRowSerializer),
        "create": eqs.ControlMethodWriteSerializer,
        "update": eqs.ControlMethodWriteSerializer,
        "get_values_for_update": eqs.ControlMethodValuesSerializer,
    }
    search_fields = ["name", "description"]
    ordering = ("name",)
    observation_texts = (_("Control method created"), _("Control method updated"), _("Control method deleted"))

    def get_queryset(self):
        return eqs.organization_methods(self.kwargs.get("org_pk")).select_related("organization")

    def list(self, request, *args, **kwargs):
        # La base lee kwargs["shelfobject"], que esta ruta no tiene.
        return super(AuthAllPermBaseObjectManagementShelfObjectBase, self).list(request, *args, **kwargs)

    def filter_queryset(self, queryset):
        # Sin equipo: el ámbito es la organización (y sus ancestros), no el laboratorio.
        return super(AuthAllPermBaseObjectManagementShelfObjectBase, self).filter_queryset(queryset)

    def get_serializer(self, *args, **kwargs):
        return super(EquipmentRecordViewSet, self).get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user, organization_id=self.kwargs["org_pk"])
        self.log(instance, ADDITION, list(serializer.validated_data.keys()))

    def perform_update(self, serializer):
        instance = serializer.save()
        self.log(instance, CHANGE, list(serializer.validated_data.keys()))

    def perform_destroy(self, instance):
        from django.db.models import ProtectedError
        from rest_framework.exceptions import ValidationError

        if instance.organization_id != int(self.kwargs["org_pk"]):
            raise ValidationError({"detail": _("The method belongs to another organization.")})
        try:
            self.log(instance, DELETION, [])
            instance.delete()
        except ProtectedError:
            raise ValidationError({"detail": _("The method is used by control points.")})


class ControlPointViewSet(EquipmentRecordViewSet):
    model_name = "controlpoint"
    perms = {
        **equipment_record_perms(model_name),
        "recalculate_limits": ["laboratory.change_controlpoint", "laboratory.view_controlpoint"],
    }
    queryset = ControlPoint.objects.select_related("method")
    serializer_class = {
        "list": eqs.datatable(eqs.ControlPointRowSerializer),
        "create": eqs.ControlPointWriteSerializer,
        "update": eqs.ControlPointWriteSerializer,
        "get_values_for_update": eqs.ControlPointValuesSerializer,
    }
    search_fields = ["name", "reference_standard"]
    ordering = ("nominal_value", "name")
    observation_texts = (_("Control point created"), _("Control point updated"), _("Control point deleted"))

    @action(detail=True, methods=["post"])
    def recalculate_limits(self, request, *args, **kwargs):
        from laboratory.equipment.control import ControlError, recalculate_limits

        point = self.get_object()
        serializer = eqs.RecalculateLimitsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            limits = recalculate_limits(
                point, serializer.validated_data["baseline_from"], serializer.validated_data["baseline_to"],
                user=request.user, notes=serializer.validated_data["notes"],
            )
        except ControlError as error:
            return Response({"baseline_from": [str(error)]}, status=status.HTTP_400_BAD_REQUEST)
        self.log(point, CHANGE, ["limits"])
        return Response({name: str(value) for name, value in limits.as_dict().items()})


class ControlMeasurementViewSet(EquipmentRecordViewSet):
    model_name = "controlmeasurement"
    perms = equipment_record_perms(model_name)
    queryset = ControlMeasurement.objects.select_related("responsible__user", "point__method")
    serializer_class = {
        "list": eqs.datatable(eqs.ControlMeasurementRowSerializer),
        "create": eqs.ControlMeasurementWriteSerializer,
        "update": eqs.ControlMeasurementWriteSerializer,
        "get_values_for_update": eqs.ControlMeasurementValuesSerializer,
    }
    search_fields = ["observation", "deviation", "corrective_action"]
    ordering = ("-measured_on", "-pk")
    observation_texts = (_("Control record created"), _("Control record updated"), _("Control record deleted"))

    def point(self):
        if not hasattr(self, "_point"):
            self._point = get_object_or_404(
                ControlPoint, pk=self.kwargs["point"], shelfobject_id=self.kwargs["shelfobject"],
                shelfobject__in_where_laboratory_id=self.kwargs["lab_pk"],
            )
        return self._point

    def filter_queryset(self, queryset):
        queryset = super(AuthAllPermBaseObjectManagementShelfObjectBase, self).filter_queryset(queryset)
        return queryset.filter(point=self.point())

    def shelfobject_id_of(self, instance):
        return instance.point.shelfobject_id

    def save_with_service(self, serializer, instance):
        from rest_framework.exceptions import ValidationError

        from laboratory.equipment.control import ControlError, save_measurement

        data = dict(serializer.validated_data)
        for name in ("shelfobject", "organization", "created_by"):
            data.pop(name, None)
        for name, value in data.items():
            setattr(instance, name, value)
        try:
            return save_measurement(instance, self.request.user)
        except ControlError as error:
            raise ValidationError({"values": [str(error)]})

    def perform_create(self, serializer):
        point = self.point()
        instance = self.save_with_service(serializer, ControlMeasurement(point=point, organization=point.organization))
        serializer.instance = instance
        self.observe(instance, 0)
        self.log(instance, ADDITION, list(serializer.validated_data.keys()))

    def perform_update(self, serializer):
        instance = self.save_with_service(serializer, serializer.instance)
        self.observe(instance, 1)
        self.log(instance, CHANGE, list(serializer.validated_data.keys()))

    def perform_destroy(self, instance):
        self.observe(instance, 2)
        self.log(instance, DELETION, [])
        instance.delete()
