"""Ramas del módulo ambiental que las pruebas por funcionalidad no alcanzaban.

Cada clase prueba un comportamiento observable (respuesta, fila del reporte, error de
validación); no se limita a ejecutar líneas.
"""
import datetime
import json
from decimal import Decimal

from django.contrib.auth.models import AnonymousUser, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from django.urls import reverse

from ambiental import reports
from ambiental.access import BuildingAccess, building_permission_map
from ambiental.alerts import evaluate_rule, point_responsibles_of
from ambiental.ambiental_defaults import KEY_NORMALIZER, KEY_RESOURCE_TYPE, NORMALIZER_AREA, NORMALIZER_PERSON
from ambiental.api.mixins import AmbientalViewSet, resolve_path
from ambiental.api.serializers import ConsumptionAlertSerializer, OrganizationScopedSerializer, actions_for
from ambiental.forms import DashboardFilterForm, IndicatorReportForm
from ambiental.models import ConsumptionAlert, ConsumptionRecord, NormalizationBase
from ambiental.normalization import preload_bases
from ambiental.tests.test_building_access import BuildingAccessTestCase
from ambiental.tests.test_normalization import NormalizationTestCase
from ambiental.tests.test_reports import ReportTestCase
from auth_and_perms.models import ProfilePermission, Rol
from laboratory.models import Catalog
from presentation.alerts import KEY_ALERT_TRIGGER, TRIGGER_ABSOLUTE, TRIGGER_PERCENT
from presentation.models import AlertRule
from risk_management.models import Buildings

YEAR = "01/01/2026 - 31/12/2026"


class ConsumptionModelsTest(ReportTestCase):
    """Costos, validación de período y representación de los modelos."""

    def test_complete_costs_sin_cantidad_no_toca_nada(self):
        record = ConsumptionRecord(point=self.water_point, quantity=None, unit_cost=Decimal("2"))
        record.complete_costs()
        self.assertIsNone(record.total_cost)

    def test_complete_costs_deduce_el_unitario(self):
        record = ConsumptionRecord(point=self.water_point, quantity=Decimal("3"), total_cost=Decimal("10"))
        record.complete_costs()
        self.assertEqual(record.unit_cost, Decimal("3.3333"))

    def test_clean_rechaza_fin_antes_del_inicio(self):
        record = ConsumptionRecord(
            organization=self.organization, point=self.water_point, unit=self.m3, quantity=Decimal("1"),
            period_start=datetime.date(2026, 5, 10), period_end=datetime.date(2026, 5, 1),
        )
        with self.assertRaises(ValidationError) as error:
            record.clean()
        self.assertIn("period_end", error.exception.message_dict)

    def test_clean_rechaza_campos_extra_ajenos_al_recurso(self):
        record = ConsumptionRecord(
            organization=self.organization, point=self.water_point, unit=self.m3, quantity=Decimal("1"),
            period_start=datetime.date(2026, 5, 1), period_end=datetime.date(2026, 5, 31),
            extra_data={"inventado": "x"},
        )
        with self.assertRaises(ValidationError) as error:
            record.clean()
        self.assertIn("extra_data", error.exception.message_dict)
        record.extra_data = {}
        record.clean()

    def test_str_de_base_y_alerta(self):
        person = Catalog.objects.get(key=KEY_NORMALIZER, description=NORMALIZER_PERSON)
        base = NormalizationBase.objects.create(
            organization=self.organization, building=self.building, normalizer=person, year=2026, value=Decimal("5"),
        )
        self.assertEqual(str(base), "Edificio A 2026 %s: 5" % person)
        rule = AlertRule.objects.create(
            organization=self.organization, name="r", process="ambiental.consumption",
            trigger=Catalog.objects.get(key=KEY_ALERT_TRIGGER, description=TRIGGER_ABSOLUTE),
            threshold={"value": "1"}, level=AlertRule.MEDIUM, created_by=self.user,
        )
        alert = ConsumptionAlert.objects.create(
            organization=self.organization, rule=rule, point=self.water_point,
            period=datetime.date(2026, 1, 1), level=rule.level, message="Consumo alto",
        )
        self.assertEqual(str(alert), "Consumo alto")


