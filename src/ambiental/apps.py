from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AmbientalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ambiental"
    verbose_name = _("Environmental management")

    def ready(self):
        from djgentelella.async_notification.registry import register_context

        from presentation.alerts import (
            TRIGGER_ABSOLUTE,
            TRIGGER_MISSING,
            TRIGGER_PERCENT,
            register_alert_process,
        )

        register_context(
            code="ambiental-consumption-alert",
            subject="{{ message }}",
            models={"point": "ambiental.MeasurementPoint", "alert": "ambiental.ConsumptionAlert"},
            extra_variables={
                "message": "Texto de la alerta",
                "link": "Enlace a la pantalla de alertas",
                "rule": "Regla que se disparó",
            },
        )
        register_alert_process(
            "ambiental.consumption",
            label=_("Atypical consumption"),
            evaluator="ambiental.alerts.evaluate_rule",
            triggers=(TRIGGER_PERCENT, TRIGGER_ABSOLUTE, TRIGGER_MISSING),
            permission="ambiental.add_measurementpoint",
            notification_code="ambiental-consumption-alert",
        )
