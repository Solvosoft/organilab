"""Ramas de gestión de riesgo que las demás pruebas no tocaban.

- `get_incompatibility_alerts` con códigos H repetidos (el inventario los repite
  cuando dos sustancias comparten indicación).
- `iper_duplicate` copiando los objetos de estante asociados a cada peligro.
- `send_iper_update_reminders` descartando laboratorios: versión vieja del mismo
  laboratorio, sin vencimiento, vencimiento lejano y sin responsable.
"""
import datetime

from django.urls import reverse

from laboratory.models import Catalog, Furniture, LaboratoryRoom, Object, Shelf, ShelfObject
from pending_tasks.models import PendingTask
from risk_management.compatibility_utils import get_incompatibility_alerts
from risk_management.models import IPERAssessment, IPERConfig, IPERHazard
from risk_management.iper_defaults import KEY_CONSEQUENCE, KEY_HAZARD_CATEGORY, KEY_PROBABILITY
from risk_management.tasks import send_iper_update_reminders
from risk_management.tests.base import RiskTestCase, crear_usuario, indicacion

HOY = datetime.date.today()


class AlertasConCodigosRepetidosTest(RiskTestCase):

    def test_un_par_repetido_se_informa_una_vez(self):
        """Con H225 dos veces el par (H225, H272) aparece dos veces en el doble
        bucle: el conjunto `seen` evita la alerta duplicada."""
        indicacion("H225")
        indicacion("H272")
        alertas = get_incompatibility_alerts(["H225", "H272", "H225"])
        self.assertEqual(len(alertas), 1)
        self.assertEqual((alertas[0]["code_a"], alertas[0]["code_b"]), ("H225", "H272"))


class IPERBaseCov(RiskTestCase):

    def evaluacion(self, laboratory=None, **kwargs):
        datos = dict(
            organization=self.organization, laboratory=laboratory or self.lab,
            assessment_date=HOY, responsible=self.user, created_by=self.user,
        )
        datos.update(kwargs)
        return IPERAssessment.objects.create(**datos)


class DuplicadoConInventarioTest(IPERBaseCov):

    def test_el_duplicado_conserva_los_objetos_del_peligro(self):
        original = self.evaluacion(status=IPERAssessment.COMPLETED)
        peligro = IPERHazard.objects.create(
            assessment=original,
            category=Catalog.objects.get(key=KEY_HAZARD_CATEGORY, description="Químico"),
            description="Vapores",
            probability=Catalog.objects.get(key=KEY_PROBABILITY, description="Alta"),
            consequence=Catalog.objects.get(key=KEY_CONSEQUENCE, description="Extremadamente Dañino"),
        )
        sala = LaboratoryRoom.objects.create(laboratory=self.lab, name="Sala")
        mueble = Furniture.objects.create(
            labroom=sala, name="Mueble", dataconfig="",
            type=Catalog.objects.create(key="furniture_type", description="Estante"),
        )
        estante = Shelf.objects.create(
            furniture=mueble, name="E1", type=Catalog.objects.create(key="container_type", description="Caja")
        )
        objeto = ShelfObject.objects.create(
            object=Object.objects.create(code="R1", name="Reactivo", type=Object.REACTIVE, organization=self.organization),
            shelf=estante, quantity=1,
            measurement_unit=Catalog.objects.create(key="units", description="u"),
            in_where_laboratory=self.lab, created_by=self.user,
        )
        peligro.related_shelfobjects.add(objeto)

        response = self.client.post(
            reverse("riskmanagement:iper_duplicate", kwargs={"org_pk": self.organization.pk, "pk": original.pk}),
            {"laboratory": self.lab.pk, "assessment_date": "2026-03-01"},
        )
        self.assertEqual(response.status_code, 200)
        nueva = IPERAssessment.objects.exclude(pk=original.pk).get()
        self.assertEqual(list(nueva.hazards.get().related_shelfobjects.all()), [objeto])
        # El original no pierde su relación al clonar el peligro.
        self.assertEqual(list(peligro.related_shelfobjects.all()), [objeto])


class RecordatoriosIPERTest(IPERBaseCov):

    def vencimiento(self, evaluacion, due_date):
        # `save()` recalcula el vencimiento; se fija directo en la base.
        IPERAssessment.objects.filter(pk=evaluacion.pk).update(due_date=due_date)

    def test_solo_avisa_a_la_ultima_version_que_vence_con_responsable(self):
        IPERConfig.objects.create(organization=self.organization, period_months=12, reminder_days_before=30)
        responsable = crear_usuario("responsable_iper", self.organization)
        self.lab.responsible = responsable
        self.lab.save()
        pronto = HOY + datetime.timedelta(days=5)

        # Mismo laboratorio, dos versiones: solo cuenta la más reciente.
        self.vencimiento(self.evaluacion(version=1), pronto)
        self.vencimiento(self.evaluacion(version=2), pronto)
        # Laboratorio cuya última evaluación no vence.
        sin_vencimiento = self.crear_laboratorio("Sin vencimiento", self.organization)
        sin_vencimiento.responsible = responsable
        sin_vencimiento.save()
        self.vencimiento(self.evaluacion(laboratory=sin_vencimiento), None)
        # Laboratorio que vence dentro de un año: todavía no toca avisar.
        lejano = self.crear_laboratorio("Vence lejos", self.organization)
        lejano.responsible = responsable
        lejano.save()
        self.vencimiento(self.evaluacion(laboratory=lejano), HOY + datetime.timedelta(days=365))
        # Laboratorio que vence pronto pero no tiene responsable.
        huerfano = self.crear_laboratorio("Sin responsable", self.organization)
        self.vencimiento(self.evaluacion(laboratory=huerfano), pronto)

        antes = PendingTask.objects.count()
        send_iper_update_reminders()
        self.assertEqual(PendingTask.objects.count(), antes + 1)
