from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from djgentelella.models import DeletedWithTrash

from ambiental.ambiental_defaults import (
    KEY_MEASURE_UNIT,
    KEY_NORMALIZER,
    KEY_POINT_TYPE,
    KEY_RESOURCE_TYPE,
    KEY_WASTE_TREATMENT,
    get_resource_info,
)
from laboratory import catalog
from laboratory.models import Catalog, Laboratory, Provider
from laboratory.models_utils import upload_files
from presentation.models import AbstractOrganizationRef

CENT = Decimal("0.01")
TEN_THOUSANDTH = Decimal("0.0001")


class MeasurementPoint(AbstractOrganizationRef, DeletedWithTrash):
    """Dónde se mide un recurso: un medidor, un tanque, un punto de acopio.

    La unidad de registro del módulo. Se asocia a un edificio (el camino corto de
    la interfaz) y, opcionalmente, a los laboratorios que abastece. Retirar un
    punto lo manda a la papelera: sale de las listas pero conserva su historial.
    """

    code = models.CharField(
        max_length=100,
        verbose_name=_("Code"),
        help_text=_("Meter or service number, as it appears on the bill"),
    )
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    point_type = catalog.GTForeignKey(
        Catalog,
        on_delete=models.PROTECT,
        verbose_name=_("Point type"),
        key_name="key",
        key_value=KEY_POINT_TYPE,
        related_name="ambiental_point_types",
    )
    resource_type = catalog.GTForeignKey(
        Catalog,
        on_delete=models.PROTECT,
        verbose_name=_("Resource type"),
        key_name="key",
        key_value=KEY_RESOURCE_TYPE,
        related_name="ambiental_point_resources",
    )
    building = models.ForeignKey(
        "risk_management.Buildings",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Building"),
        related_name="measurement_points",
    )
    laboratories = models.ManyToManyField(
        Laboratory,
        blank=True,
        verbose_name=_("Laboratories"),
        related_name="measurement_points",
    )
    meters_count = models.PositiveSmallIntegerField(
        default=1, verbose_name=_("Number of meters")
    )

    class Meta:
        verbose_name = _("Measurement point")
        verbose_name_plural = _("Measurement points")
        ordering = ["pk"]
        unique_together = ("organization", "code", "resource_type")
        permissions = [
            ("manage_building_access", _("Can manage access to buildings")),
        ]

    def __str__(self):
        return "%s - %s" % (self.code, self.name)


class ConsumptionRecord(AbstractOrganizationRef, DeletedWithTrash):
    """Cuánto consumió (o desechó) un punto de medición en un período.

    Un solo modelo para todos los recursos: lo que cambia entre ellos (placa del
    vehículo, código de residuo, número de manifiesto) va en ``extra_data``,
    validado contra los campos que ``ambiental_defaults`` declara para el recurso.
    Un residuo es un registro con ``is_waste``: comparte reportes e indicadores.

    Para reportes, indicadores y alertas el registro cuenta en el mes de
    ``period_end`` (el mes facturado); no se prorratea por días.
    """

    MANUAL = "manual"
    IMPORT = "import"
    SOURCES = (
        (MANUAL, _("Manual")),
        (IMPORT, _("Import")),
    )

    point = models.ForeignKey(
        MeasurementPoint,
        on_delete=models.PROTECT,
        verbose_name=_("Measurement point"),
        related_name="records",
    )
    period_start = models.DateField(verbose_name=_("Period start"))
    period_end = models.DateField(verbose_name=_("Period end"))
    quantity = models.DecimalField(
        max_digits=14, decimal_places=4, verbose_name=_("Quantity")
    )
    unit = catalog.GTForeignKey(
        Catalog,
        on_delete=models.PROTECT,
        verbose_name=_("Unit"),
        key_name="key",
        key_value=KEY_MEASURE_UNIT,
        related_name="ambiental_record_units",
    )
    unit_cost = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_("Unit cost"),
    )
    total_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Total cost"),
    )
    is_waste = models.BooleanField(default=False, verbose_name=_("Is waste"))
    treatment = catalog.GTForeignKey(
        Catalog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Waste treatment"),
        key_name="key",
        key_value=KEY_WASTE_TREATMENT,
        related_name="ambiental_record_treatments",
    )
    waste_manager = models.ForeignKey(
        Provider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Authorized waste manager"),
        related_name="ambiental_records",
    )
    document = models.FileField(
        upload_to=upload_files,
        null=True,
        blank=True,
        verbose_name=_("Supporting document"),
        help_text=_("Bill, receipt or waste manifest"),
    )
    extra_data = models.JSONField(default=dict, blank=True, verbose_name=_("Extra data"))
    source = models.CharField(
        max_length=20, choices=SOURCES, default=MANUAL, verbose_name=_("Source")
    )
    note = models.TextField(blank=True, default="", verbose_name=_("Note"))

    class Meta:
        verbose_name = _("Consumption record")
        verbose_name_plural = _("Consumption records")
        ordering = ["-period_end", "pk"]
        unique_together = ("point", "period_start", "period_end")
        permissions = [
            ("view_ambiental_dashboard", _("Can view the environmental dashboard")),
        ]
        indexes = [
            models.Index(fields=["organization", "period_start"]),
            models.Index(fields=["point", "period_start"]),
        ]

    def __str__(self):
        return "%s: %s - %s" % (self.point, self.period_start, self.period_end)

    @property
    def resource_info(self):
        return get_resource_info(self.point.resource_type)

    def complete_costs(self):
        """Completa el costo que falte: total = cantidad x unitario, o al revés."""
        if self.quantity is None:
            return
        quantity = Decimal(self.quantity)
        if self.total_cost is None and self.unit_cost is not None:
            self.total_cost = (quantity * Decimal(self.unit_cost)).quantize(
                CENT, rounding=ROUND_HALF_UP
            )
        elif self.unit_cost is None and self.total_cost is not None and quantity:
            self.unit_cost = (Decimal(self.total_cost) / quantity).quantize(
                TEN_THOUSANDTH, rounding=ROUND_HALF_UP
            )

    def clean(self):
        super().clean()
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValidationError(
                {"period_end": _("The period end must be after the period start.")}
            )
        allowed = set(self.resource_info["extra_fields"]) if self.point_id else set()
        unknown = set(self.extra_data or {}) - allowed
        if unknown:
            raise ValidationError(
                {"extra_data": _("Fields not allowed for this resource: %(fields)s")
                 % {"fields": ", ".join(sorted(unknown))}}
            )

    def save(self, *args, **kwargs):
        self.complete_costs()
        if self.point_id and self.resource_info["is_waste"]:
            self.is_waste = True
        super().save(*args, **kwargs)


