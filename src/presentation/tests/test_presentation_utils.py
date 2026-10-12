"""Piezas sueltas de presentation: tareas Celery, sonda de salud, retroalimentación,
modelos, parámetros, eje de roles, admin, QR y alertas."""
import datetime
from decimal import Decimal
from unittest import mock

from django.contrib.admin.sites import site
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from djgentelella.async_notification.models import EmailNotification

from auth_and_perms.models import Profile
from laboratory.models import Laboratory, OrganizationStructure
from presentation import alerts, parameters, role_catalog, tasks
from presentation.models import (
    AlertEvent,
    AlertRule,
    Donation,
    FeedbackEntry,
    NotificationSetting,
    SystemParameter,
    Tutorial,
    TutorialProgress,
    TutorialStep,
)
from presentation.tests import test_platform_alerts as alert_base
from presentation.utils import build_qr_instance, get_qr_by_instance, update_qr_instance

EVALUADOS = []


def evaluador_roto(rule, **kwargs):
    raise RuntimeError("regla rota")


def evaluador_sano(rule, **kwargs):
    EVALUADOS.append(rule.pk)


class TareasCeleryTest(TestCase):

    def test_procesa_las_notificaciones_pendientes(self):
        notification = EmailNotification.objects.create(
            subject="Aviso", message="<p>Hola</p>", recipients=["ana@example.com"])
        tasks.process_email_notifications.delay()
        notification.refresh_from_db()
        self.assertEqual(notification.status, "sent")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["ana@example.com"])

    def test_limpia_las_sesiones_vencidas(self):
        Session.objects.create(session_key="vencida", session_data="",
                               expire_date=timezone.now() - datetime.timedelta(days=1))
        tasks.clean_session.delay()
        self.assertFalse(Session.objects.filter(session_key="vencida").exists())

    def test_las_demas_tareas_llaman_a_su_comando(self):
        for task, command in ((tasks.remove_stale_contenttypes, "remove_stale_contenttypes"),
                              (tasks.delete_expired_uploads, "delete_expired_uploads")):
            with self.subTest(command=command), mock.patch("presentation.tasks.call_command") as call:
                task.delay()
                call.assert_called_once_with(command)


class SondaDeSaludTest(TestCase):

    def test_responde_ok_y_falla_a_pedido(self):
        response = self.client.get(reverse("check_ok"))
        self.assertEqual(response.content, b"ok")
        with self.assertRaises(ZeroDivisionError):
            self.client.get(reverse("check_ok") + "?raise=1")


class RetroalimentacionTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(username="root", password="pass")
        Profile.objects.create(user=cls.user)

    def setUp(self):
        self.client.force_login(self.user)

    def test_el_formulario_recuerda_organizacion_y_laboratorio(self):
        response = self.client.get(reverse("feedback") + "?org_pk=3&lab_pk=7")
        self.assertEqual((response.context["org_pk"], response.context["lab_pk"]), (3, 7))

    def test_ids_invalidos_y_correo_fallido_no_impiden_guardar(self):
        data = {"title": "Falla", "explanation": '<img src="/media/a.png">', "org_pk": "x", "lab_pk": "y",
                "related_file": ContentFile(b"hola", name="hola.pdf")}
        with mock.patch("presentation.views.send_email_from_template", side_effect=RuntimeError("smtp")):
            response = self.client.post(reverse("feedback"), data=data)
        self.assertRedirects(response, reverse("index"), fetch_redirect_response=False)
        entry = FeedbackEntry.objects.get()
        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.laboratory_id, 0)


class StrDeModelosTest(TestCase):

    def test_representaciones(self):
        user = User.objects.create_user(username="ana")
        organization = OrganizationStructure.objects.create(name="Org")
        tutorial = Tutorial.objects.create(title="Inicio", slug="inicio", url_name="index")
        step = TutorialStep.objects.create(tutorial=tutorial, order=1, step_key="a", title="Paso", content="x")
        progress = TutorialProgress.objects.create(user=user, tutorial=tutorial)
        rule = AlertRule.objects.create(organization=organization, name="Regla", process="p",
                                        trigger=alert_base.Catalog.objects.filter(key=alerts.KEY_ALERT_TRIGGER).first())
        self.assertEqual(str(FeedbackEntry(title="Falla")), "Falla")
        self.assertEqual(str(Donation(name="Ana", amount="10")), "Ana: $10")
        self.assertEqual(str(tutorial), "Inicio")
        self.assertEqual(str(step), "inicio - 1. Paso")
        self.assertEqual(str(progress), "ana - Inicio")
        self.assertEqual(str(SystemParameter(key="k", raw_value="v")), "k = v")
        self.assertEqual(str(NotificationSetting(code="aviso")), "aviso")
        self.assertEqual(str(AlertEvent(rule=rule, message="Se disparó")), "Se disparó")


