from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class AbstractOrganizationRef(models.Model):
    organization = models.ForeignKey(
        "laboratory.OrganizationStructure", null=True, on_delete=models.CASCADE
    )
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        abstract = True


class AbstractRegistry(models.Model):
    creation_date = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        abstract = True


class FeedbackEntry(models.Model):
    title = models.CharField(_("Title"), max_length=255)
    explanation = models.TextField(_("Explanation"), null=True, blank=True)
    related_file = models.FileField(
        _("Related file"), upload_to="media/feedback_entries/", null=True, blank=True
    )
    laboratory_id = models.IntegerField(
        default=0, null=True, verbose_name=_("Laboratory id")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("User"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("Feedback entry")
        verbose_name_plural = _("Feedback entries")

    def __str__(self):
        return "%s" % (self.title,)


class Donation(models.Model):
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    email = models.CharField(max_length=100, verbose_name=_("Email"))
    amount = models.CharField(max_length=10, verbose_name=_("Amount"))
    details = models.TextField(max_length=255, verbose_name=_("Details"))
    is_donator = models.BooleanField(
        default=True, verbose_name=_("Add me to the donators list")
    )
    is_paid = models.BooleanField(default=False, verbose_name=_("Is paid?"))
    donation_date = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Donation date")
    )

    class Meta:
        verbose_name = _("Donation")
        verbose_name_plural = _("Donations")

    def __str__(self):
        return f"{self.name}: ${self.amount}"


class Tutorial(models.Model):
    CHAPTER_CHOICES = [
        ("GENERAL", _("General")),
        ("PERMISOS", _("Permissions")),
        ("LABORATORIOS", _("Laboratories")),
        ("SUSTANCIAS", _("Substances")),
        ("PROCEDIMIENTOS", _("Procedures")),
        ("RESERVACIONES", _("Reservations")),
        ("TAREAS", _("Scheduled Tasks")),
    ]

    title = models.CharField(max_length=255, verbose_name=_("Title"))
    slug = models.SlugField(unique=True)
    description = models.TextField(verbose_name=_("Description"), blank=True)
    url_name = models.CharField(
        max_length=500,
        verbose_name=_("URL name(s)"),
        help_text=_(
            "Django URL name where this tutorial applies. "
            "Comma-separated for multiple pages."
        ),
    )
    target_roles = models.ManyToManyField(
        "auth_and_perms.Rol",
        blank=True,
        verbose_name=_("Target roles"),
        help_text=_("Roles that should see this tutorial. Empty = all users."),
    )
    chapter = models.CharField(
        max_length=20,
        choices=CHAPTER_CHOICES,
        default="GENERAL",
        verbose_name=_("Chapter"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    auto_start = models.BooleanField(
        default=False,
        verbose_name=_("Auto start"),
        help_text=_(
            "Start automatically on first visit " "(if user has tutorials enabled)"
        ),
    )
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))

    class Meta:
        verbose_name = _("Tutorial")
        verbose_name_plural = _("Tutorials")
        ordering = ["chapter", "order"]

    def __str__(self):
        return self.title


class TutorialStep(models.Model):
    STEP_TYPE_CHOICES = [
        ("HIGHLIGHT", _("Highlight element")),
        ("MODAL", _("Modal dialog")),
        ("POPOVER", _("Popover tooltip")),
    ]
    POSITION_CHOICES = [
        ("top", _("Top")),
        ("bottom", _("Bottom")),
        ("left", _("Left")),
        ("right", _("Right")),
    ]

    tutorial = models.ForeignKey(
        Tutorial,
        related_name="steps",
        on_delete=models.CASCADE,
        verbose_name=_("Tutorial"),
    )
    order = models.PositiveIntegerField(verbose_name=_("Order"))
    step_key = models.SlugField(max_length=100, verbose_name=_("Step key"))
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    content = models.TextField(verbose_name=_("Content"), help_text=_("Supports HTML"))
    step_type = models.CharField(
        max_length=10,
        choices=STEP_TYPE_CHOICES,
        default="MODAL",
        verbose_name=_("Step type"),
    )
    css_selector = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("CSS selector"),
        help_text=_("CSS selector of the target element to highlight"),
    )
    position = models.CharField(
        max_length=10,
        choices=POSITION_CHOICES,
        default="bottom",
        verbose_name=_("Position"),
    )
    action_url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Action URL"),
        help_text=_("URL to navigate after this step (for cross-page tutorials)"),
    )
    image = models.ImageField(
        blank=True, null=True, upload_to="tutorial_images/", verbose_name=_("Image")
    )

    class Meta:
        verbose_name = _("Tutorial step")
        verbose_name_plural = _("Tutorial steps")
        unique_together = [("tutorial", "step_key"), ("tutorial", "order")]
        ordering = ["order"]

    def __str__(self):
        return f"{self.tutorial.slug} - {self.order}. {self.title}"


class TutorialProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User")
    )
    tutorial = models.ForeignKey(
        Tutorial, on_delete=models.CASCADE, verbose_name=_("Tutorial")
    )
    completed = models.BooleanField(default=False, verbose_name=_("Completed"))
    current_step = models.PositiveIntegerField(
        default=0, verbose_name=_("Current step")
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Started at"))
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Completed at")
    )
    dismissed = models.BooleanField(
        default=False,
        verbose_name=_("Dismissed"),
        help_text=_("User temporarily dismissed this tutorial"),
    )

    class Meta:
        verbose_name = _("Tutorial progress")
        verbose_name_plural = _("Tutorial progress")
        unique_together = [("user", "tutorial")]

    def __str__(self):
        return f"{self.user} - {self.tutorial}"


