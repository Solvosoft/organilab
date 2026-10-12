from datetime import datetime, timezone as dt_timezone

from django.contrib.auth.models import User

from laboratory.models import Object, ObjectLogChange
from report.models import ObjectChangeLogReport, ObjectChangeLogReportBuilder
from report.tests.utils import ReportTestBase
from report.views.objects import report_objectlogchange_doc, report_objectlogchange_html
from sga.models import SubstanceCharacteristics

EN_PERIODO = datetime(2024, 3, 10, 12, tzinfo=dt_timezone.utc)
ANTES = datetime(2023, 1, 10, 12, tzinfo=dt_timezone.utc)


class ObjectChangesReportTest(ReportTestBase):
    """Reporte de cambios de inventario: resumen por objeto y detalle por usuario.

    Un objeto que sigue en el laboratorio pero no cambió durante el periodo
    aparece igual, con diferencia cero, para que el informe no lo omita.
    """

    def setUp(self):
        super().setUp()
        self.cal = Object.objects.get(pk=2)
        self.tanque = Object.objects.get(pk=1)
        SubstanceCharacteristics.objects.filter(object_related=self.cal).update(
            cas_id_number="1305-78-8"
        )
        self.sin_nombre = User.objects.create(username="solo-usuario")
        self.log(self.cal, self.user, 1, 3)
        self.log(self.cal, self.sin_nombre, 3, 4)
        self.log(self.cal, None, 4, 6, deleted_user_info="Usuario borrado")
        fantasma = self.log(self.cal, self.user, 6, 7)
        # El usuario no tiene FK con restricción: puede desaparecer.
        ObjectLogChange.objects.filter(pk=fantasma.pk).update(user_id=999999)
        # Fuera del periodo: el tanque solo tiene historia anterior.
        self.log(self.tanque, self.user, 0, 23, when=ANTES)

    def log(self, obj, user, old, new, when=EN_PERIODO, **extra):
        entry = ObjectLogChange.objects.create(
            object=obj,
            laboratory=self.lab,
            user=user or self.user,
            old_value=old,
            new_value=new,
            diff_value=new - old,
            measurement_unit=self.unit(),
            precursor=True,
            **extra,
        )
        ObjectLogChange.objects.filter(pk=entry.pk).update(update_time=when)
        return entry

    def report(self, file_type, **data):
        data.setdefault("period", "01/03/2024 - 31/03/2024")
        data.setdefault("precursor", True)
        return self.make_report("report_objectschanges", file_type, **data)

    def test_html_guarda_resumen_y_detalle(self):
        report = self.report("html")
        # Devuelve las filas de detalle: una por cambio del periodo.
        self.assertEqual(report_objectlogchange_html(report), 4)

        resumen = ObjectChangeLogReport.objects.get(task_report=report, object=self.cal)
        self.assertEqual(resumen.diff_value, 6)
        usuarios = {
            b.user.username if b.user else None
            for b in ObjectChangeLogReportBuilder.objects.filter(report=resumen)
        }
        self.assertEqual(usuarios, {"admin", "solo-usuario", None})
        # El tanque no cambió en el periodo pero se reporta con diferencia 0.
        tanque = ObjectChangeLogReport.objects.get(task_report=report, object=self.tanque)
        self.assertEqual(tanque.diff_value, 0)

    def test_documento_lista_usuarios_y_objetos_sin_cambios(self):
        report = self.report("xlsx", laboratory=[1, 2])
        self.assertGreaterEqual(report_objectlogchange_doc(report), 4)
        filas = [f for f in self.read_xlsx(report) if any(f)]
        textos = [str(f[0]) for f in filas]
        self.assertIn(f"{self.lab.name} | {self.cal.name} 1305-78-8", textos)
        self.assertIn(f": 6.0 {self.unit().description}", textos)
        self.assertIn("Organilab Admin", textos)
        self.assertIn("solo-usuario", textos)
        self.assertIn("Usuario borrado", textos)
        self.assertIn(None, [f[0] for f in filas if f[1] is not None])
        self.assertIn(f"{self.lab.name} | {self.tanque.name} {self.tanque.cas_code}", textos)
        self.assertIn(f": 0 {self.unit().description}", textos)

    def test_sin_laboratorios_usa_los_de_la_organizacion(self):
        report = self.report("html", laboratory=[], period="")
        self.assertGreaterEqual(report_objectlogchange_html(report), 4)
