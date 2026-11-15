"""
Cartas de control de equipos (fase 3): servicio, API, gráficos y alertas.

``laboratory/equipment/control.py``, ``api.py`` (ControlMethod/Point/Measurement) y
``charts.py``. Los datos imitan el registro de la balanza LB-127 (punto de 5 g, cinco
lecturas, error de indicación de las pesas 0.0032 g).
"""
import datetime
from decimal import Decimal as D

from django.urls import reverse

from laboratory.equipment import control
from laboratory.models import ControlLimits, ControlMeasurement, ControlMethod, ControlPoint
from laboratory.tests.test_cov_api_equipment_records import RegistrosEquipoBase
from pending_tasks.models import PendingTask
from presentation.models import AlertEvent, AlertRule

LECTURAS = [
    ["5", "5", "5", "5", "5"],
    ["5", "4.99", "5", "5", "5"],
    ["5", "5", "4.99", "5", "5"],
    ["4.99", "5", "5.01", "5", "5"],
    ["5", "4.99", "5", "5", "5"],
    ["5.01", "5", "5", "4.99", "5"],
]


class ControlBase(RegistrosEquipoBase):

    def setUp(self):
        super().setUp()
        self.metodo = ControlMethod.objects.create(name="Balanzas X-R n=5", organization=self.org, subgroup_size=5)
        self.punto = ControlPoint.objects.create(
            shelfobject=self.equipo, method=self.metodo, name="P1 (5 g)", nominal_value=D("5"), unit="g",
            correction=D("0.0032"), tolerance=D("0.02"), organization=self.org,
            reference_standard="Pesas COC 051-2024",
        )

    def registrar(self, valores, fecha, punto=None, **extra):
        registro = ControlMeasurement(point=punto or self.punto, measured_on=fecha, values=valores, **extra)
        return control.save_measurement(registro, self.user)

    def referencia(self):
        for dia, valores in enumerate(LECTURAS, start=1):
            self.registrar(valores, datetime.date(2026, 1, dia))
        return control.recalculate_limits(self.punto, datetime.date(2026, 1, 1), datetime.date(2026, 1, 31), self.user)


class MetodoTest(ControlBase):

    def test_constantes_de_la_tabla_y_editables(self):
        self.assertEqual((self.metodo.a2, self.metodo.d3, self.metodo.d4), (D("0.577"), D("0"), D("2.114")))
        propio = ControlMethod.objects.create(name="Como el Excel", organization=self.org, d4=D("2.225"))
        self.assertEqual(propio.d4, D("2.225"))
        self.assertEqual(propio.a2, D("0.577"))

    def test_i_mr_fuerza_una_lectura(self):
        imr = ControlMethod.objects.create(name="pHmetro", organization=self.org, chart_type=ControlMethod.I_MR,
                                           subgroup_size=5)
        self.assertEqual(imr.subgroup_size, 1)
        self.assertEqual(imr.a2, D("2.660"))


class ServicioTest(ControlBase):

    def test_registro_calcula_media_rango_y_corregida(self):
        registro = self.registrar(["4.99", "5", "5.01", "5", "5"], datetime.date(2026, 1, 1))
        self.assertEqual(registro.mean, D("5"))
        self.assertEqual(registro.range, D("0.02"))
        self.assertEqual(registro.corrected_mean, D("4.9968"))
        self.assertIsNone(registro.limits)
        self.assertFalse(registro.out_of_control)

    def test_cantidad_de_lecturas(self):
        with self.assertRaises(control.ControlError):
            self.registrar(["5", "5"], datetime.date(2026, 1, 1))
        with self.assertRaises(control.ControlError):
            self.registrar(["5", "5", "x", "5", "5"], datetime.date(2026, 1, 1))

    def test_limites_del_periodo_de_referencia(self):
        limites = self.referencia()
        self.assertEqual(limites.subgroups, 6)
        self.assertTrue(limites.is_current)
        self.assertEqual(limites.constants["d4"], "2.114")
        self.assertLess(limites.lcl, limites.center)
        self.assertLess(limites.center, limites.ucl)
        # Los registros del período quedan evaluados con esos límites.
        self.assertTrue(all(r.limits_id == limites.pk for r in ControlMeasurement.objects.all()))

    def test_fuera_de_control_y_de_aceptacion(self):
        self.referencia()
        dentro = self.registrar(["5", "5", "5", "5", "5"], datetime.date(2026, 2, 1))
        self.assertFalse(dentro.out_of_control)
        fuera = self.registrar(["5.05", "5.06", "5.05", "5.05", "5.06"], datetime.date(2026, 2, 2))
        self.assertTrue(fuera.out_of_control)
        self.assertTrue(fuera.out_of_acceptance)  # |5.0528 - 5| > 0.02

    def test_recalcular_guarda_el_historial(self):
        primeros = self.referencia()
        self.registrar(["5.01", "5.01", "5.01", "5.01", "5.01"], datetime.date(2026, 2, 1))
        nuevos = control.recalculate_limits(self.punto, datetime.date(2026, 1, 1), datetime.date(2026, 2, 28), self.user)
        primeros.refresh_from_db()
        self.assertFalse(primeros.is_current)
        self.assertEqual(self.punto.current_limits(), nuevos)
        self.assertEqual(ControlLimits.objects.filter(point=self.punto).count(), 2)

    def test_periodo_sin_registros(self):
        with self.assertRaises(control.ControlError):
            control.recalculate_limits(self.punto, datetime.date(2030, 1, 1), datetime.date(2030, 1, 2))

    def test_i_mr_rango_movil(self):
        imr = ControlMethod.objects.create(name="pHmetro", organization=self.org, chart_type=ControlMethod.I_MR)
        ph = ControlPoint.objects.create(shelfobject=self.equipo, method=imr, name="pH 7", nominal_value=7,
                                         organization=self.org)
        primero = self.registrar(["7.01"], datetime.date(2026, 1, 1), punto=ph)
        segundo = self.registrar(["6.98"], datetime.date(2026, 1, 3), punto=ph)
        self.assertIsNone(primero.range)
        self.assertEqual(segundo.range, D("0.03"))
        # Un registro intercalado recalcula el rango móvil del siguiente.
        self.registrar(["7.00"], datetime.date(2026, 1, 2), punto=ph)
        segundo.refresh_from_db()
        self.assertEqual(segundo.range, D("0.02"))