class AccessHelpersTest(ReportTestCase):
    """Utilidades de acceso por edificio y de la base de las APIs."""

    def test_usuario_sin_perfil_no_tiene_permisos_por_edificio(self):
        user = User.objects.create_user(username="sinperfil")
        self.assertEqual(building_permission_map(user, self.organization), {})

    def test_has_sin_edificio_usa_el_permiso_de_organizacion(self):
        access = BuildingAccess(self.user, self.organization)
        self.assertTrue(access.has("ambiental.view_consumptionrecord", None))
        self.assertFalse(access.has("ambiental.permiso_inexistente", None))

    def test_resolve_path_corta_en_none(self):
        self.assertIsNone(resolve_path(None, "point__building"))
        self.assertEqual(resolve_path(self.record(self.water_point, 4, "1", self.m3), "point__building"), self.building)

    def test_building_from_data_cae_a_la_instancia(self):
        view = AmbientalViewSet()
        view.building_field = "point__building"
        record = self.record(self.water_point, 4, "1", self.m3)
        self.assertEqual(view.building_from_data({}, record), self.building)
        self.assertIsNone(view.building_from_data({}))
        self.assertEqual(view.building_from_data({"point": self.water_point}), self.building)

    def test_serializer_sin_acceso_por_edificio_usa_permisos_del_usuario(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        serializer = OrganizationScopedSerializer(context={"request": request})
        self.assertEqual(actions_for(serializer, "consumptionrecord", self.building), {"update": False, "destroy": False})
        self.assertEqual(
            list(serializer.visible_buildings(self.organization, "ambiental.view_consumptionrecord")), [self.building]
        )
        # El gancho base no acota nada: cada serializer concreto define el suyo.
        fields = {"point": object()}
        serializer.scope_fields(fields, self.organization)
        self.assertEqual(list(fields), ["point"])

    def test_alerta_sin_revisar_lleva_acciones_por_edificio(self):
        rule = AlertRule.objects.create(
            organization=self.organization, name="r", process="ambiental.consumption",
            trigger=Catalog.objects.get(key=KEY_ALERT_TRIGGER, description=TRIGGER_ABSOLUTE),
            threshold={"value": "1"}, level=AlertRule.MEDIUM, created_by=self.user,
        )
        alert = ConsumptionAlert.objects.create(
            organization=self.organization, rule=rule, point=self.water_point,
            period=datetime.date(2026, 1, 1), level=rule.level, message="m",
        )
        context = {"building_access": BuildingAccess(self.user, self.organization)}
        actions = ConsumptionAlertSerializer(alert, context=context).data["actions"]
        self.assertEqual(set(actions), {"update", "destroy", "review"})
        self.assertTrue(actions["review"])


class ReportBranchesTest(ReportTestCase):
    """Filtros y casos límite de los reportes ambientales."""

    def test_as_text_y_parse_period(self):
        self.assertEqual(reports.as_text(None), "")
        self.assertEqual(reports.parse_period("01/01/2026"), (None, None))
        self.assertEqual(reports.parse_period("a - b - c"), (None, None))
        self.assertEqual(reports.parse_period("no es - fecha"), (None, None))

    def test_detalle_filtra_por_edificio(self):
        other = Buildings.objects.create(name="Edificio C", phone="", organization=self.organization)
        self.record(self.make_point(building=other, code="C1"), 1, "7", self.m3)
        report = self.make_report("report_consumption_detail", building=[other.pk])
        self.assertEqual(reports.report_consumption_detail_html(report), 1)
        self.assertEqual(report.table_content["dataset"][0][0], "Edificio C")

    def test_resumen_con_punto_sin_edificio(self):
        point = self.make_point(code="SUELTO")
        self.record(point, 5, "3", self.m3)
        point.building = None
        point.save()
        report = self.make_report("report_consumption_summary")
        reports.report_consumption_summary_html(report)
        self.assertIn(["", "Agua", "2026-05", "3", "m³", ""], report.table_content["dataset"])

    def test_indicadores_por_edificio_sin_base_y_con_unidades_mezcladas(self):
        area = Catalog.objects.get(key=KEY_NORMALIZER, description=NORMALIZER_AREA)
        person = Catalog.objects.get(key=KEY_NORMALIZER, description=NORMALIZER_PERSON)
        NormalizationBase.objects.create(
            organization=self.organization, building=self.building, normalizer=person, year=2026, value=Decimal("5"),
        )
        liters = Catalog.objects.get(key="ambiental_measure_unit", description="L")
        self.record(self.water_point, 3, "5000", liters)
        report = self.make_report(
            "report_environmental_indicators", period=YEAR, normalizer=[area.pk, person.pk],
            building=[self.building.pk],
        )
        reports.report_environmental_indicators_html(report)
        rows = {(row[1], row[2]): row[7] for row in report.table_content["dataset"]}
        self.assertEqual(rows[("Agua", NORMALIZER_PERSON)], "Mixed units")
        self.assertEqual(rows[("Electricidad", NORMALIZER_AREA)], "No base")

    def test_comparacion_omite_edificios_sin_datos(self):
        Buildings.objects.create(name="Edificio vacío", phone="", organization=self.organization)
        report = self.make_report(
            "report_consumption_comparison", comparison_period="01/01/2026 - 31/01/2026",
            period="01/02/2026 - 28/02/2026", resource_type=[self.water.pk],
        )
        reports.report_consumption_comparison_html(report)
        self.assertEqual([row[0] for row in report.table_content["dataset"]], ["Edificio A"])

    def test_comparacion_con_cambio_de_unidad(self):
        liters = Catalog.objects.get(key="ambiental_measure_unit", description="L")
        point = self.make_point(code="LITROS")
        self.record(point, 3, "10", self.m3)
        self.record(point, 4, "10000", liters)
        from ambiental.indicators import compare_periods

        march, april = compare_periods(
            self.organization, self.water,
            [(datetime.date(2026, 3, 1), datetime.date(2026, 3, 31)),
             (datetime.date(2026, 4, 1), datetime.date(2026, 4, 30))],
        )
        self.assertTrue(april["mixed_units"])
        self.assertIsNone(april["absolute"])
        self.assertIsNone(april["percent"])


class FormBranchesTest(ReportTestCase):

    def test_reporte_de_indicadores_limpia_normalizadores_a_pks(self):
        person = Catalog.objects.get(key=KEY_NORMALIZER, description=NORMALIZER_PERSON)
        form = IndicatorReportForm(
            data={"name": "a", "title": "a", "organization": self.organization.pk,
                  "report_name": "report_environmental_indicators", "format": "html",
                  "period": YEAR, "normalizer": [person.pk]},
            org_pk=self.organization.pk, user=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["normalizer"], [person.pk])

    def test_filtro_del_panel_sin_edificios_visibles_usa_la_organizacion(self):
        form = DashboardFilterForm(organization=self.organization)
        self.assertEqual(list(form.fields["building"].queryset), [self.building])
        self.assertEqual(list(DashboardFilterForm().fields["building"].queryset), [])


class DashboardAndChartsTest(ReportTestCase):
    """Panel y gráficos con filtros por edificio y recurso."""

    def setUp(self):
        super().setUp()
        self.building_c = Buildings.objects.create(name="Edificio C", phone="", organization=self.organization)
        self.record(self.make_point(building=self.building_c, code="C-AGUA"), 2, "5", self.m3)

    def chart(self, name, **params):
        url = reverse(name + "-detail", kwargs={"pk": self.organization.pk})
        return self.client.get(url, {"org_pk": self.organization.pk, "year": 2026, **params})

    def test_panel_filtrado_por_edificio(self):
        response = self.client.get(
            reverse("ambiental:ambiental_dashboard", kwargs={"org_pk": self.organization.pk}),
            {"year": 2026, "building": self.building_c.pk, "resource_type": self.water.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual([(c["resource"], c["quantity"]) for c in response.context["cards"]], [("Agua", Decimal("5"))])
        self.assertIn("building=%s" % self.building_c.pk, response.context["consumption_chart"])

    def test_listado_de_grafico_no_existe(self):
        url = reverse("ambientalmonthlyconsumptionchart-list")
        self.assertEqual(self.client.get(url, {"org_pk": self.organization.pk}).status_code, 404)

    def test_filtro_invalido_responde_400(self):
        self.assertEqual(self.chart("ambientalmonthlyconsumptionchart", year=1).status_code, 400)

    def test_consumo_filtrado_por_recurso(self):
        data = self.chart("ambientalmonthlyconsumptionchart", resource_type=self.electricity.pk).json()
        self.assertEqual([d["label"] for d in data["data"]["datasets"]], ["Electricidad kWh"])

    def test_costo_ignora_registros_sin_costo(self):
        data = self.chart("ambientalmonthlycostchart").json()
        series = {d["label"]: d["data"] for d in data["data"]["datasets"]}
        # El registro del edificio C no tiene costo: febrero queda con el de A.
        self.assertEqual(series["Agua"][1], 45000.0)

    def test_ranking_de_un_edificio(self):
        person = Catalog.objects.get(key=KEY_NORMALIZER, description=NORMALIZER_PERSON)
        for building in (self.building, self.building_c):
            NormalizationBase.objects.create(
                organization=self.organization, building=building, normalizer=person, year=2026, value=Decimal("5"),
            )
        data = self.chart("ambientalbuildingrankingchart", building=self.building_c.pk).json()
        self.assertEqual(data["data"]["labels"], ["Edificio C"])
        self.assertEqual(data["data"]["datasets"][0]["data"], [1.0])


class SelectsTest(BuildingAccessTestCase):
    """Autocompletes: organización inválida o ajena devuelven vacío."""

    def results(self, name, **params):
        response = self.client.get(reverse(name + "-list"), params)
        self.assertEqual(response.status_code, 200)
        return response.json()["results"]

    def test_organizacion_ausente_o_ajena(self):
        """Con el permiso global (no por rol) pasa el permiso de modelo, pero sin una
        organización propia en la URL el autocomplete no devuelve nada."""
        from django.contrib.auth.models import Permission

        outsider = self.building_user("permiso_global", {})
        outsider.user_permissions.add(Permission.objects.get(codename="view_measurementpoint"))
        self.client.force_login(outsider)
        self.assertEqual(self.results("ambiental_buildings"), [])
        self.assertEqual(self.results("ambiental_buildings", org_pk=self.other_organization.pk), [])

    def test_organizacion_inexistente(self):
        # `register_lookups` no devuelve la clase decorada: se usa la base.
        from ambiental.gtselects import AmbientalOrganizationSelect

        view = AmbientalOrganizationSelect()
        view.request = RequestFactory().get("/", {"org_pk": 999999})
        view.request.user = self.user
        self.assertIsNone(view.get_organization())

    def test_laboratorios_del_usuario_por_edificio(self):
        self.assertEqual(
            [r["text"] for r in self.results("ambiental_laboratories", org_pk=self.organization.pk)],
            ["Laboratorio de Química"],
        )
        # Con rol solo en el edificio B (sin laboratorios) no ve ninguno.
        self.client.force_login(self.building_user("solo_b", {self.building_b: "Analista ambiental"}))
        self.assertEqual(self.results("ambiental_laboratories", org_pk=self.organization.pk), [])

    def test_usuarios_de_la_organizacion(self):
        person = self.building_user("persona_sel", {})
        person.first_name, person.last_name = "Ana", "Mora"
        person.save()
        texts = [r["text"] for r in self.results("ambiental_users", org_pk=self.organization.pk)]
        self.assertIn("Ana Mora (persona_sel)", texts)
        self.assertIn("ambiental", texts)


class BuildingAccessUpdateTest(BuildingAccessTestCase):
    """Editar y borrar filas de «Acceso por edificio»."""

    def setUp(self):
        super().setUp()
        self.person = self.building_user("editable", {self.building: "Analista ambiental"})
        self.permission = ProfilePermission.objects.get(
            profile=self.person.profile, content_type=ContentType.objects.get_for_model(Buildings),
        )

    def roles(self, *names):
        return list(Rol.objects.filter(name__in=names).values_list("pk", flat=True))

    def test_editar_roles_y_no_mover_de_edificio(self):
        data = {"user": self.person.pk, "building": self.building_b.pk, "rol": self.roles("Analista ambiental")}
        response = self.put("api-buildingaccess-detail", data, pk=self.permission.pk)
        self.assertEqual(response.status_code, 400)
        self.assertIn("building", response.json())

        data["building"] = self.building.pk
        data["rol"] = self.roles("Encargado de registro ambiental")
        response = self.put("api-buildingaccess-detail", data, pk=self.permission.pk)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            list(self.permission.rol.values_list("name", flat=True)), ["Encargado de registro ambiental"]
        )

    def test_borrar_acceso(self):
        response = self.client.delete(self.url("api-buildingaccess-detail", pk=self.permission.pk))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ProfilePermission.objects.filter(pk=self.permission.pk).exists())


class ConsumptionRecordBranchesTest(ReportTestCase):
    """Validaciones del alta de consumo que dependen del recurso y del documento."""

    def post(self, data):
        url = reverse("ambiental:api-consumptionrecord-list", kwargs={"org_pk": self.organization.pk})
        return self.client.post(url, data=json.dumps(data), content_type="application/json")

    def test_recurso_sin_unidad_por_defecto_exige_unidad(self):
        vapor = Catalog.objects.create(key=KEY_RESOURCE_TYPE, description="Vapor")
        point = self.make_point(code="VAPOR", resource_type=vapor)
        response = self.post({"point": point.pk, "period_start": "2026-06-01", "period_end": "2026-06-30",
                              "quantity": "1"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("unit", response.json())

    def test_documento_borrado_queda_vacio(self):
        response = self.post({"point": self.water_point.pk, "period_start": "2026-06-01",
                              "period_end": "2026-06-30", "quantity": "1",
                              "document": json.dumps({"actions": "delete"})})
        self.assertEqual(response.status_code, 201, response.content)
        record = ConsumptionRecord.objects.get(point=self.water_point, period_end=datetime.date(2026, 6, 30))
        self.assertFalse(record.document)


class AlertBranchesTest(ReportTestCase):
    """Reglas sobre puntos sin registros, promedios nulos y responsables del edificio."""

    def rule(self, trigger, threshold):
        return AlertRule.objects.create(
            organization=self.organization, name="Consumo", process="ambiental.consumption",
            trigger=Catalog.objects.get(key=KEY_ALERT_TRIGGER, description=trigger),
            threshold=threshold, level=AlertRule.MEDIUM, created_by=self.user, create_task=False,
        )

    def test_responsables_sin_edificio_y_con_encargado(self):
        self.assertEqual(point_responsibles_of(None), [])
        self.building.manager = self.user
        self.building.save()
        self.assertEqual(point_responsibles_of(self.building), [self.user])

    def test_punto_sin_registros_y_promedio_cero(self):
        self.make_point(code="NUEVO")  # sin registros: se salta
        zero = self.make_point(code="CERO")
        self.record(zero, 1, "0", self.m3)
        self.record(zero, 2, "0", self.m3)
        self.record(zero, 3, "10", self.m3)
        rule = self.rule(TRIGGER_PERCENT, {"percent": "20"})
        alerts = evaluate_rule(rule, today=datetime.date(2026, 4, 5))
        self.assertNotIn(zero, [alert.point for alert in alerts])
        self.assertEqual(ConsumptionAlert.objects.filter(point__code__in=["NUEVO", "CERO"]).count(), 0)


class NormalizationPreloadUpdateTest(NormalizationTestCase):
    """La precarga por API registra también las bases que actualiza."""

    def test_precarga_actualiza_bases_deducidas(self):
        preload_bases(self.organization, 2026)
        self.building.area = 1500
        self.building.save()
        url = reverse("ambiental:api-normalizationbase-preload", kwargs={"org_pk": self.organization.pk})
        response = self.client.post(url, data=json.dumps({"year": 2026}), content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["updated"], 1)
