import datetime
import os
import tempfile
from unittest import mock

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from laboratory import tasks
from laboratory.models import (
    BaseUnitValues,
    Catalog,
    Furniture,
    Inform,
    InformScheduler,
    Laboratory,
    ObjectLogChange,
    ObjectMaximumLimit,
    OrganizationStructure,
    OrganizationStructureRelations,
    PrecursorReport,
    PrecursorReportValues,
    Shelf,
    ShelfObject,
    ShelfObjectLimits,
)
from pending_tasks.models import PendingTask
from sga.models import SDSTraceability, SubstanceCharacteristics

MEDIA_TMP = tempfile.mkdtemp(prefix="organilab-cov-tasks-")


def asegurar_unidades_base():
    """Mililitros (63) y Litros (62) con su equivalencia, como en producción."""
    if not BaseUnitValues.objects.filter(measurement_unit_id=62).exists():
        BaseUnitValues.objects.create(measurement_unit_id=62, measurement_unit_base_id=62, si_value=1)
    if not BaseUnitValues.objects.filter(measurement_unit_id=63).exists():
        BaseUnitValues.objects.create(measurement_unit_id=63, measurement_unit_base_id=62, si_value=1000)


def fecha_fija(anio, mes, dia):
    class FechaFija(datetime.date):
        @classmethod
        def today(cls):
            return cls(anio, mes, dia)

    return FechaFija


class BaseTareasTest(TestCase):
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        asegurar_unidades_base()
        self.user = User.objects.get(username="admin")
        self.lab = Laboratory.objects.get(pk=1)
        self.lab.responsible = self.user
        self.lab.save()


class NotificacionLimitesTest(BaseTareasTest):

    def test_objetos_con_limite_y_aviso_al_responsable(self):
        bajo = ShelfObject.objects.get(pk=1)
        bajo.limits = ShelfObjectLimits.objects.create(minimum_limit=30, maximum_limit=100)
        bajo.save()
        holgado = ShelfObject.objects.get(pk=2)
        holgado.limits = ShelfObjectLimits.objects.create(minimum_limit=1, maximum_limit=100)
        holgado.save()

        self.assertEqual(set(tasks.get_limited_shelf_objects(self.lab)), {bajo, holgado})

        tasks.notify_about_product_limit_reach()

        tarea = PendingTask.objects.get(profile=self.user.profile)
        self.assertEqual(tarea.status, PendingTask.PENDING)
        self.assertIn(bajo.object.name, tarea.description)
        self.assertNotIn(holgado.object.code, tarea.description)

    def test_programa_la_tarea_periodica(self):
        sender = mock.MagicMock()
        tasks.setup_daily_tasks(sender)
        sender.add_periodic_task.assert_called_once()
        self.assertEqual(sender.add_periodic_task.call_args.kwargs["name"], "notify")