class AlertaDeControlTest(ControlBase):

    def setUp(self):
        super().setUp()
        self.regla = AlertRule.objects.create(
            organization=self.org, name="Cartas", process=control.PROCESS, trigger=control.TRIGGER_OUT_OF_CONTROL,
            threshold={}, created_by=self.user, create_task=True,
        )

    def test_fuera_de_control_avisa_y_la_accion_lo_resuelve(self):
        self.referencia()
        fuera = self.registrar(["5.05", "5.06", "5.05", "5.05", "5.06"], datetime.date(2026, 2, 2),
                               responsible=self.profile)
        evento = AlertEvent.objects.get(rule=self.regla)
        self.assertEqual(evento.content_object, fuera)
        self.assertIn("P1 (5 g)", evento.message)
        self.assertIn(str(self.punto.pk), evento.link)
        tarea = PendingTask.objects.get(name=evento.message[:255])
        # Volver a guardar no duplica la alerta.
        control.save_measurement(fuera, self.user)
        self.assertEqual(AlertEvent.objects.filter(rule=self.regla).count(), 1)
        fuera.deviation = "Pesa contaminada"
        fuera.corrective_action = "Se limpió la pesa y se repitió la verificación"
        control.save_measurement(fuera, self.user)
        evento.refresh_from_db()
        tarea.refresh_from_db()
        self.assertIsNotNone(evento.resolved_at)
        self.assertEqual(tarea.status, PendingTask.FINISHED)

    def test_dentro_de_control_no_avisa(self):
        self.referencia()
        self.registrar(["5", "5", "5", "5", "5"], datetime.date(2026, 2, 1))
        self.assertFalse(AlertEvent.objects.filter(rule=self.regla).exists())


