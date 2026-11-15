"""
Alertas de actividades de equipo por vencer (``laboratory/equipment/alerts.py``),
sobre ``djgentelella.alerts`` vía ``presentation.alerts``.
"""
import datetime

from django.test import TestCase
from djgentelella.async_notification.models import EmailNotification

from laboratory.equipment.alerts import PROCESS, evaluate_rule
from laboratory.models import (
    EquipmentActivityPlan as Plan,
    OrganizationStructure,
    ShelfObject,
    ShelfObjectCalibrate,
    ShelfObjectEquipmentCharacteristics as Characteristics,
)
from django.contrib.auth.models import User
from pending_tasks.models import PendingTask
from presentation.alerts import TRIGGER_DUE, run_alert_rules
from presentation.models import AlertEvent, AlertRule

HOY = datetime.date(2026, 11, 15)


class AlertasDeEquipoTest(TestCase):
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        self.user = User.objects.get(username="admin")
        self.user.email = "admin@example.com"
        self.user.save()
        self.org = OrganizationStructure.objects.get(pk=1)
        self.equipo = ShelfObject.objects.get(pk=15)
        Characteristics.objects.filter(shelfobject=self.equipo).update(
            custodian=self.user.profile, internal_code="LB-127"
        )
        self.rule = AlertRule.objects.create(
            organization=self.org, name="Equipos", process=PROCESS, trigger=TRIGGER_DUE,
            threshold={"days_before": 30, "overdue_repeat_days": 0}, created_by=self.user,
            notify_responsible=True, create_task=True,
        )
        self.plan = Plan.objects.create(
            shelfobject=self.equipo, activity_kind=Plan.CALIBRATION, interval_value=12,
            reminder_days_before=30, organization=self.org,
        )
        self.calibrar(datetime.date(2025, 12, 10))  # vence el 2026-12-10: 25 días después de HOY

    def correos(self):
        # Las señales del fixture también encolan correos: solo los de la plantilla de equipos.
        return EmailNotification.objects.filter(subject__startswith="Equipos:")

    def calibrar(self, fecha):
        return ShelfObjectCalibrate.objects.create(
            shelfobject=self.equipo, calibration_date=fecha, calibrate_name="Metrología",
            created_by=self.user,
        )

    def test_avisa_por_correo_y_tarea_al_custodio(self):
        eventos = evaluate_rule(self.rule, today=HOY)
        self.assertEqual(len(eventos), 1)
        evento = eventos[0]
        self.assertEqual(evento.content_object, self.plan)
        self.assertEqual(evento.organization, self.org)
        self.assertIn("LB-127", evento.message)
        self.assertIn("10/12/2026", evento.message)
        self.assertIn("#pane-calibrate", evento.link)
        self.assertEqual(evento.recipients, ["admin"])
        correo = self.correos().get()
        self.assertEqual(correo.recipients, ["admin@example.com"])
        self.assertTrue(PendingTask.objects.filter(status=PendingTask.PENDING).exists())

    def test_evaluar_dos_veces_no_duplica(self):
        evaluate_rule(self.rule, today=HOY)
        evaluate_rule(self.rule, today=HOY + datetime.timedelta(days=1))
        self.assertEqual(AlertEvent.objects.count(), 1)
        self.assertEqual(self.correos().count(), 1)

    def test_fuera_del_margen_del_programa_no_avisa(self):
        Plan.objects.filter(pk=self.plan.pk).update(reminder_days_before=10)
        self.assertEqual(evaluate_rule(self.rule, today=HOY), [])

    def test_registrar_la_calibracion_resuelve_la_alerta_y_la_tarea(self):
        evento = evaluate_rule(self.rule, today=HOY)[0]
        calibracion = self.calibrar(datetime.date(2026, 11, 20))
        evento.refresh_from_db()
        self.assertIsNotNone(evento.resolved_at)
        self.assertEqual(evento.resolution, calibracion)
        self.assertEqual(evento.resolved_by, self.user)
        self.assertFalse(PendingTask.objects.exclude(status=PendingTask.FINISHED).exists())
        # Con la fecha nueva (2027-11-20) ya no hay nada por vencer.
        self.assertEqual(evaluate_rule(self.rule, today=HOY), [])

    def test_una_calibracion_vieja_no_resuelve(self):
        evento = evaluate_rule(self.rule, today=HOY)[0]
        self.calibrar(datetime.date(2024, 1, 1))  # no es la última: no mueve la fecha
        evento.refresh_from_db()
        self.assertIsNone(evento.resolved_at)

    def test_vencida_repite_segun_la_regla(self):
        self.rule.threshold = {"days_before": 30, "overdue_repeat_days": 7}
        self.rule.save()
        vencido = datetime.date(2027, 1, 5)
        evento = evaluate_rule(self.rule, today=vencido)[0]
        self.assertIn("overdue", evento.message)
        AlertEvent.objects.filter(pk=evento.pk).update(
            last_notified_at=evento.last_notified_at - datetime.timedelta(days=8)
        )
        evaluate_rule(self.rule, today=vencido)
        self.assertEqual(AlertEvent.objects.count(), 1)
        self.assertEqual(self.correos().count(), 2)

    def test_equipo_dado_de_baja_o_plan_inactivo_no_avisa(self):
        Characteristics.objects.filter(shelfobject=self.equipo).update(
            equipment_status=Characteristics.DECOMMISSIONED
        )
        self.assertEqual(evaluate_rule(self.rule, today=HOY), [])
        Characteristics.objects.filter(shelfobject=self.equipo).update(
            equipment_status=Characteristics.IN_SERVICE
        )
        Plan.objects.filter(pk=self.plan.pk).update(is_active=False)
        self.assertEqual(evaluate_rule(self.rule, today=HOY), [])

    def test_otra_organizacion_no_ve_el_equipo(self):
        otra = OrganizationStructure.objects.create(name="Otra")
        self.rule.organization = otra
        self.rule.save()
        self.assertEqual(evaluate_rule(self.rule, today=HOY), [])

    def test_la_tarea_programada_evalua_las_reglas_del_proceso(self):
        self.assertEqual(run_alert_rules(PROCESS), 1)
