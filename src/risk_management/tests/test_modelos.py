"""Modelos de riesgo, sus utilidades y las etiquetas de plantilla."""
import datetime
from unittest import mock

from django.test import SimpleTestCase

from laboratory.models import Catalog
from risk_management.iper_defaults import KEY_CONSEQUENCE, KEY_HAZARD_CATEGORY, KEY_PROBABILITY
from risk_management.models import (
    EstablishmentLogs,
    IncidentReport,
    IPERAssessment,
    IPERConfig,
    IPERHazard,
    IPERObservation,
    IPERRiskMatrix,
    PriorityConstrain,
    Regent,
    Structure,
    ZoneType,
    upload_notification_copy,
)
from risk_management.models_utils import (
    PriorityCalculator,
    add_months,
    compute_risk_level,
    get_iper_config,
)
from risk_management.templatetags.risk_tags import get_incidents, get_incidents_by_zone
from risk_management.tests.base import RiskTestCase
from risk_management.utils import get_regents_from_organization


class PriorityCalculatorTest(SimpleTestCase):

    def operar(self, operation, left, value, right=None):
        calculadora = PriorityCalculator()
        calculadora.operation = operation
        calculadora.left_value = left
        calculadora.right_value = right
        return calculadora.operate(value)

    def test_operaciones(self):
        casos = [
            ("<", 5, 6, None, True),
            ("<", 5, 5, None, False),
            ("<=", 5, 5, None, True),
            ("=", 5, 5, None, True),
            (">", 5, 4, None, True),
            (">=", 5, 5, None, True),
            ("!", 5, 4, None, True),
            ("<>", 1, 5, 3, True),
            ("=<>=", 5, 5, 5, True),
            ("<>=", 1, 5, 5, True),
            ("=<>", 5, 5, 3, True),
            ("<<", 1, 5, 10, True),
            ("<<", 1, 15, 10, False),
            ("=<<=", 5, 10, 10, True),
            ("<<=", 1, 10, 10, True),
            ("=<<", 5, 5, 10, True),
            ("=<<", 5, 10, 10, False),
            # Sin valor derecho se compara contra 0.
            ("<<", -5, -1, None, True),
            ("operación desconocida", 1, 1, None, False),
        ]
        for operation, left, value, right, esperado in casos:
            with self.subTest(operation=operation, left=left, value=value, right=right):
                self.assertIs(self.operar(operation, left, value, right), esperado)


class ModelosTest(RiskTestCase):

    def test_prioridad_por_defecto_de_un_tipo_de_zona(self):
        mayor_a_10 = PriorityConstrain.objects.create(
            operation="<", left_value=10, priority=4, organization=self.organization
        )
        tipo = ZoneType.objects.create(name="Comercial")
        tipo.priority_validator.add(mayor_a_10)
        self.assertEqual(tipo.get_priority(50), 4)
        self.assertEqual(tipo.get_priority(5), 1)
        self.assertEqual(str(tipo), "Comercial")

    def test_representaciones(self):
        regente = Regent.objects.create(user=self.user, organization=self.organization)
        self.assertEqual(str(regente), self.user.username)
        estructura = Structure.objects.create(
            name="Tanque", area=10, organization=self.organization,
            type_structure=Catalog.objects.create(key="structure_type", description="Tanque"),
            measuerement_unit=Catalog.objects.create(key="distance_unit", description="m"),
        )
        self.assertEqual(str(estructura), "Tanque")
        log = EstablishmentLogs(establishment_status="Riesgo menor")
        self.assertEqual(str(log), "Riesgo menor")
        incidente = IncidentReport(short_description="Derrame")
        self.assertEqual(str(incidente), "Derrame")
        celda = IPERRiskMatrix.objects.select_related(
            "probability", "consequence", "risk_level"
        ).first()
        self.assertEqual(
            str(celda), "%s x %s -> %s" % (celda.probability, celda.consequence, celda.risk_level)
        )
        config = IPERConfig.objects.create(organization=self.organization, period_months=6)
        self.assertEqual(str(config), "%s (6)" % self.organization)
        evaluacion = IPERAssessment.objects.create(
            organization=self.organization, laboratory=self.lab,
            assessment_date=datetime.date(2026, 3, 1), version=2,
        )
        self.assertEqual(str(evaluacion), "%s v2 (2026-03-01)" % self.lab)
        peligro = IPERHazard.objects.create(
            assessment=evaluacion,
            category=Catalog.objects.filter(key=KEY_HAZARD_CATEGORY).first(),
            probability=Catalog.objects.filter(key=KEY_PROBABILITY).first(),
            consequence=Catalog.objects.filter(key=KEY_CONSEQUENCE).first(),
            description="x" * 60,
        )
        self.assertEqual(str(peligro), "x" * 50)
        observacion = IPERObservation.objects.create(assessment=evaluacion, text="y" * 60)
        self.assertEqual(str(observacion), "y" * 50)

    def test_nombre_de_la_copia_de_notificacion(self):
        with mock.patch("risk_management.models.datetime") as reloj:
            reloj.now.return_value = datetime.datetime(2026, 10, 12, 8, 30, 15)
            ruta = upload_notification_copy(None, "Copia CNCI.final.pdf")
        self.assertEqual(ruta, "notifications/20261012083015/copia-cncifinal.pdf")

    def test_regentes_de_la_organizacion(self):
        regente = Regent.objects.create(user=self.user, organization=self.organization)
        Regent.objects.create(user=self.sin_permisos, organization=self.other)
        self.assertEqual(get_regents_from_organization(self.organization.pk), [regente.user.pk])

    def test_etiquetas_de_incidentes(self):
        incidente = IncidentReport.objects.create(
            short_description="Derrame", incident_date=datetime.date.today(),
            causes="", infraestructure_impact="", people_impact="", environment_impact="",
            result_of_plans="", mitigation_actions="", recomendations="",
        )
        incidente.buildings.add(self.building)
        self.assertEqual(get_incidents(self.building.pk), 1)
        self.assertEqual(get_incidents(self.other_building.pk), 0)
        self.assertEqual(get_incidents_by_zone(self.zone.pk), self.zone.pk)


class IPERConfigAplicableTest(RiskTestCase):

    def test_sobrescritura_por_laboratorio(self):
        de_la_org = IPERConfig.objects.create(organization=self.organization)
        del_lab = IPERConfig.objects.create(
            organization=self.organization, laboratory=self.lab, period_months=3
        )
        IPERConfig.objects.create(
            organization=self.organization, laboratory=self.other_lab, is_active=False
        )
        self.assertEqual(get_iper_config(self.organization, self.lab), del_lab)
        self.assertEqual(get_iper_config(self.organization, self.other_lab), de_la_org)
        self.assertEqual(get_iper_config(self.organization), de_la_org)

    def test_sin_organizacion(self):
        self.assertIsNone(get_iper_config(None))

    def test_add_months_y_nivel_de_riesgo_sin_datos(self):
        self.assertIsNone(add_months(None, 3))
        probabilidad = Catalog.objects.filter(key=KEY_PROBABILITY).first()
        self.assertEqual(compute_risk_level(None, probabilidad), (None, 0))
        consecuencia = Catalog.objects.create(key=KEY_CONSEQUENCE, description="Sin celda")
        self.assertEqual(compute_risk_level(probabilidad, consecuencia), (None, 0))