class NormalizationBase(AbstractOrganizationRef):
    """El denominador de un indicador: los m² o las personas de un edificio en un año.

    Se precarga con lo que Organilab ya sabe (``Buildings.area`` y las jornadas de las
    zonas de riesgo del edificio) y quien administra lo corrige. Una fila escrita a
    mano (``is_manual``) no la vuelve a pisar la precarga. Si un año no tiene base,
    ``normalization.get_base`` hereda la del último año anterior.
    """

    normalizer = catalog.GTForeignKey(
        Catalog,
        on_delete=models.PROTECT,
        verbose_name=_("Normalizer"),
        key_name="key",
        key_value=KEY_NORMALIZER,
        related_name="ambiental_normalization_bases",
    )
    building = models.ForeignKey(
        "risk_management.Buildings",
        on_delete=models.CASCADE,
        verbose_name=_("Building"),
        related_name="normalization_bases",
    )
    year = models.PositiveSmallIntegerField(verbose_name=_("Year"))
    value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Value"))
    is_manual = models.BooleanField(
        default=True,
        verbose_name=_("Entered manually"),
        help_text=_("Preloading never overwrites a value entered manually"),
    )

    class Meta:
        verbose_name = _("Normalization base")
        verbose_name_plural = _("Normalization bases")
        ordering = ["-year", "pk"]
        unique_together = ("organization", "normalizer", "building", "year")
        permissions = [
            ("preload_normalizationbase", _("Can preload normalization bases")),
        ]

    def __str__(self):
        return "%s %s %s: %s" % (self.building, self.year, self.normalizer, self.value)


class ConsumptionAlert(AbstractOrganizationRef):
    """Un consumo atípico (o un punto sin registros) detectado por una regla de alerta.

    La alerta no desaparece al revisarla: queda con la nota que la explica (fuga,
    error de digitación, obra), que es lo que permite calibrar la regla después.
    """

    point = models.ForeignKey(
        MeasurementPoint,
        on_delete=models.CASCADE,
        verbose_name=_("Measurement point"),
        related_name="alerts",
    )
    record = models.ForeignKey(
        ConsumptionRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Consumption record"),
        related_name="alerts",
    )
    rule = models.ForeignKey(
        "presentation.AlertRule",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Alert rule"),
        related_name="consumption_alerts",
    )
    period = models.DateField(verbose_name=_("Period"))
    reference_value = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True, verbose_name=_("Reference value")
    )
    registered_value = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True, verbose_name=_("Registered value")
    )
    variation_pct = models.DecimalField(
        max_digits=9, decimal_places=2, null=True, blank=True, verbose_name=_("Variation (%)")
    )
    level = models.CharField(max_length=20, verbose_name=_("Level"))
    message = models.TextField(verbose_name=_("Message"))
    reviewed = models.BooleanField(default=False, verbose_name=_("Reviewed"))
    reviewed_note = models.TextField(blank=True, default="", verbose_name=_("Review note"))
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Reviewed by"),
        related_name="reviewed_consumption_alerts",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Reviewed at"))

    class Meta:
        verbose_name = _("Consumption alert")
        verbose_name_plural = _("Consumption alerts")
        ordering = ["reviewed", "-period", "pk"]
        unique_together = ("rule", "point", "period")
        permissions = [
            ("review_consumptionalert", _("Can review consumption alerts")),
        ]

    def __str__(self):
        return self.message
