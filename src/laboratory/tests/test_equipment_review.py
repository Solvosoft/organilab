"""
Correcciones de la revisión del módulo de equipos ISO/IEC 17025 (plan, sección 9).

Reglas de alerta por defecto, corrección guardada en cada registro de control, alertas
que no quedan colgadas, vecinos del rango móvil, límites fijos, ventana de las cartas,
programa sin fecha, calibración no conforme, historial de estado y baja.
"""
import datetime
from decimal import Decimal as D

from django.urls import reverse

from laboratory.equipment import alerts, control
from laboratory.equipment.charts import DEFAULT_WINDOW
from laboratory.models import (
    ControlLimits,
    ControlMeasurement,
    ControlMethod,
    ControlPoint,
    EquipmentActivityPlan as Plan,
    ShelfObjectCalibrate,
    ShelfObjectEquipmentCharacteristics as Characteristics,
    ShelfObjectFailure,
    ShelfObjectLog,
    ShelfObjectObservation,
    ShelfObjectVerification,
)
from laboratory.tests.test_equipment_control import ControlBase
from laboratory.tests.test_cov_api_equipment_records import RegistrosEquipoBase
from presentation.models import AlertEvent, AlertRule

FUERA = ["5.05", "5.06", "5.05", "5.05", "5.06"]


class ReglaPorDefectoTest(RegistrosEquipoBase):

    def test_el_primer_programa_crea_la_regla(self):
        self.assertFalse(AlertRule.objects.filter(process=alerts.PROCESS).exists())
        Plan.objects.create(shelfobject=self.equipo, activity_kind=Plan.CALIBRATION, interval_value=12,
                            start_date=datetime.date(2026, 1, 1), organization=self.org, created_by=self.user)
        regla = AlertRule.objects.get(process=alerts.PROCESS)
        self.assertEqual(regla.organization, self.lab.organization)
        self.assertEqual(regla.created_by, self.user)
        self.assertEqual(regla.threshold["days_before"], 30)
        self.assertTrue(regla.notify_responsible and regla.create_task)
        # El segundo programa no la duplica.
        Plan.objects.create(shelfobject=self.equipo, activity_kind=Plan.CLEANING, interval_value=1,
                            start_date=datetime.date(2026, 1, 1), organization=self.org)
        self.assertEqual(AlertRule.objects.filter(process=alerts.PROCESS).count(), 1)

    def test_una_regla_desactivada_no_se_recrea(self):
        AlertRule.objects.create(organization=self.lab.organization, name="Apagada", process=alerts.PROCESS,
                                 trigger="due", threshold={"days_before": 5}, is_active=False)
        Plan.objects.create(shelfobject=self.equipo, activity_kind=Plan.CALIBRATION, interval_value=12,
                            organization=self.org)
        self.assertEqual(AlertRule.objects.filter(process=alerts.PROCESS).count(), 1)

    def test_el_primer_punto_de_control_crea_su_regla(self):
        metodo = ControlMethod.objects.create(name="X-R", organization=self.org)
        ControlPoint.objects.create(shelfobject=self.equipo, method=metodo, name="P1", organization=self.org,
                                    created_by=self.user)
        regla = AlertRule.objects.get(process=control.PROCESS)
        self.assertEqual(regla.trigger, control.TRIGGER_OUT_OF_CONTROL)

    def test_programas_anteriores_sin_regla(self):
        Plan.objects.create(shelfobject=self.equipo, activity_kind=Plan.CALIBRATION, interval_value=12,
                            organization=self.org, created_by=self.user)
        AlertRule.objects.all().delete()
        creadas = alerts.ensure_rules_for_existing_plans()
        self.assertEqual(len(creadas), 1)
        self.assertEqual(alerts.ensure_rules_for_existing_plans(), [])

    def test_la_regla_por_defecto_dispara(self):
        Plan.objects.create(shelfobject=self.equipo, activity_kind=Plan.CALIBRATION, interval_value=12,
                            start_date=datetime.date(2026, 1, 1), organization=self.org, created_by=self.user,
                            responsible=self.profile)
        regla = AlertRule.objects.get(process=alerts.PROCESS)
        eventos = alerts.evaluate_rule(regla, today=datetime.date(2026, 2, 1))
        self.assertEqual(len(eventos), 1)


