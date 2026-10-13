import io
from unittest.mock import patch

from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext
from django_celery_results.models import TaskResult
from djgentelella.models import Notification

from laboratory.models import Catalog, Object
from report import register
from report.models import (
    DocumentReportStatus,
    ObjectChangeLogReport,
    ObjectChangeLogReportBuilder,
    TaskReport,
)
from report.tests.utils import XHR, ReportTestBase
from report.views.base import base_pdf, build_report


def en_espanol(texto):
    """El estado se guarda traducido al idioma del reporte (aquí, español)."""
    with translation.override("es"):
        return gettext(texto)


class BasePdfTest(ReportTestBase):
    """`base_pdf` es el exportador PDF común: escribe el fichero y cuenta filas."""

    def test_reporte_generico_genera_pdf(self):
        report = self.make_report("reactive_report", "pdf")
        report.table_content = {
            "columns": [{"name": "name", "title": "Nombre"}],
            "dataset": [["Cal"], ["Sal"]],
        }
        report.save()

        total = base_pdf(report, "http://testserver/")

        report.refresh_from_db()
        self.assertEqual(total, 2)
        self.assertTrue(report.file.name.endswith(".pdf"))
        with report.file.open("rb") as fh:
            self.assertEqual(fh.read(4), b"%PDF")

    def test_compatibilidad_colorea_la_columna_de_compatibilidad(self):
        report = self.make_report("compatibility_report", "pdf", title="")
        report.table_content = {
            "columns": [{"title": str(i)} for i in range(5)],
            "dataset": [
                ["e", "z", "H200", "H220", "Incompatible"],
                ["e", "z", "H200", "H201", "Compatible"],
                ["e", "z", "H200", "H202", "desconocida"],
            ],
        }
        report.save()

        with patch("report.views.base.render_to_string", return_value="<p></p>") as render:
            base_pdf(report, "http://testserver/")

        context = render.call_args.kwargs["context"]
        datalist = context["datalist"]
        # La columna 5 (tras numerar las filas) lleva el color de la etiqueta y
        # el texto en blanco sobre rojo para que se lea.
        self.assertIn(
            '<td style="background-color:#FF0000;color:#FFFFFF;font-weight:bold;">Incompatible</td>',
            datalist,
        )
        self.assertIn(
            '<td style="background-color:#00B050;color:#000000;font-weight:bold;">Compatible</td>',
            datalist,
        )
        self.assertIn("<td>desconocida</td>", datalist)
        # Sin título se usa el nombre del reporte.
        self.assertEqual(context["title"], "reporte-prueba")
        self.assertEqual(context["size_sheet"], "landscape")

    def test_cambios_de_objetos_cuenta_las_filas_del_detalle(self):
        report = self.make_report("report_objectschanges", "pdf")
        log = ObjectChangeLogReport.objects.create(
            task_report=report,
            laboratory=self.lab,
            unit=Catalog.objects.get(pk=63),
            object=Object.objects.get(pk=1),
        )
        for _ in range(3):
            ObjectChangeLogReportBuilder.objects.create(
                report=log, user=self.user, update_time="2024-01-01T00:00:00Z"
            )
        with patch("report.views.base.render_to_string", return_value="<p></p>"):
            self.assertEqual(base_pdf(report, "http://testserver/"), 3)

    def test_muchas_columnas_usan_hoja_b4(self):
        report = self.make_report("reactive_report", "pdf")
        report.table_content = {"columns": [], "dataset": [list(range(9))]}
        report.save()
        with patch("report.views.base.render_to_string", return_value="<p></p>") as render:
            base_pdf(report, "http://testserver/")
        self.assertEqual(render.call_args.kwargs["context"]["size_sheet"], "b4 landscape")