class QRModel(models.Model):
    qr_url = models.TextField(null=True, verbose_name=_("QR Url"))
    qr_image = models.TextField(null=True, verbose_name=_("Image QR on SVG"))
    b64_image = models.TextField(null=True, verbose_name=_("Base64 Image QR"))

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    organization = models.ForeignKey(
        "laboratory.OrganizationStructure", null=True, on_delete=models.CASCADE
    )


class SystemParameter(AbstractOrganizationRef):
    """El valor propio de un parámetro del sistema en una organización.

    Qué parámetros existen, su tipo, su valor por defecto y quién los puede cambiar lo
    declara ``presentation/parameters.py``: aquí solo se guarda el valor que una
    organización fija. Sin fila, la organización hereda el de sus ancestros o el
    valor por defecto (ver ``presentation.parameters.resolve_parameter``).
    """

    key = models.CharField(max_length=150, verbose_name=_("Key"))
    raw_value = models.TextField(blank=True, default="", verbose_name=_("Value"))

    class Meta:
        verbose_name = _("System parameter")
        verbose_name_plural = _("System parameters")
        ordering = ["key"]
        unique_together = ("organization", "key")

    def __str__(self):
        return "%s = %s" % (self.key, self.raw_value)

    @property
    def value(self):
        from presentation.parameters import cast_value, get_definition

        return cast_value(get_definition(self.key)["type"], self.raw_value)

    def clean(self):
        from django.core.exceptions import ValidationError

        from presentation.parameters import PARAMETERS, cast_value

        super().clean()
        if self.key not in PARAMETERS:
            raise ValidationError({"key": _("Unknown parameter.")})
        try:
            cast_value(PARAMETERS[self.key]["type"], self.raw_value)
        except (TypeError, ValueError):
            raise ValidationError({"raw_value": _("Invalid value for this parameter.")})


class NotificationSetting(AbstractOrganizationRef):
    """Cómo manda una organización el correo de un proceso registrado.

    Las plantillas de ``djgentelella.async_notification`` son globales; esta fila
    permite a una organización (y a sus hijas) apagar un correo o reemplazar su asunto y
    su mensaje sin tocar la plantilla de las demás. Ver
    ``presentation.notifications.send_process_email``.
    """

    code = models.SlugField(max_length=150, verbose_name=_("Code"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is active"))
    override_subject = models.CharField(
        max_length=500, blank=True, default="", verbose_name=_("Subject")
    )
    override_message = models.TextField(blank=True, default="", verbose_name=_("Message"))

    class Meta:
        verbose_name = _("Notification setting")
        verbose_name_plural = _("Notification settings")
        ordering = ["code"]
        unique_together = ("organization", "code")

    def __str__(self):
        return self.code


class AlertRule(AbstractOrganizationRef):
    """Una regla de alerta de un proceso: qué vigilar, cuándo disparar y a quién avisar.

    El proceso (``process``) y cómo se evalúa lo registra la app dueña con
    ``presentation.alerts.register_alert_process``; la plataforma no conoce los
    procesos. ``threshold`` guarda el umbral según el disparador (ver
    ``presentation.alerts.THRESHOLD_FIELDS``).
    """

    INFO = "info"
    MEDIUM = "medium"
    CRITICAL = "critical"
    LEVELS = (
        (INFO, _("Informative")),
        (MEDIUM, _("Medium")),
        (CRITICAL, _("Critical")),
    )

    name = models.CharField(max_length=255, verbose_name=_("Name"))
    process = models.CharField(max_length=150, verbose_name=_("Process"))
    trigger = models.ForeignKey(
        "laboratory.Catalog",
        on_delete=models.PROTECT,
        limit_choices_to={"key": "alert_trigger"},
        verbose_name=_("Trigger"),
        related_name="alert_rules",
    )
    threshold = models.JSONField(default=dict, blank=True, verbose_name=_("Threshold"))
    level = models.CharField(max_length=20, choices=LEVELS, default=MEDIUM, verbose_name=_("Level"))
    notification_code = models.SlugField(
        max_length=150, blank=True, default="", verbose_name=_("Email")
    )
    notify_roles = models.ManyToManyField(
        "auth_and_perms.Rol", blank=True, verbose_name=_("Notify roles")
    )
    notify_responsible = models.BooleanField(default=True, verbose_name=_("Notify the responsible"))
    create_task = models.BooleanField(default=True, verbose_name=_("Create pending task"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is active"))

    class Meta:
        verbose_name = _("Alert rule")
        verbose_name_plural = _("Alert rules")
        ordering = ["process", "name"]

    def __str__(self):
        return self.name


class AlertEvent(models.Model):
    """Cada vez que una regla se disparó: el historial que sirve para calibrarla."""

    rule = models.ForeignKey(
        AlertRule, on_delete=models.CASCADE, related_name="events", verbose_name=_("Alert rule")
    )
    organization = models.ForeignKey(
        "laboratory.OrganizationStructure", on_delete=models.CASCADE, null=True
    )
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    message = models.TextField(verbose_name=_("Message"))
    level = models.CharField(max_length=20, choices=AlertRule.LEVELS, verbose_name=_("Level"))
    link = models.CharField(max_length=500, blank=True, default="", verbose_name=_("Link"))
    recipients = models.JSONField(default=list, blank=True, verbose_name=_("Recipients"))
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Date"))

    class Meta:
        verbose_name = _("Alert event")
        verbose_name_plural = _("Alert events")
        ordering = ["-creation_date"]

    def __str__(self):
        return self.message
