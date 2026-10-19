from datetime import datetime, timedelta, timezone as dt_timezone

from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from django.utils import translation

from laboratory.models import (
    BaseUnitValues,
    Catalog,
    Furniture,
    Laboratory,
    Object,
    ObjectLogChange,
)
from report.models import (
    DocumentReportStatus,
    ObjectChangeLogReport,
    ObjectChangeLogReportBuilder,
    TaskReport,
)
from report.utils import (
    calc_duration,
    filter_period,
    format_date,
    format_datetime,
    local_datetime,
    period_range,
    get_conversion_units_to_kilograms,
    get_furniture_queryset_by_filters,
    get_pdf_log_change_table_content,
    get_pdf_table_content,
    get_report_name,
    sanitize_ods_table,
    set_format_table_columns,
)
from presentation.pdf import html_to_pdf
from report.tests.utils import ReportTestBase


class FormatoDeFechasTest(SimpleTestCase):
    """Las fechas del periodo llegan como texto `dd/mm/aaaa` desde el datepicker."""

    def test_format_date_valida(self):
        self.assertEqual(format_date("05/03/2024"), datetime(2024, 3, 5))

    def test_format_date_invalida_devuelve_none(self):
        self.assertIsNone(format_date("2024-03-05"))

    def test_format_datetime_inicio_y_fin_del_dia(self):
        self.assertEqual(
            format_datetime("05/03/2024", "initial"), timezone.make_aware(datetime(2024, 3, 5))
        )
        self.assertEqual(
            format_datetime("05/03/2024", "final"),
            timezone.make_aware(datetime(2024, 3, 5, 23, 59, 59, 999999)),
        )

    def test_period_range_incluye_el_ultimo_dia_completo(self):
        inicio, fin = period_range("14/03/2026 - 14/03/2026")
        self.assertEqual(inicio, timezone.make_aware(datetime(2026, 3, 14)))
        self.assertEqual(fin, timezone.make_aware(datetime(2026, 3, 14, 23, 59, 59, 999999)))
        self.assertEqual(
            period_range("03/14/2026 - 03/14/2026", input_format="%m/%d/%Y"), (inicio, fin)
        )
        self.assertIsNone(period_range("14/03/2026 - ayer"))
        self.assertIsNone(period_range(""))

    def test_local_datetime_usa_la_zona_horaria_de_settings(self):
        momento = datetime(2026, 3, 15, 2, 18, 55, tzinfo=dt_timezone.utc)
        self.assertEqual(local_datetime(momento), "14/03/2026 20:18:55")
        self.assertEqual(local_datetime(momento, "%Y-%m-%d"), "2026-03-14")
        self.assertEqual(local_datetime(None), "")

    def test_format_datetime_invalida_devuelve_none(self):
        self.assertIsNone(format_datetime("no es fecha", "initial"))


