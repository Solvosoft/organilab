from django.apps import AppConfig


class LaboratoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'laboratory'

    def ready(self):
        self.register_equipment_alerts()
        import laboratory.signals
        from djgentelella.async_notification.registry import register_context

        super(LaboratoryConfig, self).ready()
        register_context(
            code='shelf-object-in-limit',
            subject='The shelf object called {{shelf_object.object.name}} '
                    'reached its limit quantity',
            models={
                'shelf_object': 'laboratory.ShelfObject',
                'labroom': 'laboratory.LaboratoryRoom',
                'laboratory': 'laboratory.Laboratory',
            },
            extra_variables={
                'domain': 'Site domain, used to build links',
                'blockurl': 'URL to block these notifications',
            },
        )
        register_context(
            code='expiring-reactives',
            subject='Expiring reactives - {{ laboratory.name }}',
            models={
                'laboratory': 'laboratory.Laboratory',
            },
            extra_variables={
                'shelf_objects': 'List of expiring shelf objects',
                'domain': 'Site domain, used to build links',
            },
        )
        register_context(
            code='lab_or_org_request_created',
            subject='{{ subject|safe }}',
            models={},
            extra_variables={
                'subject': 'Rendered subject of the request',
                'body': 'Rendered body of the request',
            },
        )
        register_context(
            code='lab_or_org_request_status_changed',
            subject='{{ subject|safe }}',
            models={},
            extra_variables={
                'subject': 'Rendered subject of the request',
                'body': 'Rendered body of the request',
            },
        )

    def register_equipment_alerts(self):
        """Alertas de actividades de equipo por vencer (laboratory/equipment/alerts.py)."""
        from django.utils.translation import gettext_lazy as _
        from djgentelella.async_notification.registry import register_context

        from presentation.alerts import TRIGGER_DUE, register_alert_process
        from laboratory.equipment.alerts import NOTIFICATION_CODE, PROCESS

        import laboratory.equipment.signals  # noqa: F401
        from laboratory.equipment.control import register_alerts as register_control_alerts

        register_control_alerts()
        register_context(
            code="equipment-control-alert",
            subject="{{ message }}",
            models={"point": "laboratory.ControlPoint", "measurement": "laboratory.ControlMeasurement"},
            extra_variables={"message": "Texto de la alerta", "link": "Enlace a la carta de control",
                             "rule": "Regla que se disparó"},
        )

        register_context(
            code=NOTIFICATION_CODE,
            subject="{{ message }}",
            models={"plan": "laboratory.EquipmentActivityPlan", "equipment": "laboratory.ShelfObject"},
            extra_variables={
                "message": "Texto de la alerta",
                "link": "Enlace a la ficha del equipo",
                "rule": "Regla que se disparó",
                "status": "upcoming, due u overdue",
                "next_due": "Fecha de vencimiento",
            },
        )
        register_alert_process(
            PROCESS,
            label=_("Equipment due activities"),
            evaluator="laboratory.equipment.alerts.evaluate_rule",
            triggers=(TRIGGER_DUE,),
            permission="laboratory.change_shelfobject",
            notification_code=NOTIFICATION_CODE,
        )