class CorreccionPorRegistroTest(ControlBase):

    def test_cambiar_el_certificado_no_reescribe_los_registros(self):
        viejo = self.registrar(["5", "5", "5", "5", "5"], datetime.date(2026, 1, 1))
        self.assertEqual(viejo.correction, D("0.0032"))
        self.punto.correction = D("0")  # certificado nuevo de las pesas
        self.punto.save()
        nuevo = self.registrar(["5", "5", "5", "5", "5"], datetime.date(2026, 6, 1))
        self.assertEqual(nuevo.corrected_mean, D("5"))
        # Editar el registro viejo o recalcular límites conserva su corrección.
        viejo = ControlMeasurement.objects.get(pk=viejo.pk)
        viejo.observation = "revisado"
        control.save_measurement(viejo, self.user)
        control.recalculate_limits(self.punto, datetime.date(2026, 1, 1), datetime.date(2026, 12, 31), self.user)
        viejo.refresh_from_db()
        self.assertEqual(viejo.correction, D("0.0032"))
        self.assertEqual(viejo.corrected_mean, D("4.9968"))


class AlertasDeControlSinColgarTest(ControlBase):

    def setUp(self):
        super().setUp()
        AlertRule.objects.filter(process=control.PROCESS).delete()
        self.regla = AlertRule.objects.create(
            organization=self.org, name="Cartas", process=control.PROCESS, trigger=control.TRIGGER_OUT_OF_CONTROL,
            threshold={}, created_by=self.user, create_task=True,
        )

    def abiertas(self):
        return AlertEvent.objects.filter(rule=self.regla, resolved_at__isnull=True)

    def test_recalcular_no_avisa_por_registros_historicos(self):
        self.punto.tolerance = None  # sin límites ni tolerancia nada queda fuera todavía
        self.punto.save()
        for dia, valores in enumerate([["5", "5", "5", "5", "5"], ["5", "4.99", "5", "5", "5"], FUERA], start=1):
            self.registrar(valores, datetime.date(2026, 1, dia))
        self.assertEqual(self.abiertas().count(), 0)
        control.recalculate_limits(self.punto, datetime.date(2026, 1, 1), datetime.date(2026, 1, 2), self.user)
        historico = ControlMeasurement.objects.get(point=self.punto, measured_on=datetime.date(2026, 1, 3))
        # Queda marcado en la carta, pero nadie recibe un aviso por un registro viejo.
        self.assertTrue(historico.out_of_control)
        self.assertEqual(self.abiertas().count(), 0)

    def test_recalcular_resuelve_los_que_quedaron_dentro(self):
        self.punto.tolerance = None
        self.punto.save()
        self.referencia()
        fuera = self.registrar(["5.02", "5.02", "5.02", "5.02", "5.02"], datetime.date(2026, 2, 2))
        self.assertTrue(fuera.out_of_control)
        self.assertEqual(self.abiertas().count(), 1)
        # Límites fijos más anchos: el registro queda dentro y su alerta se cierra.
        control.set_fixed_limits(
            self.punto, {"lcl": "4.9", "center": "5", "ucl": "5.1", "range_lcl": "0", "range_center": "0.01",
                         "range_ucl": "0.05"}, apply_from=datetime.date(2026, 1, 1), user=self.user,
        )
        fuera.refresh_from_db()
        self.assertFalse(fuera.out_of_control)
        self.assertEqual(self.abiertas().count(), 0)

    def test_corregir_la_lectura_resuelve_la_alerta(self):
        self.referencia()
        fuera = self.registrar(FUERA, datetime.date(2026, 2, 2))
        self.assertEqual(self.abiertas().count(), 1)
        fuera.values = ["5", "5", "5", "5", "5"]
        control.save_measurement(fuera, self.user)
        self.assertEqual(self.abiertas().count(), 0)

    def test_borrar_el_registro_cierra_su_alerta(self):
        self.referencia()
        fuera = self.registrar(FUERA, datetime.date(2026, 2, 2))
        url = reverse("laboratory:api-equipment-control-measurement-detail",
                      kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "shelfobject": self.equipo.pk,
                              "point": self.punto.pk, "pk": fuera.pk})
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertFalse(ControlMeasurement.objects.filter(pk=fuera.pk).exists())
        self.assertEqual(self.abiertas().count(), 0)


