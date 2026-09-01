from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from djgentelella.fields.maps import GTPointField

from laboratory import catalog
from laboratory.models import Laboratory, Catalog, ShelfObject
from laboratory.models_utils import upload_files
from presentation.models import AbstractOrganizationRef
from risk_management.models_utils import PriorityCalculator, compute_risk_level
from risk_management.iper_defaults import (
    KEY_HAZARD_CATEGORY,
    KEY_PROBABILITY,
    KEY_CONSEQUENCE,
    KEY_RISK_LEVEL,
    DEFAULT_PERIOD_MONTHS,
    DEFAULT_REMINDER_DAYS_BEFORE,
)


class PriorityConstrain(AbstractOrganizationRef, PriorityCalculator):
    OPERATIONS = (
        ("<", "<"),
        ("<=", "<="),
        ("=", "="),
        (">", ">"),
        (">=", ">="),
        ("!", "!"),
        ("<>", "<X>"),
        ("=<>=", "=<X>="),
        ("<>=", "<X>="),
        ("=<>", "=<X>"),
        ("<<", "<X<"),
        ("=<<=", "=<X<="),
        ("<<=", "<X<="),
        ("=<<", "=<X<"),
    )
    operation = models.CharField(
        max_length=5, choices=OPERATIONS, verbose_name=_("Opertation")
    )
    left_value = models.IntegerField(
        help_text=_("left_value opertation X ej.  left_value > 100"),
        verbose_name=_("Comparative value"),
    )
    right_value = models.IntegerField(
        null=True, blank=True, help_text=_("Use only if =<x>=, <x>, <x>= or =<x>  ")
    )
    priority = models.IntegerField(
        default=1,
        verbose_name=_("Set priority if true"),
        help_text=_("Value result if operation is True"),
    )

    def __str__(self):
        if self.operation in ["<>", "=<>=", "<>=", "=<>", "<<", "=<<=", "<<=", "=<<"]:
            right = ""
            if self.right_value:
                right = str(self.right_value)
            return "%d %s  %s --> %s" % (
                self.left_value,
                self.get_operation_display(),
                right,
                self.priority,
            )
        return "%d %s X --> %s" % (self.left_value, self.operation, self.priority)


class ZoneType(models.Model):
    name = models.CharField(max_length=250, verbose_name=_("Name"))
    priority_validator = models.ManyToManyField(
        PriorityConstrain, verbose_name=_("Priority calculate operators")
    )

    def get_priority(self, value):
        for instance in self.priority_validator.all():
            if instance.operate(value):
                return instance.priority
        return 1

    def __str__(self):
        return self.name