class BuildReportTest(ReportTestBase):
    def test_formato_pdf_pasa_por_html_y_pdf(self):
        report = self.make_report("reactive_report", "pdf")
        build_report(report.pk, "http://testserver/")
        report.refresh_from_db()
        self.assertEqual(report.status, en_espanol("Generated"))
        self.assertTrue(report.file.name.endswith(".pdf"))
        self.assertIn("dataset", report.table_content)

    def test_tipo_desconocido_no_hace_nada(self):
        report = self.make_report("no_existe", "xlsx")
        report.refresh_from_db()
        estado_inicial = report.status
        build_report(report.pk, "http://testserver/")
        report.refresh_from_db()
        # Sin reporte registrado nada cambia: el estado queda como se creó.
        self.assertEqual(report.status, estado_inicial)
        self.assertFalse(DocumentReportStatus.objects.filter(report=report).exists())


class CreateRequestTest(ReportTestBase):
    def url(self, org=None):
        return reverse(
            "report:create_report_request", kwargs={"org_pk": org or self.org.pk}
        )

    def params(self, **extra):
        data = {
            "name": "mi reporte",
            "title": "Mi reporte",
            "organization": self.org.pk,
            "report_name": "reactive_report",
            "format": "xlsx",
            "laboratory": [self.lab.pk],
        }
        data.update(extra)
        return data

    def test_mapa_de_peligros_en_pantalla_redirige_a_la_vista_directa(self):
        response = self.client.get(
            self.url(),
            self.params(report_name="hazard_map_report", format="html", title="Mapa"),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["result"])
        visual = reverse("report:hazard_map_visual", kwargs={"org_pk": self.org.pk})
        self.assertEqual(
            data["redirect_url"], "%s?laboratory=%d&title=Mapa" % (visual, self.lab.pk)
        )
        # No se encola ninguna tarea: la vista directa no pasa por Celery.
        self.assertFalse(TaskReport.objects.exists())

    def test_tarea_que_no_importa_responde_401(self):
        roto = dict(register.REPORT_FORMS["reactive_report"], task="report.no.existe")
        with patch.dict(register.REPORT_FORMS, {"reactive_report": roto}):
            response = self.client.get(self.url(), self.params())
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()["result"])

    def test_crea_la_tarea_y_genera_el_fichero(self):
        response = self.client.get(self.url(), self.params())
        data = response.json()
        self.assertTrue(data["result"])
        report = TaskReport.objects.get(pk=data["report"])
        self.assertEqual(report.created_by, self.user)
        self.assertEqual(report.data["laboratory"], [self.lab.pk])
        self.assertEqual(report.data["org_pk"], self.org.pk)
        self.assertTrue(report.file.name.endswith(".xlsx"))
        self.assertEqual(TaskResult.objects.get(task_id=data["celery_id"]).status, "SUCCESS")

    def test_formulario_invalido_devuelve_errores(self):
        response = self.client.get(self.url(), self.params(name=""))
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.json()["form_errors"])