class ReportePrecursoresTest(BaseTareasTest):

    def setUp(self):
        super().setUp()
        # Un reporte anterior vacío: el primer saldo se toma como saldo previo.
        PrecursorReport.objects.create(month=12, year=2025, laboratory=self.lab, consecutive=1, month_belong=11)

    def test_reporte_de_enero_corresponde_a_diciembre_del_anio_anterior(self):
        log = ObjectLogChange.objects.create(
            object_id=1, laboratory=self.lab, user=self.user, diff_value=5, precursor=True,
            measurement_unit_id=62, subject="Compra", bill="F-1", type_action=0,
        )
        ObjectLogChange.objects.filter(pk=log.pk).update(update_time=datetime.datetime(2025, 12, 10, 12, tzinfo=datetime.timezone.utc))
        ObjectLogChange.objects.create(
            object_id=1, laboratory=self.lab, user=self.user, diff_value=-2, precursor=True,
            measurement_unit_id=62, type_action=3, subject=None,
        )
        ObjectLogChange.objects.filter(diff_value=-2).update(update_time=datetime.datetime(2025, 12, 11, 12, tzinfo=datetime.timezone.utc))

        with mock.patch.object(tasks, "date", fecha_fija(2026, 1, 15)):
            tasks.create_precursor_reports()

        reporte = PrecursorReport.objects.filter(laboratory=self.lab).last()
        self.assertEqual((reporte.month, reporte.month_belong, reporte.year), (1, 12, 2026))
        self.assertEqual(reporte.consecutive, 2)
        valores = PrecursorReportValues.objects.get(precursor_report=reporte, object_id=1)
        self.assertEqual(valores.new_income, 5)
        self.assertEqual(valores.month_expense, 2)
        self.assertEqual(valores.bills, "F-1")
        self.assertEqual(valores.reason_to_spend, "Compra")
        # Dos ShelfObject del mismo reactivo se acumulan en una sola fila.
        self.assertGreater(valores.quantity, 0)
        self.assertGreater(valores.previous_balance, 0)
        self.assertIn("2025", reporte.get_date_range())

    def test_segundo_reporte_arrastra_el_saldo_final(self):
        with mock.patch.object(tasks, "date", fecha_fija(2026, 3, 2)):
            tasks.create_precursor_reports()
        primero = PrecursorReport.objects.filter(laboratory=self.lab).last()
        PrecursorReportValues.objects.filter(precursor_report=primero).update(final_balance=7)

        with mock.patch.object(tasks, "date", fecha_fija(2026, 4, 2)):
            tasks.create_precursor_reports()

        segundo = PrecursorReport.objects.filter(laboratory=self.lab).last()
        self.assertEqual(segundo.consecutive, 3)
        self.assertEqual(segundo.month_belong, 3)
        valores = PrecursorReportValues.objects.get(precursor_report=segundo, object_id=1)
        self.assertEqual(valores.previous_balance, 7)
        self.assertEqual(valores.final_balance, valores.stock - valores.month_expense)

    def test_existencias_en_unidades_distintas_se_suman_en_la_unidad_base(self):
        existencias = ShelfObject.objects.filter(in_where_laboratory=self.lab, object_id=1)
        self.assertGreaterEqual(existencias.count(), 2)
        primera, segunda = existencias[:2]
        existencias.exclude(pk__in=[primera.pk, segunda.pk]).delete()
        # 500 mL y 1 L del mismo reactivo: la fila en Litros debe decir 1.5.
        primera.measurement_unit_id, primera.quantity = 63, 500
        primera.save()
        segunda.measurement_unit_id, segunda.quantity = 62, 1
        segunda.save()

        with mock.patch.object(tasks, "date", fecha_fija(2026, 3, 2)):
            tasks.create_precursor_reports()

        reporte = PrecursorReport.objects.filter(laboratory=self.lab).last()
        valores = PrecursorReportValues.objects.get(precursor_report=reporte, object_id=1)
        self.assertEqual(valores.measurement_unit_id, 62)
        self.assertAlmostEqual(valores.quantity, 1.5)

    def test_consecutivo_inicial_sin_reportes(self):
        PrecursorReport.objects.all().delete()
        self.assertEqual(tasks.add_consecutive(self.lab), 1)


class InformesPeriodicosTest(BaseTareasTest):

    def test_crea_periodo_e_informes_el_dia_de_inicio(self):
        hoy = datetime.datetime.today().date()
        programador = InformScheduler.objects.get(pk=1)
        programador.informsperiod_set.all().delete()
        programador.start_application_date = hoy
        programador.close_application_date = hoy
        programador.save()
        programador.laboratories.add(self.lab, Laboratory.objects.get(pk=2))
        InformScheduler.objects.exclude(pk=programador.pk).update(active=False)

        tasks.create_informs_based_on_period()

        periodo = programador.informsperiod_set.get()
        self.assertEqual(periodo.start_application_date, hoy)
        self.assertEqual(periodo.close_application_date, hoy + datetime.timedelta(days=programador.period_on_days))
        self.assertEqual(periodo.informs.count(), 2)
        self.assertTrue(Inform.objects.filter(name="%s -- %s" % (programador.name, self.lab.name)).exists())
        self.assertTrue(PendingTask.objects.filter(profile=self.user.profile).exists())

        # Con un periodo previo el siguiente se calcula desde él: hoy no toca.
        tasks.create_informs_based_on_period()
        self.assertEqual(programador.informsperiod_set.count(), 1)