class ParametrosTest(TestCase):
    key = "ambiental.alert_window_months"

    def test_conversion_de_cada_tipo(self):
        cast = parameters.cast_value
        self.assertEqual(cast(parameters.FLOAT, "1.5"), 1.5)
        self.assertEqual(cast(parameters.DECIMAL, "2.50"), Decimal("2.50"))
        self.assertEqual(cast(parameters.DATE, "2026-01-31"), datetime.date(2026, 1, 31))
        self.assertEqual(cast(parameters.JSON, '{"a": 1}'), {"a": 1})
        self.assertEqual(cast(parameters.STR, "  texto "), "texto")
        for data_type, raw in ((parameters.BOOL, "quizá"), (parameters.DECIMAL, "uno")):
            with self.subTest(data_type=data_type), self.assertRaises(ValueError):
                cast(data_type, raw)

    def test_serializacion(self):
        serialize = parameters.serialize_value
        self.assertEqual(serialize(parameters.INT, None), "")
        self.assertEqual(serialize(parameters.BOOL, True), "true")
        self.assertEqual(serialize(parameters.DATE, datetime.date(2026, 1, 2)), "2026-01-02")
        self.assertEqual(serialize(parameters.JSON, {"á": 1}), '{"á": 1}')

    def test_valor_invalido_guardado_cae_al_ancestro_y_se_cachea_por_peticion(self):
        root = OrganizationStructure.objects.create(name="Raíz")
        child = OrganizationStructure.objects.create(name="Hija", parent=root)
        SystemParameter.objects.create(organization=root, key=self.key, raw_value="6")
        SystemParameter.objects.create(organization=child, key=self.key, raw_value="seis")
        resolved = parameters.resolve_parameter(child, self.key)
        self.assertEqual((resolved["value"], resolved["origin"]), (6, parameters.ORIGIN_INHERITED))

        request = RequestFactory().get("/")
        self.assertEqual(parameters.get_parameter(child, self.key, request=request), 6)
        SystemParameter.objects.filter(organization=root).update(raw_value="9")
        self.assertEqual(parameters.get_parameter(child, self.key, request=request), 6)
        self.assertEqual(parameters.get_parameter(child, self.key), 9)

    def test_valor_y_validacion_del_modelo(self):
        organization = OrganizationStructure.objects.create(name="Org")
        parameter = SystemParameter(organization=organization, key=self.key, raw_value="4")
        self.assertEqual(parameter.value, 4)
        parameter.full_clean()
        for key, raw, field in (("no.existe", "1", "key"), (self.key, "cuatro", "raw_value")):
            with self.subTest(key=key):
                parameter.key, parameter.raw_value = key, raw
                with self.assertRaises(ValidationError) as error:
                    parameter.clean()
                self.assertIn(field, error.exception.message_dict)


class EjeDeRolesTest(TestCase):

    def test_busqueda_por_id_y_por_nombre(self):
        self.assertEqual(role_catalog.get_role("estudiante").name, "Estudiante")
        with self.assertRaises(LookupError):
            role_catalog.get_role("no-existe")
        self.assertEqual(role_catalog.resolve_name("Estudiante").id, "estudiante")
        self.assertIsNone(role_catalog.resolve_name("Gestión de objetos"))
        self.assertEqual(role_catalog.canonical_ids(), tuple(r.id for r in role_catalog.CANONICAL_ROLES))
        self.assertIn("estudiante", role_catalog.canonical_ids())


class FeedbackAdminTest(TestCase):

    def test_muestra_explicacion_y_archivo(self):
        model_admin = site._registry[FeedbackEntry]
        entry = FeedbackEntry(title="Falla", explanation='<img src="../media/a.png">')
        entry.related_file.name = "feedback/a.pdf"
        rendered = model_admin.explanation_rendered(entry)
        self.assertIn('src="/media/a.png"', rendered)
        self.assertIn('href="/media/feedback/a.pdf"', model_admin.file_preview(entry))
        vacio = FeedbackEntry(title="Vacía")
        self.assertEqual(model_admin.explanation_rendered(vacio), "-")
        self.assertEqual(model_admin.file_preview(vacio), "-")


class CodigoQRTest(TestCase):

    def test_actualizar_reemplaza_el_qr_existente(self):
        organization = OrganizationStructure.objects.create(name="Org")
        laboratory = Laboratory.objects.create(name="Lab", organization=organization)
        first = build_qr_instance("https://a.example/1", laboratory, organization.pk)
        updated = update_qr_instance("https://a.example/2", laboratory, organization.pk)
        self.assertEqual(updated.pk, first.pk)
        self.assertEqual(updated.qr_url, "https://a.example/2")
        self.assertIn("<svg", updated.qr_image)
        self.assertEqual(get_qr_by_instance(laboratory, organization), updated)


class AlertasBordesTest(alert_base.AlertTestCase):

    def test_disparador_desconocido(self):
        with self.assertRaises(ValueError):
            alerts.validate_threshold("Desconocido", "5")

    def test_regla_sin_creador_no_crea_tarea(self):
        rule = self.make_rule(created_by=None, create_task=True)
        with mock.patch.object(alerts.logger, "warning") as warning:
            event = alerts.fire_alert(rule, "Sin creador")
        self.assertEqual(event.message, "Sin creador")
        self.assertFalse(alert_base.PendingTask.objects.exists())
        self.assertIn("no tiene creador", warning.call_args.args[0])

    def test_proceso_desconocido_y_regla_rota(self):
        self.assertEqual(alerts.run_alert_rules("no.existe"), 0)
        alerts.register_alert_process("platform.roto", label="Roto",
                                      evaluator="presentation.tests.test_presentation_utils.evaluador_roto",
                                      triggers=(alerts.TRIGGER_PERCENT,))
        alerts.register_alert_process("platform.sano", label="Sano",
                                      evaluator="presentation.tests.test_presentation_utils.evaluador_sano",
                                      triggers=(alerts.TRIGGER_PERCENT,))
        self.addCleanup(alerts.ALERT_PROCESSES.pop, "platform.roto")
        self.addCleanup(alerts.ALERT_PROCESSES.pop, "platform.sano")
        self.make_rule(process="platform.roto")
        sana = self.make_rule(process="platform.sano", name="Sana")
        with mock.patch.object(alerts.logger, "exception") as exception:
            self.assertEqual(alerts.run_alert_rules("platform.roto"), 1)
        exception.assert_called_once()
        self.assertEqual(alerts.run_alert_rules("platform.sano"), 1)
        self.assertIn(sana.pk, EVALUADOS)