class DownloadReportTest(ReportTestBase):
    def test_reporte_entregado_como_fichero(self):
        report, celery = self.task()
        response = self.client.get(
            self.url(), {"task": celery.task_id, "taskreport": report.pk}
        )
        data = response.json()
        self.assertTrue(data["result"])
        self.assertEqual(data["url_file"], report.file.url)
        self.assertEqual(data["type_report"], "xlsx")
        self.assertTrue(
            Notification.objects.filter(
                user=self.user, description="reporte-prueba.xlsx"
            ).exists()
        )

    def url(self, org=None):
        return reverse("report:generate_report", kwargs={"org_pk": org or self.org.pk})

    def task(self, file_type="xlsx", **result):
        report = self.make_report("reactive_report", file_type)
        report.status = "Generated"
        if file_type != "html":
            report.file.save("reporte.xlsx", io.BytesIO(b"x"), save=False)
        report.save()
        result.setdefault("status", "SUCCESS")
        celery = TaskResult.objects.create(task_id="tarea-%d" % report.pk, **result)
        return report, celery

    def test_organizacion_ajena_es_401(self):
        response = self.client.get(self.url(self.foreign_org.pk))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["state"], "FAILURE")

    def test_metodo_distinto_de_get_es_405(self):
        response = self.client.post(self.url())
        self.assertEqual(response.status_code, 405)
        self.assertTrue(response.json()["end"])

    def test_formulario_invalido_es_401(self):
        response = self.client.get(self.url(), {"task": "x", "taskreport": 999999})
        self.assertEqual(response.status_code, 401)

    def test_sin_resultado_de_celery_sigue_pendiente(self):
        report = self.make_report("reactive_report")
        response = self.client.get(self.url(), {"task": "nada", "taskreport": report.pk})
        self.assertEqual(response.json()["state"], "PENDING")
        self.assertFalse(response.json()["end"])

    def test_fallo_devuelve_la_traza(self):
        report, celery = self.task(status="FAILURE", traceback="Traceback: boom")
        response = self.client.get(
            self.url(), {"task": celery.task_id, "taskreport": report.pk}
        )
        data = response.json()
        self.assertEqual((data["state"], data["end"]), ("FAILURE", True))
        self.assertEqual(data["error"], "Traceback: boom")
        report.refresh_from_db()
        self.assertEqual(report.status, "Generated")

    def test_html_entrega_la_tabla_y_notifica(self):
        report, celery = self.task(file_type="html")
        response = self.client.get(
            self.url(), {"task": celery.task_id, "taskreport": report.pk}
        )
        data = response.json()
        self.assertTrue(data["result"])
        self.assertEqual(
            data["url_file"],
            reverse("report:report_table", kwargs={"org_pk": self.org.pk, "pk": report.pk}),
        )
        report.refresh_from_db()
        self.assertEqual(report.status, "Delivered")
        self.assertTrue(Notification.objects.filter(user=self.user, link=data["url_file"]).exists())


class ReportTableTest(ReportTestBase):
    def url(self, report, org=None):
        return reverse(
            "report:report_table", kwargs={"org_pk": org or self.org.pk, "pk": report.pk}
        )

    def test_organizacion_ajena_es_404(self):
        report = self.make_report("reactive_report", "html")
        response = self.client.get(self.url(report, self.foreign_org.pk), **XHR)
        self.assertEqual(response.status_code, 404)

    def test_reporte_de_otra_organizacion_es_404(self):
        # El usuario sí entra a su organización, pero la tarea se pidió desde otra.
        report = self.make_report("reactive_report", "html", org_pk=self.foreign_org.pk)
        response = self.client.get(self.url(report), **XHR)
        self.assertEqual(response.status_code, 404)

    def test_cambios_de_objetos_usa_su_plantilla(self):
        report = self.make_report("report_objectschanges", "html")
        log = ObjectChangeLogReport.objects.create(
            task_report=report,
            laboratory=self.lab,
            unit=Catalog.objects.get(pk=63),
            object=Object.objects.get(pk=1),
        )
        response = self.client.get(self.url(report))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "report/log_change.html")
        self.assertEqual(list(response.context["changelogreport"]), [log])

    def test_mapa_de_peligros_usa_su_plantilla(self):
        report = self.make_report("hazard_map_report", "html")
        report.table_content = {"map_data": []}
        report.save()
        response = self.client.get(self.url(report))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "report/hazard_map.html")
        self.assertEqual(response.context["map_data"], [])


class ReportStatusTest(ReportTestBase):
    def test_fallo_expone_el_error_y_el_historial(self):
        report = self.make_report("reactive_report")
        DocumentReportStatus.objects.create(report=report, description="Inicio")
        TaskResult.objects.create(task_id="t-1", status="FAILURE", result="error simple")
        response = self.client.get(
            reverse("report:report_status", kwargs={"org_pk": self.org.pk}),
            {"task": "t-1", "taskreport": report.pk},
        )
        data = response.json()
        self.assertEqual((data["state"], data["end"]), ("FAILURE", True))
        self.assertEqual(data["error"], "error simple")
        self.assertIn("Inicio", data["text"])