class RangoMovilTest(ControlBase):

    def setUp(self):
        super().setUp()
        imr = ControlMethod.objects.create(name="pHmetro", organization=self.org, chart_type=ControlMethod.I_MR)
        self.ph = ControlPoint.objects.create(shelfobject=self.equipo, method=imr, name="pH 7", organization=self.org)
        self.a = self.registrar(["7.00"], datetime.date(2026, 1, 1), punto=self.ph)
        self.b = self.registrar(["7.05"], datetime.date(2026, 1, 2), punto=self.ph)
        self.c = self.registrar(["7.01"], datetime.date(2026, 1, 3), punto=self.ph)

    def rango(self, registro):
        return ControlMeasurement.objects.get(pk=registro.pk).range

    def test_serie_inicial(self):
        self.assertIsNone(self.rango(self.a))
        self.assertEqual(self.rango(self.b), D("0.05"))
        self.assertEqual(self.rango(self.c), D("0.04"))

    def test_mover_un_registro_recalcula_los_dos_vecinos(self):
        self.b.measured_on = datetime.date(2026, 1, 5)
        control.save_measurement(self.b, self.user)
        self.assertEqual(self.rango(self.c), D("0.01"))  # ahora sigue a «a»
        self.assertEqual(self.rango(self.b), D("0.04"))  # y «b» sigue a «c»

    def test_borrar_recalcula_el_siguiente(self):
        control.delete_measurement(self.b, self.user)
        self.assertEqual(self.rango(self.c), D("0.01"))
        control.delete_measurement(self.a, self.user)
        self.assertIsNone(self.rango(self.c))

    def test_mismo_dia_no_se_toma_a_si_mismo_como_vecino(self):
        otro = self.registrar(["7.02"], datetime.date(2026, 1, 3), punto=self.ph)
        self.assertEqual(self.rango(otro), D("0.01"))
        self.assertEqual(self.rango(self.c), D("0.04"))


class LimitesFijosTest(ControlBase):

    def url(self):
        return reverse("laboratory:api-equipment-control-point-set-limits",
                       kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "shelfobject": self.equipo.pk,
                               "pk": self.punto.pk})

    def datos(self, **extra):
        return {"lcl": "4.98", "center": "5", "ucl": "5.02", "range_lcl": "0", "range_center": "0.01",
                "range_ucl": "0.03", "apply_from": "01/01/2026", "notes": "Según PT-05", **extra}

    def test_fija_los_limites_y_reevalua(self):
        viejo = self.registrar(["5", "5", "5", "5", "5"], datetime.date(2025, 12, 1))
        dentro = self.registrar(["5", "5", "5", "5", "5"], datetime.date(2026, 1, 5))
        response = self.post(self.url(), self.datos())
        self.assertEqual(response.status_code, 200, response.content)
        limites = self.punto.current_limits()
        self.assertTrue(limites.manual)
        self.assertIsNone(limites.baseline_from)
        self.assertEqual(limites.ucl, D("5.02"))
        self.assertEqual(limites.notes, "Según PT-05")
        dentro.refresh_from_db()
        viejo.refresh_from_db()
        self.assertEqual(dentro.limits, limites)
        self.assertIsNone(viejo.limits)  # anterior a «aplicar desde»
        fuera = self.registrar(FUERA, datetime.date(2026, 1, 6))
        self.assertTrue(fuera.out_of_control)

    def test_reemplazan_a_los_calculados_y_queda_el_historial(self):
        calculados = self.referencia()
        self.post(self.url(), self.datos())
        calculados.refresh_from_db()
        self.assertFalse(calculados.is_current)
        self.assertEqual(ControlLimits.objects.filter(point=self.punto, is_current=True).count(), 1)

    def test_limites_incoherentes(self):
        response = self.post(self.url(), self.datos(lcl="5.5"))
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(self.punto.current_limits())

    def test_la_carta_muestra_limites_fijos(self):
        self.post(self.url(), self.datos())
        carta = reverse("laboratory:equipment_control_point",
                        kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": self.equipo.pk,
                                "point": self.punto.pk})
        response = self.client.get(carta)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "fixed_limits_submit")


