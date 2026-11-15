"""
Programa de actividades del equipo, estado por fallas e historial de ubicación
(ISO/IEC 17025 §6.4, ``plans/EQUIPOS_ISO17025_PLAN.md``).
"""
import datetime

from django.test import TestCase

from laboratory.models import (
    EquipmentActivityPlan as Plan,
    Shelf,
    ShelfObject,
    ShelfObjectCalibrate,
    ShelfObjectEquipmentCharacteristics as Characteristics,
    ShelfObjectFailure,
    ShelfObjectMaintenance,
    ShelfObjectObservation,
    ShelfObjectVerification,
)

HOY = datetime.date(2026, 11, 15)


class EquipoBase(TestCase):
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        self.equipo = ShelfObject.objects.get(pk=15)  # equipo con características, laboratorio 1
        self.ficha = self.equipo.shelfobjectequipmentcharacteristics

    def plan(self, kind=Plan.CALIBRATION, **extra):
        extra.setdefault("interval_value", 12)
        return Plan.objects.create(shelfobject=self.equipo, activity_kind=kind, **extra)

    def calibrar(self, fecha, **extra):
        return ShelfObjectCalibrate.objects.create(
            shelfobject=self.equipo, calibration_date=fecha, calibrate_name="Metrología", **extra
        )

    def mantener(self, fecha, tipo=ShelfObjectMaintenance.PREVENTIVE, **extra):
        return ShelfObjectMaintenance.objects.create(
            shelfobject=self.equipo, maintenance_date=fecha, maintenance_type=tipo, **extra
        )


class ProximaFechaTest(EquipoBase):

    def test_sin_registros_usa_la_fecha_de_inicio(self):
        plan = self.plan(start_date=datetime.date(2027, 1, 10))
        self.assertIsNone(plan.last_done())
        self.assertEqual(plan.next_due(), datetime.date(2027, 1, 10))

    def test_sin_registros_ni_inicio_no_vence(self):
        plan = self.plan()
        self.assertIsNone(plan.next_due())
        self.assertEqual(plan.due_status(HOY), Plan.UNSCHEDULED)

    def test_calibracion_suma_el_intervalo_en_meses(self):
        plan = self.plan()
        self.calibrar(datetime.date(2025, 4, 10))
        self.calibrar(datetime.date(2026, 4, 10))
        self.assertEqual(plan.last_done(), datetime.date(2026, 4, 10))
        self.assertEqual(plan.next_due(), datetime.date(2027, 4, 10))

    def test_la_proxima_del_certificado_manda(self):
        plan = self.plan()
        self.calibrar(datetime.date(2026, 4, 10), next_calibration_date=datetime.date(2026, 12, 1))
        self.assertEqual(plan.next_due(), datetime.date(2026, 12, 1))

    def test_intervalo_en_dias(self):
        plan = self.plan(kind=Plan.CLEANING, interval_value=15, interval_unit=Plan.DAYS)
        self.mantener(datetime.date(2026, 11, 1), tipo=ShelfObjectMaintenance.CLEANING)
        self.mantener(datetime.date(2026, 11, 10))  # preventivo: no cuenta como limpieza
        self.assertEqual(plan.next_due(), datetime.date(2026, 11, 16))

    def test_mantenimiento_preventivo_ignora_correctivos(self):
        plan = self.plan(kind=Plan.PREVENTIVE_MAINTENANCE, interval_value=6)
        self.mantener(datetime.date(2026, 1, 5))
        self.mantener(datetime.date(2026, 3, 5), tipo=ShelfObjectMaintenance.CORRECTIVE)
        self.assertEqual(plan.next_due(), datetime.date(2026, 7, 5))

    def test_verificaciones_enlazadas_al_plan_mandan(self):
        balanza = self.plan(kind=Plan.VERIFICATION, interval_value=1, name="Pesas")
        ShelfObjectVerification.objects.create(
            shelfobject=self.equipo, verification_date=datetime.date(2026, 11, 1), plan=None
        )
        ShelfObjectVerification.objects.create(
            shelfobject=self.equipo, verification_date=datetime.date(2026, 10, 1), plan=balanza
        )
        self.assertEqual(balanza.next_due(), datetime.date(2026, 11, 1))

    def test_otra_actividad_solo_cuenta_lo_enlazado(self):
        plan = self.plan(kind=Plan.OTHER, interval_value=3, start_date=datetime.date(2026, 12, 1))
        self.mantener(datetime.date(2026, 10, 1))
        self.assertEqual(plan.next_due(), datetime.date(2026, 12, 1))
        self.mantener(datetime.date(2026, 10, 20), plan=plan)
        self.assertEqual(plan.next_due(), datetime.date(2027, 1, 20))

    def test_estados(self):
        plan = self.plan(reminder_days_before=30)
        self.calibrar(datetime.date(2025, 12, 10))  # vence 2026-12-10: 25 días después de HOY
        self.assertEqual(plan.due_status(HOY), Plan.DUE_SOON)
        self.assertEqual(plan.due_status(datetime.date(2026, 11, 1)), Plan.VALID)
        self.assertEqual(plan.due_status(datetime.date(2027, 1, 1)), Plan.EXPIRED)

    def test_estado_de_calibracion_de_la_ficha(self):
        self.assertEqual(self.ficha.calibration_status(HOY), ("not_required", None))
        self.plan()
        self.calibrar(datetime.date(2026, 4, 10))
        self.assertEqual(self.ficha.calibration_status(HOY), (Plan.VALID, datetime.date(2027, 4, 10)))