class OrganizationRequestTest(ReportTestBase):
    """Las rutas «de organización» comparten formulario y tarea con las de laboratorio."""

    def url(self, org=None):
        return reverse(
            "report:create_organization_report_request",
            kwargs={"org_pk": org or self.org.pk},
        )

    def params(self, **extra):
        data = {
            "name": "reporte org",
            "title": "Reporte org",
            "organization": self.org.pk,
            "report_name": "reactive_report",
            "format": "xlsx",
        }
        data.update(extra)
        return data

    def test_crea_y_genera_el_reporte(self):
        response = self.client.get(self.url(), self.params())
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["result"])
        report = TaskReport.objects.get(pk=data["report"])
        self.assertEqual(report.status, "Generated")
        self.assertTrue(report.file)
        self.assertTrue(TaskResult.objects.filter(task_id=data["celery_id"]).exists())

    def test_formulario_invalido(self):
        response = self.client.get(self.url(), self.params(format="docx"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("format", response.json()["form_errors"])

    def test_tarea_que_no_importa_responde_401(self):
        roto = dict(register.REPORT_FORMS["reactive_report"], task="report.no.existe")
        with patch.dict(register.REPORT_FORMS, {"reactive_report": roto}):
            response = self.client.get(self.url(), self.params())
        self.assertEqual(response.status_code, 401)

    def test_organizacion_inexistente_es_401(self):
        response = self.client.get(self.url(999999), self.params(), **XHR)
        self.assertIn(response.status_code, (401, 404))


class DownloadOrganizationReportTest(ReportTestBase):
    def url(self, org=None):
        return reverse(
            "report:generate_organization_report",
            kwargs={"org_pk": org or self.org.pk},
        )

    def entregar(self, file_type):
        report = self.make_report("reactive_report", file_type)
        report.status = "Generated"
        if file_type != "html":
            report.file.save("r.xlsx", io.BytesIO(b"x"), save=False)
        report.save()
        TaskResult.objects.create(task_id="org-%d" % report.pk, status="SUCCESS")
        response = self.client.get(
            self.url(), {"task": "org-%d" % report.pk, "taskreport": report.pk}
        )
        report.refresh_from_db()
        return report, response

    def test_html_apunta_a_la_tabla_de_organizacion(self):
        report, response = self.entregar("html")
        self.assertEqual(report.status, "Delivered")
        self.assertEqual(
            response.json()["url_file"],
            reverse(
                "report:report_organization_table",
                kwargs={"org_pk": self.org.pk, "pk": report.pk},
            ),
        )

    def test_fichero_devuelve_su_url(self):
        report, response = self.entregar("xlsx")
        self.assertEqual(response.json()["url_file"], report.file.url)
        self.assertTrue(Notification.objects.filter(link=report.file.url).exists())

    def test_formulario_invalido_es_401(self):
        response = self.client.get(self.url(), {"task": "x"})
        self.assertEqual(response.status_code, 401)

    def test_organizacion_inexistente_es_401(self):
        response = self.client.get(self.url(999999), {"task": "x", "taskreport": 1}, **XHR)
        self.assertIn(response.status_code, (401, 404))


class ReportOrganizationTableTest(ReportTestBase):
    def get(self, report):
        return self.client.get(
            reverse(
                "report:report_organization_table",
                kwargs={"org_pk": self.org.pk, "pk": report.pk},
            )
        )

    def test_tabla_general(self):
        report = self.make_report("reactive_report", "html")
        report.table_content = {"columns": [], "dataset": []}
        report.save()
        response = self.get(report)
        self.assertTemplateUsed(response, "report/general_organization_report.html")

    def test_cambios_de_objetos(self):
        report = self.make_report("report_objectschanges", "html")
        response = self.get(report)
        self.assertTemplateUsed(response, "report/log_change.html")

    def test_regencia(self):
        report = self.make_report("regency_report", "html")
        response = self.get(report)
        # El HTML de regencia guarda columnas y filas como los demás reportes.
        self.assertTemplateUsed(response, "report/general_organization_report.html")

    def test_mapa_de_peligros(self):
        report = self.make_report("hazard_map_report", "html")
        report.table_content = {"map_data": []}
        report.save()
        response = self.get(report)
        self.assertTemplateUsed(response, "report/hazard_map.html")