class PresentacionDeTablasTest(SimpleTestCase):
    def test_columnas_con_tipo_desconocido_heredan_el_anterior(self):
        columnas = set_format_table_columns(
            [
                {"name": "a", "title": "A", "type": "number"},
                {"name": "b", "title": "B", "type": "inventado"},
                {"name": "", "title": "sin nombre"},
                {"name": "c"},
            ]
        )
        self.assertEqual([c["name"] for c in columnas], ["a", "b", "c"])
        self.assertEqual([c["type"] for c in columnas], ["number", "number", "number"])
        # Sin título propio se arrastra el último visto.
        self.assertEqual(columnas[2]["title"], "B")

    def test_tabla_pdf_numera_filas_y_aplica_estilo(self):
        contenido = {
            "columns": [{"title": "Nombre"}, {"name": "sin_titulo"}],
            "dataset": [["Cal", 1], ["Sal", 2]],
        }
        html = get_pdf_table_content(
            contenido,
            cell_style_fn=lambda idx, valor: ' class="c%d"' % idx,
        )
        self.assertIn("<th>Item</th><th>Nombre</th></tr>", html)
        self.assertIn('<td class="c0">1</td><td class="c1">Cal</td>', html)
        self.assertIn('<td class="c0">2</td><td class="c1">Sal</td>', html)
        self.assertTrue(html.endswith("</tbody></table>"))

    def test_tabla_pdf_celda_sin_dato_queda_vacia(self):
        html = get_pdf_table_content({"columns": [{"title": "Código"}, {"title": "Nombre"}], "dataset": [[None, "Cal"]]})
        self.assertIn("<td>1</td><td></td><td>Cal</td>", html)
        self.assertNotIn("None", html)

    def test_tabla_pdf_sin_filas_lo_dice(self):
        html = get_pdf_table_content({"columns": [{"title": "Nombre"}, {"title": "CAS"}], "dataset": []})
        self.assertIn("<th>Item</th><th>Nombre</th><th>CAS</th>", html)
        self.assertIn("<tr><td colspan='3'>No records.</td></tr>", html)

    def test_tabla_pdf_con_indicaciones_de_peligro_largas(self):
        # Con ancho automático la columna quedaba estrecha y la fila del
        # formaldehído (nueve códigos H) era más alta que la página: xhtml2pdf
        # no parte filas y el PDF entero fallaba con LayoutError.
        peligro = ", ".join([
            "(H301) Tóxico en caso de ingestión",
            "(H311) Tóxico en contacto con la piel",
            "(H314) Provoca graves quemaduras en la piel y lesiones oculares",
            "(H317) Puede provocar una reacción cutánea alérgica",
            "(H331) Tóxico si se inhala",
            "(H335) Puede irritar las vías respiratorias o provocar somnoliencia",
            "(H341) Suscepctible a provocar cancer (Indíquese la vías de exósición si se ha demostrado concluyendtemente que ninguna otra vía es peligrosa)",
            "(H350) Puede provocar cáncer (indíquese la vía de exposición si se ha demostrado concluyentemente que ninguna otra vía es peligrosa)",
            "(H370) Provoca daños en los órganos (o indíquese todos los órganos afectados, si se conocen) "
            "(Indíquese la vía de exposición si se ha demostrado concluyentemente que ninguna otra vía es peligrosa)",
        ])
        columnas = ["shelfobject_code", "code", "name", "type", "features",
                    "danger_indication", "molecular_formula", "cas_id_number"]
        contenido = {
            "columns": [{"name": nombre, "title": nombre} for nombre in columnas],
            "dataset": [["UC-1", "REA-1", "Formaldehído", "Reactivo", "Sólido", peligro, "CH2O", "50-00-0"]],
        }
        datalist = get_pdf_table_content(contenido)
        self.assertIn("<th width='35%'>danger_indication</th>", datalist)
        html = render_to_string("report/base_report_pdf.html", {
            "datalist": datalist, "title": "Objetos", "size_sheet": "landscape",
        })
        self.assertTrue(html_to_pdf(html).startswith(b"%PDF"))

    def test_tabla_pdf_sin_dataset_queda_vacia(self):
        self.assertEqual(get_pdf_table_content({"columns": []}), "")

    def test_sanitize_ods_table_limpia_nulos_y_escalares(self):
        self.assertEqual(
            sanitize_ods_table([None, "texto", 3, ["a", None, 1]]),
            [[""], ["texto"], [3], ["a", "", 1]],
        )


class NombreYDuracionTest(SimpleTestCase):
    """Los textos esperados están en inglés: no depender del idioma que deje otra prueba."""

    def setUp(self):
        self.enterContext(translation.override("en"))

    def report(self, **data):
        return TaskReport(data=data)

    def test_nombre_por_prioridad(self):
        self.assertEqual(get_report_name(self.report(name="n", title="t")), "n")
        self.assertEqual(get_report_name(self.report(name="", title="t")), "t")
        self.assertEqual(get_report_name(self.report(report_name="r")), "r")
        self.assertEqual(str(get_report_name(self.report())), "Report")

    def test_duracion_en_segundos_y_minutos(self):
        inicio = timezone.now()
        valor, unidad = calc_duration(inicio, inicio + timedelta(seconds=30))
        self.assertEqual((valor, str(unidad)), (30.0, "seconds"))
        valor, unidad = calc_duration(inicio, inicio + timedelta(minutes=3, seconds=5))
        self.assertEqual((valor, str(unidad)), (3.0, "minutes"))


class FiltroPorPeriodoTest(ReportTestBase):
    def setUp(self):
        super().setUp()
        base = {
            "object": Object.objects.get(pk=1),
            "laboratory": self.lab,
            "user": self.user,
            "measurement_unit": Catalog.objects.get(pk=63),
        }
        self.dentro = ObjectLogChange.objects.create(**base)
        self.fuera = ObjectLogChange.objects.create(**base)
        ObjectLogChange.objects.filter(pk=self.dentro.pk).update(
            update_time=timezone.make_aware(datetime(2024, 3, 10, 12))
        )
        ObjectLogChange.objects.filter(pk=self.fuera.pk).update(
            update_time=timezone.make_aware(datetime(2024, 5, 10, 12))
        )

    def test_filtra_por_rango(self):
        qs = filter_period("01/03/2024 - 31/03/2024", ObjectLogChange.objects.all())
        self.assertIn(self.dentro, qs)
        self.assertNotIn(self.fuera, qs)

    def test_texto_sin_rango_no_filtra(self):
        todos = ObjectLogChange.objects.all()
        self.assertIs(filter_period("01/03/2024", todos), todos)