class LimpiezaYExistenciasTest(BaseTareasTest):

    def test_mueble_sin_cuadricula_conserva_sus_estantes(self):
        mueble = Furniture.objects.get(pk=1)
        Furniture.objects.filter(pk=mueble.pk).update(dataconfig="")
        estantes = Shelf.objects.filter(furniture=mueble).count()
        tasks.remove_shelf_not_furniture()
        self.assertEqual(Shelf.objects.filter(furniture=mueble).count(), estantes)

    def test_registra_el_maximo_diario_por_reactivo(self):
        tasks.add_maximum_object_stock_per_day()
        maximos = ObjectMaximumLimit.objects.filter(laboratory=self.lab)
        self.assertEqual(set(maximos.values_list("object_id", flat=True)), {1, 2})
        tanque = maximos.get(object_id=1)
        self.assertEqual(tanque.measurement_unit_id, 63)
        # 2 ShelfObject de 23 mL en el laboratorio, expresados en litros.
        self.assertAlmostEqual(tanque.quantity, 0.046)

    def test_aviso_de_vencimiento_solo_a_laboratorios_con_responsable(self):
        manana = datetime.date.today() + datetime.timedelta(days=1)
        lab_sin_responsable = Laboratory.objects.get(pk=2)
        ShelfObject.objects.filter(pk__in=[1, 2, 4]).update(reactive_expiration_date=manana)
        ShelfObject.objects.filter(pk=2).update(in_where_laboratory=lab_sin_responsable)

        tasks.send_expiration_email()

        tareas = PendingTask.objects.filter(name="ShelfObject expiration")
        self.assertEqual(tareas.count(), 1)
        self.assertEqual(tareas.get().profile, self.user.profile)

    def test_borra_relaciones_a_laboratorios_y_organizaciones_inexistentes(self):
        org = OrganizationStructure.objects.get(pk=1)
        ct_lab = ContentType.objects.get_for_model(Laboratory)
        ct_org = ContentType.objects.get_for_model(OrganizationStructure)
        huerfana_lab = OrganizationStructureRelations.objects.create(organization=org, content_type=ct_lab, object_id=99999)
        huerfana_org = OrganizationStructureRelations.objects.create(organization=org, content_type=ct_org, object_id=99999)
        valida_org = OrganizationStructureRelations.objects.create(organization=org, content_type=ct_org, object_id=org.pk)

        tasks.remove_relation_organization_laboratory()

        restantes = OrganizationStructureRelations.objects.all()
        self.assertNotIn(huerfana_lab, restantes)
        self.assertNotIn(huerfana_org, restantes)
        self.assertIn(valida_org, restantes)
        self.assertTrue(restantes.filter(content_type=ct_lab, object_id=1).exists())