class ApiDeControlTest(ControlBase):

    def kwargs(self, **extra):
        return {"org_pk": self.org.pk, "lab_pk": self.lab.pk, **extra}

    def test_metodo_desde_la_api_con_constantes_por_defecto(self):
        url = reverse("laboratory:api-equipment-control-method-list", kwargs=self.kwargs())
        response = self.post(url, {"name": "pHmetros", "chart_type": "i_mr", "subgroup_size": 1})
        self.assertEqual(response.status_code, 201, response.content)
        metodo = ControlMethod.objects.get(name="pHmetros")
        self.assertEqual(metodo.organization, self.org)
        self.assertEqual(metodo.a2, D("2.660"))
        filas = self.client.get(url).json()["data"]
        self.assertIn("pHmetros", [fila["name"] for fila in filas])

    def test_x_r_con_n_fuera_de_rango(self):
        url = reverse("laboratory:api-equipment-control-method-list", kwargs=self.kwargs())
        response = self.post(url, {"name": "Malo", "chart_type": "xbar_r", "subgroup_size": 12})
        self.assertEqual(response.status_code, 400)

    def test_metodo_en_uso_no_se_borra(self):
        url = reverse("laboratory:api-equipment-control-method-detail", kwargs=self.kwargs(pk=self.metodo.pk))
        self.assertEqual(self.client.delete(url).status_code, 400)
        self.assertTrue(ControlMethod.objects.filter(pk=self.metodo.pk).exists())

    def test_punto_y_registros(self):
        url = reverse("laboratory:api-equipment-control-point-list", kwargs=self.kwargs(shelfobject=self.equipo.pk))
        response = self.post(url, {"method": self.metodo.pk, "name": "P2 (25 g)", "nominal_value": "25",
                                   "correction": "0", "is_active": True})
        self.assertEqual(response.status_code, 201, response.content)
        punto = ControlPoint.objects.get(name="P2 (25 g)")
        medir = reverse("laboratory:api-equipment-control-measurement-list",
                        kwargs=self.kwargs(shelfobject=self.equipo.pk, point=punto.pk))
        response = self.post(medir, {"measured_on": "05/01/2026", "values": "25,1; 25 25.1 25; 24.9",
                                     "responsible": self.profile.pk})
        self.assertEqual(response.status_code, 201, response.content)
        registro = ControlMeasurement.objects.get(point=punto)
        self.assertEqual(registro.values, ["25.1", "25", "25.1", "25", "24.9"])
        self.assertEqual(registro.range, D("0.2"))
        response = self.post(medir, {"measured_on": "06/01/2026", "values": "25; 25"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("values", response.json())
        fila = self.client.get(url).json()["data"][0]
        self.assertIn("/control/", fila["chart_url"])

    def test_recalcular_limites_desde_la_api(self):
        for dia, valores in enumerate(LECTURAS, start=1):
            self.registrar(valores, datetime.date(2026, 1, dia))
        url = reverse("laboratory:api-equipment-control-point-recalculate-limits",
                      kwargs=self.kwargs(shelfobject=self.equipo.pk, pk=self.punto.pk))
        response = self.post(url, {"baseline_from": "01/01/2026", "baseline_to": "31/01/2026"})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIsNotNone(self.punto.current_limits())
        vacio = self.post(url, {"baseline_from": "01/01/2030", "baseline_to": "31/01/2030"})
        self.assertEqual(vacio.status_code, 400)

    def test_registros_de_otro_equipo(self):
        url = reverse("laboratory:api-equipment-control-measurement-list",
                      kwargs=self.kwargs(shelfobject=13, point=self.punto.pk))
        self.assertEqual(self.client.get(url).status_code, 404)


class GraficosTest(ControlBase):

    def grafico(self, basename):
        url = reverse("%s-detail" % basename, kwargs={"pk": self.punto.pk})
        response = self.client.get(url, {"organization": self.org.pk, "laboratory": self.lab.pk})
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_medias_con_limites_discontinuos_y_puntos_rojos(self):
        self.registrar(["5", "5", "5", "5", "5"], datetime.date(2025, 12, 31))  # antes de los límites
        self.referencia()
        self.registrar(["5.05", "5.06", "5.05", "5.05", "5.06"], datetime.date(2026, 2, 2))
        data = self.grafico("equipmentcontrolmeanschart")
        valores, lcs, lc, lci = data["data"]["datasets"]
        self.assertEqual(len(data["data"]["labels"]), 8)
        self.assertEqual(lcs["borderDash"], [6, 4])
        self.assertIsNone(lcs["data"][0])  # sin límites todavía: hueco
        self.assertEqual(valores["pointBackgroundColor"][-1], "rgb(216, 15, 53)")
        self.assertNotEqual(valores["pointBackgroundColor"][1], "rgb(216, 15, 53)")

    def test_rangos(self):
        self.referencia()
        data = self.grafico("equipmentcontrolrangeschart")
        valores = data["data"]["datasets"][0]["data"]
        self.assertEqual(valores[3], 0.02)

    def test_laboratorio_ajeno(self):
        url = reverse("equipmentcontrolmeanschart-detail", kwargs={"pk": self.punto.pk})
        response = self.client.get(url, {"organization": self.org.pk, "laboratory": 2})
        self.assertEqual(response.status_code, 404)


class PaginasDeControlTest(ControlBase):

    def test_carta_y_metodos_con_el_rol_tecnico(self):
        from auth_and_perms.management.commands.update_roles import sync_roles
        from auth_and_perms.roles import ROLES
        from presentation.tests.test_platform_parameters import make_role_user

        sync_roles(["tecnico_laboratorio"])
        tecnico = make_role_user("tecnico", self.org, ROLES["tecnico_laboratorio"])
        self.client.force_login(tecnico)
        carta = reverse("laboratory:equipment_control_point",
                        kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": self.equipo.pk, "point": self.punto.pk})
        response = self.client.get(carta)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "P1 (5 g)")
        # El JS de la tabla recibe la URL real de la API (no una variable de otro bloque).
        api = reverse("laboratory:api-equipment-control-measurement-list",
                      kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "shelfobject": self.equipo.pk,
                              "point": self.punto.pk})
        self.assertContains(response, 'list_url: "%s"' % api)
        metodos = reverse("laboratory:equipment_control_methods", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(metodos)
        self.assertEqual(response.status_code, 200)
        api_metodos = reverse("laboratory:api-equipment-control-method-list",
                              kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertContains(response, 'list_url: "%s"' % api_metodos)
        medir = reverse("laboratory:api-equipment-control-measurement-list",
                        kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "shelfobject": self.equipo.pk,
                                "point": self.punto.pk})
        response = self.post(medir, {"measured_on": "05/01/2026", "values": "5 5 5 5 5"})
        self.assertEqual(response.status_code, 201, response.content)
