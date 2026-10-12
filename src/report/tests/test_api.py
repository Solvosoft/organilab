from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from djgentelella.models import HistoryRelation

from laboratory.models import (
    Catalog,
    Laboratory,
    Object,
    PrecursorReport,
    PrecursorReportValues,
)
from report.models import (
    ObjectChangeLogReport,
    ObjectChangeLogReportBuilder,
    RegencyReport,
    RegencyReportBuilder,
)
from report.tests.utils import XHR, ReportTestBase
from sga.models import SubstanceCharacteristics


class ReportDataApiTest(ReportTestBase):
    """El endpoint que alimenta el DataTable de un reporte en pantalla."""

    def setUp(self):
        super().setUp()
        self.report = self.make_report("reactive_report", "html")
        self.report.table_content = {
            "columns": [{"name": "name"}, {"name": "unit"}],
            "dataset": [["Cal", "ml"], ["Sal", "g"], ["Calcio", "g"], ["Agua", "ml"]],
        }
        self.report.save()

    def get(self, **params):
        response = self.client.get(
            reverse("report:api-report-detail", kwargs={"pk": self.report.pk}), params
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_filtros_por_columna_orden_y_paginacion(self):
        data = self.get(name="CAL", unit="g", ordering=["-name", "unit"], limit=5, draw=3)
        self.assertEqual(data["data"], [["Calcio", "g"]])
        self.assertEqual((data["recordsTotal"], data["recordsFiltered"]), (4, 1))
        self.assertEqual(data["draw"], 3)

        data = self.get(ordering="name", limit=2, offset=1)
        self.assertEqual(data["data"], [["Cal", "ml"], ["Calcio", "g"]])

    def test_filtro_con_comilla_no_rompe_la_consulta(self):
        """Los filtros iban pegados al SQL: una comilla cerraba la cadena.

        Con `' OR '1'='1` se devolvían todas las filas (o un 500 con otra
        carga útil). Ahora el valor viaja como parámetro.
        """
        data = self.get(name="x' OR '1'='1", ordering="name")
        self.assertEqual(data["data"], [])
        self.assertEqual(data["recordsFiltered"], 0)

    def test_limite_no_numerico_y_orden_desconocido(self):
        data = self.get(limit="1; DROP TABLE report_taskreport", offset="-3", ordering="nope")
        self.assertEqual(data["recordsTotal"], 4)
        self.assertEqual(len(data["data"]), 4)


class ReportDataLogApiTest(ReportTestBase):
    def setUp(self):
        super().setUp()
        self.report = self.make_report("report_objectschanges", "html")
        self.obj = Object.objects.get(pk=2)
        self.unidad = Catalog.objects.get(pk=63)
        log = ObjectChangeLogReport.objects.create(
            task_report=self.report, laboratory=self.lab, unit=self.unidad, object=self.obj
        )
        sin_nombre = User.objects.create(username="solo-usuario")
        for user, new in ((self.user, 4), (sin_nombre, 7), (None, 9)):
            ObjectChangeLogReportBuilder.objects.create(
                report=log, user=user, update_time="2024-03-10T12:00:00Z",
                old_value=1, new_value=new, diff_value=new - 1,
            )

    def get(self, **params):
        base = {"laboratory": self.lab.pk, "object": self.obj.pk, "unit": self.unidad.pk}
        base.update(params)
        response = self.client.get(
            reverse("report:api-report-log-detail", kwargs={"pk": self.report.pk}), base
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_detalle_del_objeto(self):
        """Una fila sin usuario (usuario borrado) también se lista."""
        data = self.get(ordering="new_value")
        self.assertEqual(
            [r["user"] for r in data["data"]],
            ["Organilab Admin", "solo-usuario", "No user found"],
        )
        self.assertEqual(data["data"][0]["update_time"], "03/10/2024, 12:00:00")

    def test_filtro_por_usuario(self):
        """El filterset exige un pk y el filtro extra pedía el texto en nombre
        completo Y usuario a la vez: filtrar por usuario nunca devolvía filas."""
        data = self.get(user=str(self.user.pk))
        self.assertEqual([r["new_value"] for r in data["data"]], [4.0])

    def test_filtros_de_columna_y_periodo(self):
        self.assertEqual(len(self.get(new_value="7")["data"]), 1)
        self.assertEqual(len(self.get(update_time="03/01/2024 - 03/31/2024")["data"]), 3)
        self.assertEqual(len(self.get(update_time="01/01/2023 - 01/31/2023")["data"]), 0)
        self.assertEqual(len(self.get(update_time="sin rango")["data"]), 3)
        # Antes un rango con fechas ilegibles terminaba en 500.
        self.assertEqual(len(self.get(update_time="ayer - hoy")["data"]), 3)

    def test_busqueda_global(self):
        self.assertEqual(len(self.get(search="solo")["data"]), 1)

    def test_sin_filtros_validos_no_hay_filas(self):
        response = self.client.get(
            reverse("report:api-report-log-detail", kwargs={"pk": self.report.pk})
        )
        self.assertEqual(response.json()["data"], [])


class ObjectChangeLogSerializerTest(ReportTestBase):
    def test_sin_usuario_ni_fecha(self):
        from report.api.serializers import ObjectChangeLogSerializer

        serializer = ObjectChangeLogSerializer()
        builder = ObjectChangeLogReportBuilder(user=None, update_time=None)
        self.assertEqual(str(serializer.get_user(builder)), "No user found")
        self.assertEqual(str(serializer.get_user(None)), "No user found")
        self.assertEqual(serializer.get_update_time(builder), "")


class RegencyApiTest(ReportTestBase):
    def test_lista_por_paso(self):
        task = self.make_report("regency_report", "html")
        regency = RegencyReport.objects.create(task_report=task, organization=self.org, year=2024)
        cal = Object.objects.get(pk=2)
        RegencyReportBuilder.objects.create(
            report=regency, substance=cal, danger_category="health", danger_list=3,
            total=2, break_threshold=True,
        )
        RegencyReportBuilder.objects.create(
            report=regency, substance=cal, danger_category="physical", danger_list=4, total=1,
        )
        url = reverse("report:api-regency-list", kwargs={"org_pk": self.org.pk})
        data = self.client.get(url, {"pk": task.pk, "step": 3}).json()
        self.assertEqual(len(data["data"]), 1)
        fila = data["data"][0]
        self.assertEqual(fila["break_threshold"], "Yes")
        self.assertEqual(fila["danger_category"], "health")
        self.assertTrue(fila["actions"]["list"])

        sin_paso = self.client.get(url, {"pk": task.pk}).json()
        self.assertEqual(sin_paso["data"], [])

        segundo = self.client.get(url, {"pk": task.pk, "step": 4}).json()
        self.assertEqual(segundo["data"][0]["break_threshold"], "No")


class PrecursorReportValuesApiTest(ReportTestBase):
    """CRUD de los valores de un reporte de precursores, atado a su organización."""

    def setUp(self):
        super().setUp()
        for codename in ("view", "add", "change", "delete"):
            self.user.user_permissions.add(
                Permission.objects.get(
                    content_type=ContentType.objects.get_for_model(PrecursorReportValues),
                    codename="%s_precursorreportvalues" % codename,
                )
            )
        self.cal = Object.objects.get(pk=2)
        SubstanceCharacteristics.objects.filter(object_related=self.cal).update(is_precursor=True)
        # Laboratorio 2 de la org 1: su pk no coincide con el del reporte.
        self.lab = Laboratory.objects.get(pk=2)
        self.precursor = PrecursorReport.objects.create(
            month=3, month_belong=2, year=2024, laboratory=self.lab
        )
        self.value = PrecursorReportValues.objects.create(
            precursor_report=self.precursor, object=self.cal, measurement_unit=self.unit(),
        )

    def url(self, pk=None, precursor=None, org=None):
        kwargs = {
            "org_pk": org or self.org.pk,
            "precusor_pk": precursor or self.precursor.pk,
        }
        if pk:
            kwargs["pk"] = pk
            return reverse("report:api-precursor-report-values-detail", kwargs=kwargs)
        return reverse("report:api-precursor-report-values-list", kwargs=kwargs)

    def payload(self, **extra):
        data = {
            "object": self.cal.pk,
            "measurement_unit": self.unit().pk,
            "quantity": 1,
            "previous_balance": 2,
            "new_income": 3,
            "stock": 5,
            "month_expense": 1,
            "final_balance": 4,
            "reason_to_spend": "",
        }
        data.update(extra)
        return data

    def related(self, value_pk):
        return {
            (r.content_type.model, r.object_id)
            for r in HistoryRelation.objects.filter(
                log_entry__object_id=str(value_pk), content_type__isnull=False
            )
        }

    def test_lista(self):
        data = self.client.get(self.url()).json()
        self.assertEqual([r["id"] for r in data["data"]], [self.value.pk])
        self.assertTrue(data["data"][0]["actions"]["destroy"])

    def test_crear_editar_y_borrar_registran_laboratorio_y_organizacion(self):
        response = self.client.post(self.url(), self.payload(), content_type="application/json")
        self.assertEqual(response.status_code, 201, response.content)
        nuevo = PrecursorReportValues.objects.exclude(pk=self.value.pk).get()
        self.assertEqual(nuevo.precursor_report, self.precursor)
        esperado = {("laboratory", self.lab.pk), ("organizationstructure", self.org.pk)}
        self.assertEqual(self.related(nuevo.pk), esperado)

        response = self.client.put(
            self.url(nuevo.pk), self.payload(final_balance=9), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200, response.content)
        nuevo.refresh_from_db()
        self.assertEqual(nuevo.final_balance, 9)

        response = self.client.delete(self.url(nuevo.pk))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(PrecursorReportValues.objects.filter(pk=nuevo.pk).exists())
        self.assertEqual(self.related(nuevo.pk), esperado)

    def test_reporte_de_otra_organizacion_es_404(self):
        ajeno_lab = Laboratory.objects.create(name="Ajeno", organization=self.foreign_org)
        ajeno = PrecursorReport.objects.create(
            month=3, month_belong=2, year=2024, laboratory=ajeno_lab
        )
        valor = PrecursorReportValues.objects.create(
            precursor_report=ajeno, object=self.cal, measurement_unit=self.unit(),
        )
        self.assertEqual(self.client.get(self.url(precursor=ajeno.pk), **XHR).status_code, 404)
        response = self.client.delete(self.url(valor.pk, precursor=ajeno.pk), **XHR)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(PrecursorReportValues.objects.filter(pk=valor.pk).exists())
        response = self.client.post(
            self.url(precursor=ajeno.pk), self.payload(), content_type="application/json", **XHR
        )
        self.assertEqual(response.status_code, 404)