@override_settings(MEDIA_ROOT=MEDIA_TMP)
class ActualizacionFichasSDSTest(TestCase):
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        self.sc_con_pdf = SubstanceCharacteristics.objects.get(pk=1)
        self.sc_con_pdf.security_sheet.save("ficha_cov.pdf", ContentFile(b"%PDF-1.4 prueba"), save=True)
        self.sc_sin_pdf = SubstanceCharacteristics.objects.get(pk=2)
        self.sc_sin_pdf.security_sheet = None
        self.sc_sin_pdf.save()

    def test_fuentes_segun_trazabilidad_pubchem(self):
        fuentes, forzar = tasks._get_sources_for_substance(self.sc_con_pdf, True)
        self.assertFalse(forzar)
        self.assertTrue(fuentes)
        SDSTraceability.objects.create(sga_substance_characteristics=self.sc_con_pdf, source="pubchem")
        fuentes, forzar = tasks._get_sources_for_substance(self.sc_con_pdf, True)
        self.assertTrue(forzar)
        self.assertEqual([f.__class__.__name__ for f in fuentes], ["MerckSource"])

    def test_resolucion_de_la_ruta_del_pdf(self):
        self.assertIsNone(tasks._resolve_pdf_path(self.sc_sin_pdf))
        self.assertTrue(os.path.exists(tasks._resolve_pdf_path(self.sc_con_pdf)))
        self.sc_sin_pdf.security_sheet.name = "security_sheets/no_existe.pdf"
        self.assertIsNone(tasks._resolve_pdf_path(self.sc_sin_pdf))

    def test_densidad_vacia_es_cero(self):
        self.sc_con_pdf.density = 0
        self.assertTrue(tasks._is_empty(self.sc_con_pdf, "density"))
        self.sc_con_pdf.density = 1.2
        self.assertFalse(tasks._is_empty(self.sc_con_pdf, "density"))

    def test_sin_pdf_no_se_actualiza(self):
        self.assertEqual(tasks._update_substance_from_pdf(self.sc_sin_pdf), (False, "no PDF file", {}))

    def test_campos_de_catalogo_desde_el_texto(self):
        iarc = Catalog.objects.create(key="IARC", description="Grupo 1 cov")
        organo = Catalog.objects.create(key="white_organ", description="Pulmón cov")
        datos = {"_lang": "en", "_text": "IARC Group 1\nPulmón cov", "density": 1.5}
        with mock.patch("laboratory.utils_pdf.extract_msds_data", return_value=datos), \
                mock.patch("laboratory.utils_pdf.extract_catalog_fields",
                           return_value={"iarc": iarc.pk, "white_organ": [organo.pk]}) as extractor:
            ok, mensaje, _ = tasks._update_substance_from_pdf(self.sc_con_pdf)
        self.assertEqual((ok, mensaje), (True, "updated"))
        self.assertIn((iarc.pk, "Grupo 1 cov"), extractor.call_args.args[1]["IARC"])
        self.sc_con_pdf.refresh_from_db()
        self.assertEqual(self.sc_con_pdf.iarc_id, iarc.pk)
        self.assertEqual(list(self.sc_con_pdf.white_organ.values_list("pk", flat=True)), [organo.pk])
        self.assertEqual(self.sc_con_pdf.density, 1.5)

    def test_proceso_masivo_reporta_cada_resultado(self):
        traza_pubchem = SDSTraceability.objects.create(sga_substance_characteristics=self.sc_con_pdf, source="pubchem")
        resultados = [{"status": "updated", "source": "merck"}, {"status": "no_source"}]
        with mock.patch("laboratory.sds_sources.update_sds_for_substance", side_effect=resultados) as descarga, \
                mock.patch.object(tasks.time, "sleep") as dormir, \
                mock.patch("laboratory.utils_pdf.extract_msds_data", return_value=None):
            resumen = tasks.update_sds_and_extract_data(sc_ids=[self.sc_con_pdf.pk, self.sc_sin_pdf.pk], delay=1)
        self.assertEqual(descarga.call_count, 2)
        self.assertEqual(dormir.call_count, 2)
        self.assertEqual(resumen, {"total": 2, "updated": 0, "skipped": 2, "errors": 0})

        # Sin forzar: se consulta la vigencia del PDF que ya existe.
        traza_pubchem.delete()
        with mock.patch("laboratory.sds_sources.check_needs_update", return_value=(True, "")), \
                mock.patch("laboratory.sds_sources.update_sds_for_substance", return_value={"status": "error", "error": "x"}), \
                mock.patch("laboratory.utils_pdf.extract_msds_data", return_value={"_lang": "es", "_text": ""}):
            resumen = tasks.update_sds_and_extract_data(sc_ids=[self.sc_con_pdf.pk], delay=0)
        self.assertEqual(resumen["updated"], 1)

        with mock.patch("laboratory.sds_sources.check_needs_update", side_effect=RuntimeError("boom")):
            resumen = tasks.update_sds_and_extract_data(sc_ids=[self.sc_con_pdf.pk], delay=0)
        self.assertEqual(resumen["errors"], 1)