class MetodoProtegidoTest(ControlBase):

    def url(self, metodo):
        return reverse("laboratory:api-equipment-control-method-detail",
                       kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": metodo.pk})

    def datos(self, **extra):
        return {"name": "Balanzas", "chart_type": "xbar_r", "subgroup_size": 5, "decimal_places": 4, **extra}

    def test_con_registros_no_cambia_n_ni_el_tipo(self):
        self.registrar(["5", "5", "5", "5", "5"], datetime.date(2026, 1, 1))
        self.assertEqual(self.put(self.url(self.metodo), self.datos(subgroup_size=3)).status_code, 400)
        self.assertEqual(self.put(self.url(self.metodo), self.datos(chart_type="i_mr", subgroup_size=1)).status_code, 400)
        # Las constantes y el nombre sí se pueden corregir.
        response = self.put(self.url(self.metodo), self.datos(d4="2.225"))
        self.assertEqual(response.status_code, 200, response.content)
        self.metodo.refresh_from_db()
        self.assertEqual(self.metodo.d4, D("2.225"))

    def test_sin_registros_se_puede_cambiar(self):
        response = self.put(self.url(self.metodo), self.datos(subgroup_size=3))
        self.assertEqual(response.status_code, 200, response.content)

    def test_metodo_de_una_organizacion_ancestra_no_se_edita(self):
        from laboratory.models import OrganizationStructure

        padre = OrganizationStructure.objects.create(name="Institución")
        OrganizationStructure.objects.filter(pk=self.org.pk).update(parent=padre)
        heredado = ControlMethod.objects.create(name="Heredado", organization=padre)
        self.assertEqual(self.put(self.url(heredado), self.datos(name="Cambiado")).status_code, 400)


class VentanaDeLaCartaTest(ControlBase):

    def cargar(self, cantidad):
        inicio = datetime.date(2024, 1, 1)
        ControlMeasurement.objects.bulk_create([
            ControlMeasurement(
                point=self.punto, organization=self.org, measured_on=inicio + datetime.timedelta(days=dia),
                values=["5"] * 5, mean=D("5"), range=D("0"), corrected_mean=D("4.9968"), correction=D("0.0032"),
            ) for dia in range(cantidad)
        ])

    def grafico(self, **params):
        url = reverse("equipmentcontrolmeanschart-detail", kwargs={"pk": self.punto.pk})
        return self.client.get(url, {"organization": self.org.pk, "laboratory": self.lab.pk, **params})

    def test_sin_rango_trae_los_ultimos(self):
        self.cargar(1000)
        etiquetas = self.grafico().json()["data"]["labels"]
        self.assertEqual(len(etiquetas), DEFAULT_WINDOW)
        self.assertEqual(etiquetas[-1], (datetime.date(2024, 1, 1) + datetime.timedelta(days=999)).strftime("%d/%m/%Y"))
        self.assertLess(etiquetas[0][-4:] + etiquetas[0][3:5], etiquetas[-1][-4:] + etiquetas[-1][3:5] + "z")

    def test_con_rango(self):
        self.cargar(400)
        etiquetas = self.grafico(**{"from": "2024-02-01", "to": "2024-02-29"}).json()["data"]["labels"]
        self.assertEqual(len(etiquetas), 29)
        self.assertEqual(etiquetas[0], "01/02/2024")

    def test_las_consultas_no_crecen_con_los_registros(self):
        self.cargar(50)
        with self.assertNumQueries(FuzzyInt(1, 30)) as pocos:
            self.grafico()
        self.cargar(950)
        with self.assertNumQueries(len(pocos.captured_queries)):
            self.grafico()

    def test_fecha_invalida(self):
        self.assertEqual(self.grafico(**{"from": "ayer"}).status_code, 404)


class FuzzyInt(int):
    """Entero que se compara igual a cualquier valor de un rango (para medir consultas)."""

    def __new__(cls, lowest, highest):
        obj = super().__new__(cls, highest)
        obj.lowest, obj.highest = lowest, highest
        return obj

    def __eq__(self, other):
        return self.lowest <= other <= self.highest

    __hash__ = int.__hash__


class ProgramaSinFechaTest(RegistrosEquipoBase):
    basename = "api-equipment-plan"

    def datos(self, **extra):
        return self.base_data(activity_kind=Plan.CALIBRATION, interval_value=12, interval_unit="months",
                              reminder_days_before=30, is_active=True, **extra)

    def test_sin_registros_exige_la_fecha_de_inicio(self):
        response = self.post(self.ruta(self.basename), self.datos())
        self.assertEqual(response.status_code, 400)
        self.assertIn("start_date", response.json())
        response = self.post(self.ruta(self.basename), self.datos(start_date="01/03/2026"))
        self.assertEqual(response.status_code, 201, response.content)

    def test_con_registros_la_fecha_es_opcional(self):
        ShelfObjectCalibrate.objects.create(shelfobject=self.equipo, calibration_date=datetime.date(2026, 1, 10),
                                            organization=self.org, calibrate_name="LACOMET")
        response = self.post(self.ruta(self.basename), self.datos())
        self.assertEqual(response.status_code, 201, response.content)

    def test_estado_sin_fecha(self):
        plan = Plan.objects.create(shelfobject=self.equipo, activity_kind=Plan.CLEANING, interval_value=1,
                                   organization=self.org)
        self.assertEqual(plan.due_status(), Plan.UNSCHEDULED)
        fila = self.client.get(self.ruta(self.basename)).json()["data"][0]
        self.assertEqual(fila["due_status"]["code"], "unscheduled")


class EstadoDelEquipoTest(RegistrosEquipoBase):

    def setUp(self):
        super().setUp()
        self.ficha, _created = Characteristics.objects.get_or_create(
            shelfobject=self.equipo, defaults={"organization": self.org}
        )

    def test_calibracion_no_conforme_no_es_vigente(self):
        Plan.objects.create(shelfobject=self.equipo, activity_kind=Plan.CALIBRATION, interval_value=12,
                            organization=self.org)
        hoy = datetime.date.today()
        calibracion = ShelfObjectCalibrate.objects.create(
            shelfobject=self.equipo, calibration_date=hoy, organization=self.org, calibrate_name="LACOMET",
            conformity=ShelfObjectCalibrate.CONFORMING,
        )
        self.assertEqual(self.ficha.calibration_status()[0], "valid")
        calibracion.conformity = ShelfObjectCalibrate.NON_CONFORMING
        calibracion.save()
        self.assertEqual(self.ficha.calibration_status()[0], "non_conforming")

    def test_el_cambio_de_estado_queda_en_la_linea_de_tiempo(self):
        self.ficha.equipment_status = Characteristics.IN_CALIBRATION
        self.ficha.save()
        observacion = ShelfObjectObservation.objects.filter(shelf_object=self.equipo).order_by("-pk").first()
        self.assertIn("→", observacion.description)
        cantidad = ShelfObjectObservation.objects.filter(shelf_object=self.equipo).count()
        self.ficha.notes = "sin cambio de estado"
        self.ficha.save()
        self.assertEqual(ShelfObjectObservation.objects.filter(shelf_object=self.equipo).count(), cantidad)

    def test_la_baja_marca_la_unidad_y_pone_la_fecha(self):
        self.ficha.equipment_status = Characteristics.DECOMMISSIONED
        self.ficha.save()
        self.ficha.refresh_from_db()
        self.equipo.refresh_from_db()
        self.assertEqual(self.ficha.decommission_date, datetime.date.today())
        self.assertTrue(self.equipo.marked_as_discard)

    def test_la_falla_bloquea_y_borrarla_devuelve_el_equipo(self):
        falla = ShelfObjectFailure.objects.create(
            shelfobject=self.equipo, failure_date=datetime.date(2026, 3, 1), description="No enciende",
            organization=self.org,
        )
        self.ficha.refresh_from_db()
        self.assertEqual(self.ficha.equipment_status, Characteristics.OUT_OF_SERVICE)
        self.assertTrue(ShelfObjectObservation.objects.filter(shelf_object=self.equipo, description__contains="→").exists())
        falla.delete()
        self.ficha.refresh_from_db()
        self.assertEqual(self.ficha.equipment_status, Characteristics.IN_SERVICE)

    def test_borrar_una_falla_con_otra_abierta_no_libera_el_equipo(self):
        datos = {"shelfobject": self.equipo, "failure_date": datetime.date(2026, 3, 1), "organization": self.org}
        primera = ShelfObjectFailure.objects.create(description="No enciende", **datos)
        ShelfObjectFailure.objects.create(description="Plato suelto", **datos)
        primera.delete()
        self.ficha.refresh_from_db()
        self.assertEqual(self.ficha.equipment_status, Characteristics.OUT_OF_SERVICE)

    def test_no_se_registra_uso_de_un_equipo_fuera_de_servicio(self):
        url = self.ruta("api-shelfobject-log")
        self.ficha.equipment_status = Characteristics.OUT_OF_SERVICE
        self.ficha.save()
        response = self.post(url, self.base_data(description="Pesada de rutina"))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(ShelfObjectLog.objects.filter(description="Pesada de rutina").exists())
        self.ficha.equipment_status = Characteristics.IN_SERVICE
        self.ficha.save()
        response = self.post(url, self.base_data(description="Pesada de rutina"))
        self.assertEqual(response.status_code, 201, response.content)


class TextosDeLaLineaDeTiempoTest(RegistrosEquipoBase):

    def test_los_registros_se_describen(self):
        verificacion = ShelfObjectVerification(verification_type="Pesa de 100 g", verification_date=datetime.date(2026, 5, 4))
        self.assertEqual(str(verificacion), "Pesa de 100 g 04/05/2026")
        falla = ShelfObjectFailure(failure_date=datetime.date(2026, 5, 4), description="No enciende")
        self.assertEqual(str(falla), "04/05/2026: No enciende")
        calibracion = ShelfObjectCalibrate(calibration_date=datetime.date(2026, 5, 4))
        self.assertIn("04/05/2026", str(calibracion))

    def test_la_verificacion_deja_su_descripcion_en_la_linea_de_tiempo(self):
        response = self.post(self.ruta("api-equipment-verification"), self.base_data(
            verification_date="04/05/2026", verification_type="Pesa de 100 g", result="100.01 g",
        ))
        self.assertEqual(response.status_code, 201, response.content)
        observacion = ShelfObjectObservation.objects.filter(shelf_object=self.equipo).order_by("-pk").first()
        self.assertEqual(observacion.description, "Pesa de 100 g 04/05/2026")


class ListadoDeEquiposTest(RegistrosEquipoBase):

    def setUp(self):
        super().setUp()
        self.ficha, _created = Characteristics.objects.get_or_create(
            shelfobject=self.equipo, defaults={"organization": self.org}
        )
        self.ficha.internal_code = "LB-127"
        self.ficha.serial_number = "S-2025"
        self.ficha.physical_location = "Mesa de balanzas"
        self.ficha.save()
        self.url = reverse("laboratory:api-equipment-unit-list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})

    def filas(self, **params):
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()["data"]

    def test_busca_por_codigo_interno_y_serie(self):
        self.assertEqual([fila["internal_code"] for fila in self.filas(search="lb-127")], ["LB-127"])
        self.assertEqual([fila["id"] for fila in self.filas(search="S-2025")], [self.equipo.pk])
        self.assertEqual(self.filas(search="no-existe"), [])

    def test_estado_calibracion_y_proxima_actividad(self):
        Plan.objects.create(shelfobject=self.equipo, activity_kind=Plan.CALIBRATION, interval_value=12,
                            start_date=datetime.date(2020, 1, 1), organization=self.org)
        fila = self.filas(search="LB-127")[0]
        self.assertEqual(fila["equipment_status"]["code"], "in_service")
        self.assertEqual(fila["calibration"], {"code": "expired", "text": fila["calibration"]["text"], "date": "01/01/2020"})
        self.assertEqual(fila["next_activity"]["code"], "expired")
        self.assertIn("/edit/", fila["url"])

    def test_filtro_por_estado(self):
        self.assertEqual(self.filas(equipment_status="out_of_service"), [])
        self.ficha.equipment_status = Characteristics.OUT_OF_SERVICE
        self.ficha.save()
        self.assertEqual([fila["id"] for fila in self.filas(equipment_status="out_of_service")], [self.equipo.pk])

    def test_solo_equipos_del_laboratorio(self):
        from laboratory.models import Object, ShelfObject

        esperados = ShelfObject.objects.filter(in_where_laboratory=self.lab, object__type=Object.EQUIPMENT).count()
        response = self.client.get(self.url, {"length": 100}).json()
        self.assertEqual(response["recordsTotal"], esperados)

    def test_es_de_solo_lectura(self):
        self.assertIn(self.post(self.url, {}).status_code, (403, 405))

    def test_pagina(self):
        pagina = reverse("laboratory:equipment_units", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(pagina)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.url)


class ControlDelDiaTest(ControlBase):

    def setUp(self):
        super().setUp()
        self.p2 = ControlPoint.objects.create(shelfobject=self.equipo, method=self.metodo, name="P2 (25 g)",
                                              nominal_value=D("25"), organization=self.org)
        self.inactivo = ControlPoint.objects.create(shelfobject=self.equipo, method=self.metodo, name="P9",
                                                    organization=self.org, is_active=False)
        self.url = reverse("laboratory:api-equipment-control-point-register-day",
                           kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "shelfobject": self.equipo.pk})

    def datos(self, lecturas, **extra):
        return {"measured_on": "05/03/2026", "responsible": self.profile.pk, "observation": "Rutina",
                "readings": lecturas, **extra}

    def test_registra_todos_los_puntos_con_lecturas(self):
        response = self.post(self.url, self.datos({
            str(self.punto.pk): "5; 5; 4,99; 5; 5", str(self.p2.pk): "25 25.1 25 25 24.9", str(self.inactivo.pk): "",
        }))
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["created"], 2)
        registro = ControlMeasurement.objects.get(point=self.p2)
        self.assertEqual(registro.measured_on, datetime.date(2026, 3, 5))
        self.assertEqual(registro.responsible, self.profile)
        self.assertEqual(registro.range, D("0.2"))
        self.assertTrue(ShelfObjectObservation.objects.filter(shelf_object=self.equipo, description__contains="P2 (25 g)").exists())

    def test_un_punto_sin_lecturas_se_omite(self):
        response = self.post(self.url, self.datos({str(self.punto.pk): "5 5 5 5 5", str(self.p2.pk): " "}))
        self.assertEqual(response.status_code, 201, response.content)
        self.assertFalse(ControlMeasurement.objects.filter(point=self.p2).exists())

    def test_un_error_no_guarda_ninguno(self):
        response = self.post(self.url, self.datos({str(self.punto.pk): "5 5 5 5 5", str(self.p2.pk): "25 25"}))
        self.assertEqual(response.status_code, 400)
        self.assertIn(str(self.p2.pk), response.json()["readings"])
        self.assertFalse(ControlMeasurement.objects.exists())

    def test_sin_lecturas_o_con_un_punto_ajeno(self):
        self.assertEqual(self.post(self.url, self.datos({})).status_code, 400)
        self.assertEqual(self.post(self.url, self.datos({"999999": "5 5 5 5 5"})).status_code, 400)
        self.assertEqual(self.post(self.url, self.datos({str(self.inactivo.pk): "5 5 5 5 5"})).status_code, 400)

    def test_avisa_los_que_quedaron_fuera(self):
        self.referencia()
        response = self.post(self.url, self.datos({str(self.punto.pk): "5.05 5.06 5.05 5.05 5.06"}))
        self.assertEqual(response.json()["out"], ["P1 (5 g)"])

    def test_la_ficha_muestra_el_formulario(self):
        ficha = reverse("laboratory:equipment_shelfobject_detail",
                        kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": self.equipo.pk})
        response = self.client.get(ficha)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-point="%s"' % self.punto.pk)
        self.assertNotContains(response, 'data-point="%s"' % self.inactivo.pk)
        self.assertContains(response, self.url)


class ImportadorSujetoAConfirmacionTest(RegistrosEquipoBase):

    def test_no_es_no_conforme(self):
        from laboratory.equipment import importer
        from laboratory.tests.test_equipment_importer_parser import as_file, program_workbook

        libro = program_workbook()
        hoja = libro.active
        fila, columnas, _bloques = importer.find_program_header(hoja)
        hoja.cell(fila, columnas["calibration_result"]).value = "Sujeto a confirmación"
        _titulo, filas = importer.read_workbook(as_file(libro), importer.PROGRAM)
        self.assertEqual(filas[0]["calibration_conformity"], "")
        self.assertEqual(filas[0]["calibration_result"], "Sujeto a confirmación")


class ListadoConRolCanonicoTest(RegistrosEquipoBase):

    def test_el_tecnico_ve_el_listado_y_su_api(self):
        from auth_and_perms.management.commands.update_roles import sync_roles
        from auth_and_perms.roles import ROLES
        from presentation.tests.test_platform_parameters import make_role_user

        sync_roles(["tecnico_laboratorio"])
        tecnico = make_role_user("tecnico_listado", self.org, ROLES["tecnico_laboratorio"])
        self.client.force_login(tecnico)
        kwargs = {"org_pk": self.org.pk, "lab_pk": self.lab.pk}
        self.assertEqual(self.client.get(reverse("laboratory:equipment_units", kwargs=kwargs)).status_code, 200)
        response = self.client.get(reverse("laboratory:api-equipment-unit-list", kwargs=kwargs))
        self.assertEqual(response.status_code, 200, response.content)
