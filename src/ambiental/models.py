from django.db import models
from django.utils.translation import gettext_lazy as _
from djgentelella.models import DeletedWithTrash

from ambiental.ambiental_defaults import KEY_POINT_TYPE, KEY_RESOURCE_TYPE
from laboratory import catalog
from laboratory.models import Catalog, Laboratory
from presentation.models import AbstractOrganizationRef


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

    def __str__(self):
        return "%s - %s" % (self.code, self.name)