class ConversionAKilogramosTest(TestCase):
    """La regencia suma en kilogramos: los volúmenes pasan por la densidad."""

    def unit(self, description):
        return Catalog.objects.filter(key="units", description=description).first()

    def test_litros_con_y_sin_densidad(self):
        litros = self.unit("Litros")
        self.assertEqual(get_conversion_units_to_kilograms(litros, 10, density=2), 20)
        self.assertAlmostEqual(get_conversion_units_to_kilograms(litros, 10), 8.0)

    def test_mililitros_se_reducen_antes_de_la_densidad(self):
        mililitros = self.unit("Mililitros")
        self.assertAlmostEqual(
            get_conversion_units_to_kilograms(mililitros, 1000, density=1.5), 1.5
        )

    def test_libras_no_usan_densidad(self):
        kilos = self.unit("Kilogramos")
        libra = Catalog.objects.create(key="units", description="Libra")
        BaseUnitValues.objects.create(
            measurement_unit=libra, measurement_unit_base=kilos, si_value=1
        )
        self.assertAlmostEqual(
            get_conversion_units_to_kilograms(libra, 10, density=99), 4.536
        )

    def test_unidad_sin_conversion_da_cero(self):
        rara = Catalog.objects.create(key="units", description="Sin base")
        self.assertEqual(get_conversion_units_to_kilograms(rara, 10), 0)


class MueblesPorFiltroTest(ReportTestBase):
    def test_sala_acota_los_muebles(self):
        report = TaskReport(
            data={"organization": self.org.pk, "laboratory": [], "lab_room": [2]}
        )
        muebles = get_furniture_queryset_by_filters(report)
        self.assertEqual(
            set(muebles), set(Furniture.objects.filter(labroom__pk=2))
        )
        self.assertTrue(muebles.exists())


class TablaPdfDeCambiosTest(ReportTestBase):
    """El PDF del reporte de cambios se arma desde las filas ya calculadas."""

    def test_tabla_por_objeto_con_y_sin_usuario(self):
        report = self.make_report("report_objectschanges", "pdf")
        obj = Object.objects.get(pk=1)
        unidad = Catalog.objects.get(pk=63)
        log = ObjectChangeLogReport.objects.create(
            task_report=report,
            laboratory=self.lab,
            unit=unidad,
            object=obj,
            diff_value=3,
        )
        sin_nombre = User.objects.create(username="solo-usuario")
        momento = datetime(2024, 1, 2, 3, 4, 5, tzinfo=dt_timezone.utc)
        for user in (self.user, sin_nombre, None):
            ObjectChangeLogReportBuilder.objects.create(
                report=log,
                user=user,
                update_time=momento,
                old_value=1,
                new_value=4,
                diff_value=3,
            )

        html = get_pdf_log_change_table_content(report)

        self.assertIn(f"{self.lab.name} | {obj.name}", html)
        self.assertIn(f"Difference: 3.0 {unidad.description}", html)
        self.assertIn("<td>Organilab Admin</td>", html)
        self.assertIn("<td>solo-usuario</td>", html)
        # Una fila sin usuario no rompe la tabla: queda la celda vacía.
        self.assertIn("<td></td>", html)
        self.assertEqual(html.count("<td>01/01/2024 21:04:05</td>"), 3)


class ModelosYTareaTest(ReportTestBase):
    def test_representacion_de_reporte_y_estado(self):
        report = self.make_report("reactive_report", "xlsx")
        self.assertEqual(str(report), f"{report.pk} - reactive_report - xlsx")
        estado = DocumentReportStatus.objects.create(report=report, description="Listo")
        self.assertTrue(str(estado).endswith(" Listo"))

    def test_tarea_con_reporte_inexistente_falla_con_mensaje(self):
        from django.core.exceptions import ObjectDoesNotExist

        from report.tasks import task_report

        with self.assertRaises(ObjectDoesNotExist):
            task_report(999999, "http://testserver/")

    def test_tarea_que_falla_conserva_el_error_y_lo_registra(self):
        from unittest.mock import patch

        from report.tasks import task_report

        report = self.make_report("reactive_report", "pdf")
        with patch("report.tasks.build_report", side_effect=ValueError("no cabe")):
            with self.assertRaisesMessage(ValueError, "no cabe"):
                task_report(report.pk, "http://testserver/")
        self.assertEqual(
            list(DocumentReportStatus.objects.filter(report=report).values_list("description", flat=True)),
            ["Error al generar el reporte"],
        )