class RiskZone(AbstractOrganizationRef):
    name = models.CharField(max_length=150, verbose_name=_("Name"))
    laboratories = models.ManyToManyField(
        "laboratory.Laboratory", verbose_name=_("Laboratories")
    )
    buildings = models.ManyToManyField(
        "risk_management.Buildings", verbose_name=_("Buildings")
    )
    num_workers = models.SmallIntegerField(verbose_name=_("Number of workers (aprox)"))
    zone_type = models.ForeignKey(
        ZoneType, on_delete=models.CASCADE, verbose_name=_("Zone Type")
    )
    priority = models.SmallIntegerField(verbose_name=_("Priority"), default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Risk zone")
        verbose_name_plural = _("Risk zones")
        ordering = ("priority", "pk")


def upload_notification_copy(instance, filename):
    date = int(datetime.now().strftime("%Y%m%d%H%M%S"))
    fname, dot, extension = filename.rpartition(".")
    return f"notifications/{slugify(date)}/{slugify(fname)}.{extension}"


class IncidentReport(AbstractOrganizationRef):
    creation_date = models.DateTimeField(auto_now_add=True)
    short_description = models.CharField(
        max_length=500,
        verbose_name=_("Descipción corta"),
        help_text=_("Descipción corta de evento, max 500 caracteres"),
    )
    incident_date = models.DateField(verbose_name=_("Fecha del incidente"))
    laboratories = models.ManyToManyField(
        "laboratory.Laboratory", verbose_name=_("Laboratories")
    )

    causes = models.TextField(verbose_name=_("Causas del accidente"))
    infraestructure_impact = models.TextField(
        verbose_name=_("Impacto a la infraestructura"),
        help_text=_("Indicando las consecuencias a corto, mediano y largo plazo."),
    )
    people_impact = models.TextField(
        verbose_name=_(
            "Impacto a las personas (empleados, visitantes y comunidad afectada)"
        ),
        help_text=_("Indicando las consecuencias a corto, mediano y largo plazo."),
    )
    environment_impact = models.TextField(
        verbose_name=_("Impacto ambiental"),
        help_text=_("Indicando las consecuencias a corto, mediano y largo plazo."),
    )
    result_of_plans = models.TextField(
        verbose_name=_(
            "Resultado de la implementación del Plan de Prevención, Preparación y Respuesta ante Accidentes Químicos."
        )
    )

    mitigation_actions = models.TextField(
        verbose_name=_(
            "Medidas adoptadas para corregir la situación y para atenuar sus efectos."
        )
    )

    recomendations = models.TextField(
        verbose_name=_("Recomendaciones"),
        help_text=_(
            """Recomendaciones que describan en detalle las medidas que se vayan a llevar a cabo para reducir el riesgo de que accidentes similares vuelvan a producirse."""
        ),
    )

    notification_copy = models.FileField(
        upload_to=upload_notification_copy,
        verbose_name=_(
            "En caso de intoxicación adjuntar copia de la notificación realizada al Centro Nacional de Control de Intoxicaciones (CNCI)"
        ),
        null=True,
        blank=True,
    )
    buildings = models.ManyToManyField(
        "risk_management.Buildings",
        verbose_name=_("Buildings"),
        related_name="incident_buildings",
        blank=True,
    )
    risk_zone = models.ForeignKey(
        "risk_management.RiskZone",
        verbose_name=_("Risk Zone"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.short_description


class Regent(AbstractOrganizationRef):
    TYPEREGENTS = (
        ("chemical", _("Chemical")),
        ("chemical_engineer", _("Chemical Engineer")),
        ("veterinarian", _("Veterinarian")),
    )

    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="regent_user"
    )
    laboratories = models.ManyToManyField(
        Laboratory, related_name="regent_laboratories"
    )
    type_regent = models.CharField(
        max_length=100,
        choices=TYPEREGENTS,
        default="chemical",
        verbose_name=_("Type Regent"),
    )

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return self.user.username


class Buildings(AbstractOrganizationRef):
    name = models.CharField(
        verbose_name=_("Name"), max_length=255, null=False, blank=False
    )
    laboratories = models.ManyToManyField(
        Laboratory, verbose_name=_("Laboratories"), related_name="buildings", blank=True
    )
    is_asociaty_buildings = models.BooleanField(
        verbose_name=_("It is Associated with Buildings?"), default=False
    )
    nearby_buildings = models.ManyToManyField(
        "self",
        symmetrical=False,
        verbose_name=_("Nearby Buildings"),
        related_name="near_buildings_as",
        blank=True,
    )
    phone = models.CharField(
        verbose_name=_("Phone"), max_length=25, null=False, blank=False
    )
    manager = models.ForeignKey(
        User,
        verbose_name=_("Responsible"),
        related_name="manager",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    geolocation = GTPointField(
        default="9.895804362670006,-84.1552734375", zoom=15
    )
    regents = models.ManyToManyField(
        "risk_management.Regent",
        verbose_name=_("Regents Associated"),
        related_name="regents",
        blank=True,
    )
    has_water_resources = models.BooleanField(
        verbose_name=_("Presence of rivers, " "streams, springs and " "aquifers"),
        default=False,
    )
    has_nearby_sites = models.FileField(
        verbose_name=_(
            "Are there establishments with a "
            "large concentration of people "
            "that could be exposed to the "
            "risk of an accident?"
        ),
        upload_to=upload_files,
        null=True,
        blank=True,
    )
    area = models.FloatField(verbose_name=_("Area"), default=0.0)
    plans = models.FileField(
        verbose_name=_("Plans"), upload_to=upload_files, null=True, blank=True
    )
    security_plan = models.FileField(
        verbose_name=_("Security Plan"), upload_to=upload_files, null=True, blank=True
    )
    regulatory_plans = models.FileField(
        verbose_name=_("Regulatory Plans"),
        upload_to=upload_files,
        null=True,
        blank=True,
    )
    emergency_plan = models.FileField(
        verbose_name=_("Emergency Plan"), upload_to=upload_files, null=True, blank=True
    )

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return self.name


class Structure(AbstractOrganizationRef):
    name = models.CharField(
        max_length=150, verbose_name=_("Name"), null=False, blank=False
    )
    buildings = models.ManyToManyField(
        "risk_management.Buildings",
        verbose_name=_("Buildings"),
        related_name="structura_buildings",
    )
    type_structure = catalog.GTForeignKey(
        Catalog,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Type"),
        key_name="key",
        key_value="structure_type",
    )
    area = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Area/Volume")
    )
    measuerement_unit = catalog.GTForeignKey(
        Catalog,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Measurement Unit"),
        key_name="key",
        key_value="distance_unit",
        related_name="structure_measurement_unit",
    )
    geolocation = GTPointField(
        default="9.895804362670006,-84.1552734375",
        zoom=15,
        verbose_name=_("Geolocation"),
    )
    manager = models.ForeignKey(
        User,
        verbose_name=_("Responsible"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="structure_manager",
    )

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return self.name


class EstablishmentLogs(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    physical = models.FloatField(default=False)
    health = models.FloatField(default=False)
    environmental = models.FloatField(default=False)
    establishment_status = models.CharField(
        max_length=50, null=True, blank=True, verbose_name=_("Establishment Status")
    )
    table_content = models.JSONField(null=True, blank=True)
    xls_content = models.FileField(null=True, blank=True)
    date = models.DateTimeField(default=timezone.now, editable=True)

    def __str__(self):
        return self.establishment_status

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]


class Workday(AbstractOrganizationRef):
    WORKDAYS = (
        ("day shift", _("Day shift")),
        ("mixed shift", _("Mixed shift")),
        ("night shift", _("Night shift")),
    )
    workday = models.CharField(
        max_length=20, choices=WORKDAYS, verbose_name=_("Workday")
    )
    num_workers = models.SmallIntegerField(verbose_name=_("Number of workers (aprox)"))
    start_time = models.TimeField(verbose_name=_("Start Time"))
    end_time = models.TimeField(verbose_name=_("End Time"))
    risk_zone = models.ForeignKey(
        "risk_management.RiskZone",
        verbose_name=_("Risk Zone"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )


# ---------------------------------------------------------------------------
# IPER (Identificación de Peligros y Evaluación de Riesgos) — metodología INTE T55
# ---------------------------------------------------------------------------


class IPERRiskMatrix(models.Model):
    """Matriz Probabilidad x Consecuencia -> Nivel de riesgo (global, 9 filas).

    Las tres columnas referencian entradas del ``Catalog`` global vía
    ``GTForeignKey`` filtrando por ``key``. Se siembra en la migración.
    """

    probability = catalog.GTForeignKey(
        Catalog,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Probability"),
        key_name="key",
        key_value=KEY_PROBABILITY,
        related_name="iper_matrix_probability",
    )
    consequence = catalog.GTForeignKey(
        Catalog,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Consequence"),
        key_name="key",
        key_value=KEY_CONSEQUENCE,
        related_name="iper_matrix_consequence",
    )
    risk_level = catalog.GTForeignKey(
        Catalog,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Risk level"),
        key_name="key",
        key_value=KEY_RISK_LEVEL,
        related_name="iper_matrix_risk_level",
    )

    class Meta:
        verbose_name = _("IPER risk matrix")
        verbose_name_plural = _("IPER risk matrix")
        unique_together = ("probability", "consequence")
        ordering = ["pk"]

    def __str__(self):
        return "%s x %s -> %s" % (
            self.probability,
            self.consequence,
            self.risk_level,
        )


class IPERConfig(AbstractOrganizationRef):
    """Configuración de periodicidad del IPER. Vive en la organización raíz; puede
    sobreescribirse por laboratorio."""

    period_months = models.PositiveIntegerField(
        verbose_name=_("Update period (months)"), default=DEFAULT_PERIOD_MONTHS
    )
    reminder_days_before = models.PositiveIntegerField(
        verbose_name=_("Remind days before due date"),
        default=DEFAULT_REMINDER_DAYS_BEFORE,
    )
    is_active = models.BooleanField(verbose_name=_("Is active"), default=True)
    laboratory = models.ForeignKey(
        Laboratory,
        verbose_name=_("Laboratory"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="iper_configs",
    )

    class Meta:
        verbose_name = _("IPER configuration")
        verbose_name_plural = _("IPER configurations")
        ordering = ["pk"]

    def __str__(self):
        return "%s (%s)" % (self.organization, self.period_months)


class IPERAssessment(AbstractOrganizationRef):
    """Evaluación IPER de un laboratorio, versionada en el tiempo."""

    DRAFT = "draft"
    COMPLETED = "completed"
    OBSOLETE = "obsolete"
    STATUS = (
        (DRAFT, _("Draft")),
        (COMPLETED, _("Completed")),
        (OBSOLETE, _("Obsolete")),
    )

    PERIODIC = "periodic"
    ON_DEMAND = "on_demand"
    ZONE_REQUEST = "zone_request"
    SOURCES = (
        (PERIODIC, _("Periodic")),
        (ON_DEMAND, _("On demand")),
        (ZONE_REQUEST, _("Risk zone request")),
    )

    laboratory = models.ForeignKey(
        Laboratory,
        verbose_name=_("Laboratory"),
        on_delete=models.CASCADE,
        related_name="iper_assessments",
    )
    assessment_date = models.DateField(verbose_name=_("Assessment date"))
    responsible = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Responsible"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="iper_responsible",
    )
    status = models.CharField(
        max_length=20, choices=STATUS, default=DRAFT, verbose_name=_("Status")
    )
    version = models.PositiveIntegerField(verbose_name=_("Version"), default=1)
    previous = models.ForeignKey(
        "self",
        verbose_name=_("Previous version"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="next_versions",
    )
    due_date = models.DateField(
        verbose_name=_("Next update due date"), null=True, blank=True
    )
    source = models.CharField(
        max_length=20, choices=SOURCES, default=ON_DEMAND, verbose_name=_("Source")
    )
    is_anonymous = models.BooleanField(
        default=True,
        verbose_name=_("Anonymous"),
        help_text=_("When enabled, the laboratory name is hidden in public listings."),
    )

    class Meta:
        verbose_name = _("IPER assessment")
        verbose_name_plural = _("IPER assessments")
        ordering = ("-assessment_date", "-version", "-pk")
        permissions = [
            ("view_all_iper", _("Can view all IPER assessments in the organization")),
            ("request_iper", _("Can request laboratories to fill the IPER")),
            ("view_iper_dashboard", _("Can view the IPER risk dashboard")),
            (
                "manage_iper_catalog",
                _("Can manage IPER catalog and risk matrix (root org)"),
            ),
        ]

    def __str__(self):
        return "%s v%d (%s)" % (self.laboratory, self.version, self.assessment_date)

    def risk_level_counts(self):
        """Conteo de peligros por nivel de riesgo (description -> total)."""
        counts = {}
        for hazard in self.hazards.select_related("risk_level"):
            if hazard.risk_level_id:
                key = hazard.risk_level.description
                counts[key] = counts.get(key, 0) + 1
        return counts


class IPERHazard(models.Model):
    """Un peligro identificado dentro de una evaluación IPER."""

    assessment = models.ForeignKey(
        IPERAssessment,
        verbose_name=_("Assessment"),
        on_delete=models.CASCADE,
        related_name="hazards",
    )
    category = catalog.GTForeignKey(
        Catalog,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Hazard classification"),
        key_name="key",
        key_value=KEY_HAZARD_CATEGORY,
        related_name="iper_hazard_category",
    )
    description = models.TextField(verbose_name=_("Hazard description"))
    location = models.CharField(
        max_length=255, verbose_name=_("Hazard location"), blank=True
    )
    probability = catalog.GTForeignKey(
        Catalog,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Probability"),
        key_name="key",
        key_value=KEY_PROBABILITY,
        related_name="iper_hazard_probability",
    )
    consequence = catalog.GTForeignKey(
        Catalog,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Consequence"),
        key_name="key",
        key_value=KEY_CONSEQUENCE,
        related_name="iper_hazard_consequence",
    )
    risk_level = catalog.GTForeignKey(
        Catalog,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Risk level"),
        key_name="key",
        key_value=KEY_RISK_LEVEL,
        related_name="iper_hazard_risk_level",
        null=True,
        blank=True,
        editable=False,
    )
    risk_priority = models.SmallIntegerField(
        verbose_name=_("Risk priority"), default=0, editable=False
    )
    controls = models.TextField(verbose_name=_("Implemented controls"), blank=True)
    recommended_controls = models.TextField(
        verbose_name=_("Recommended controls"), blank=True
    )
    related_shelfobjects = models.ManyToManyField(
        ShelfObject,
        verbose_name=_("Related inventory items"),
        related_name="iper_hazards",
        blank=True,
    )

    class Meta:
        verbose_name = _("IPER hazard")
        verbose_name_plural = _("IPER hazards")
        ordering = ("-risk_priority", "pk")

    def save(self, *args, **kwargs):
        level, priority = compute_risk_level(self.probability, self.consequence)
        self.risk_level = level
        self.risk_priority = priority
        super().save(*args, **kwargs)

    def __str__(self):
        return self.description[:50]


class IPERObservation(models.Model):
    """Observación del analista de riesgo sobre una evaluación (sin aprobación)."""

    assessment = models.ForeignKey(
        IPERAssessment,
        verbose_name=_("Assessment"),
        on_delete=models.CASCADE,
        related_name="observations",
    )
    author = models.ForeignKey(
        get_user_model(),
        verbose_name=_("Author"),
        null=True,
        on_delete=models.SET_NULL,
        related_name="iper_observations",
    )
    text = models.TextField(verbose_name=_("Observation"))
    creation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("IPER observation")
        verbose_name_plural = _("IPER observations")
        ordering = ("-creation_date", "-pk")

    def __str__(self):
        return self.text[:50]