class FallaYEstadoTest(EquipoBase):

    def fallar(self, **extra):
        return ShelfObjectFailure.objects.create(
            shelfobject=self.equipo, failure_date=HOY, description="No enciende", **extra
        )

    def estado(self):
        return Characteristics.objects.get(pk=self.ficha.pk).equipment_status

    def test_falla_bloqueante_saca_de_servicio_y_retorno_lo_devuelve(self):
        falla = self.fallar()
        self.assertEqual(self.estado(), Characteristics.OUT_OF_SERVICE)
        falla.return_to_service_date = HOY
        falla.save()
        self.assertEqual(self.estado(), Characteristics.IN_SERVICE)

    def test_sigue_fuera_si_queda_otra_falla_abierta(self):
        primera = self.fallar()
        self.fallar()
        primera.return_to_service_date = HOY
        primera.save()
        self.assertEqual(self.estado(), Characteristics.OUT_OF_SERVICE)

    def test_falla_no_bloqueante_no_cambia_el_estado(self):
        self.fallar(blocked=False)
        self.assertEqual(self.estado(), Characteristics.IN_SERVICE)

    def test_retorno_no_reactiva_un_equipo_dado_de_baja(self):
        falla = self.fallar()
        Characteristics.objects.filter(pk=self.ficha.pk).update(
            equipment_status=Characteristics.DECOMMISSIONED
        )
        falla.return_to_service_date = HOY
        falla.save()
        self.assertEqual(self.estado(), Characteristics.DECOMMISSIONED)


class HistorialDeUbicacionTest(EquipoBase):

    def test_cambio_de_estante_queda_en_la_linea_de_tiempo(self):
        otro = Shelf.objects.filter(furniture__labroom__laboratory_id=1).exclude(pk=self.equipo.shelf_id).first()
        self.equipo.shelf = otro
        self.equipo.save()
        self.assertTrue(
            ShelfObjectObservation.objects.filter(
                shelf_object=self.equipo, description__contains=str(otro)
            ).exists()
        )

    def test_cambio_de_ubicacion_fisica(self):
        self.ficha.physical_location = "Mesa de balanzas"
        self.ficha.save()
        self.assertTrue(
            ShelfObjectObservation.objects.filter(
                shelf_object=self.equipo, description__endswith="Mesa de balanzas"
            ).exists()
        )

    def test_guardar_sin_cambios_no_deja_rastro(self):
        antes = ShelfObjectObservation.objects.count()
        self.equipo.save()
        self.ficha.save()
        self.assertEqual(ShelfObjectObservation.objects.count(), antes)
