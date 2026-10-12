from django.contrib.auth.models import User

from laboratory.models import Object, ObjectFeatures, ObjectLogChange, ShelfObjectLimits
from report.tests.utils import ReportTestBase
from report.views.objects import (
    report_limit_object_doc,
    report_limit_object_html,
    report_objects_doc,
    report_objects_html,
    report_organization_reactive_list_doc,
    report_reactive_exposition_html,
    report_reactive_precursor_doc,
    report_reactive_precursor_html,
)
from sga.models import DangerIndication, SubstanceCharacteristics


def column_names(report):
    return [c["name"] for c in report.table_content["columns"]]


class PrecursorReportTest(ReportTestBase):
    """Reporte de precursores: la columna de laboratorio solo aparece si hay varios."""

    def setUp(self):
        super().setUp()
        self.cal = Object.objects.get(pk=2)
        SubstanceCharacteristics.objects.update(is_precursor=False)
        SubstanceCharacteristics.objects.filter(object_related=self.cal).update(
            is_precursor=True
        )

    def test_un_laboratorio_suma_cajas_por_su_contenido(self):
        caja = self.make_shelfobject(
            self.cal,
            quantity=1,
            is_box=True,
            quantity_units=[{"units": 1, "quantity": 4}, {"units": 1, "quantity": 6}],
        )
        report = self.make_report("reactive_precursor", "html")
        total = report_reactive_precursor_html(report)

        report.refresh_from_db()
        self.assertNotIn("laboratory", column_names(report))
        self.assertEqual(total, 1)
        fila = dict(zip(column_names(report), report.table_content["dataset"][0]))
        self.assertEqual(fila["name"], self.cal.name)
        # Las unidades sueltas del fixture (23 + 2 + 2) más el contenido de la caja.
        sueltas = sum(
            so.quantity for so in self.cal.shelfobject_set.filter(
                in_where_laboratory=self.lab, is_box=False
            )
        )
        self.assertEqual(fila["quantity_total"], round(sueltas + 10, 3))
        self.assertTrue(caja.pk)

    def test_sin_laboratorios_en_el_payload_es_general(self):
        report = self.make_report("reactive_precursor", "html")
        del report.data["laboratory"]
        report.save()
        report_reactive_precursor_html(report)
        report.refresh_from_db()
        self.assertEqual(column_names(report)[0], "laboratory")
        self.assertTrue(report.table_content["dataset"])

    def test_documento_general_y_por_laboratorio(self):
        general = self.make_report("reactive_precursor", "xlsx", laboratory=[])
        self.assertGreater(report_reactive_precursor_doc(general), 0)
        filas = self.read_xlsx(general)
        self.assertEqual(filas[0][0], "reporte-prueba")
        self.assertEqual(len(filas[1]), 10)

        uno = self.make_report("reactive_precursor", "xlsx")
        report_reactive_precursor_doc(uno)
        filas = self.read_xlsx(uno)
        self.assertEqual(len([c for c in filas[1] if c is not None]), 9)
        self.assertEqual(filas[2][1], self.cal.name)


class ObjectsReportTest(ReportTestBase):
    def setUp(self):
        super().setUp()
        self.cal = Object.objects.get(pk=2)
        self.cal.features.add(ObjectFeatures.objects.create(name="Corrosivo", description="x"))
        self.h_codes = list(DangerIndication.objects.order_by("code")[:2])
        sga = SubstanceCharacteristics.objects.get(object_related=self.cal)
        sga.molecular_formula = "CaO"
        sga.cas_id_number = "1305-78-8"
        sga.save()
        sga.h_code.set(self.h_codes)

    def test_html_filtra_por_tipo_y_lista_peligros(self):
        report = self.make_report("report_objects", "html", object_type="0")
        report_objects_html(report)
        report.refresh_from_db()
        nombres = column_names(report)
        self.assertNotIn("laboratory", nombres)
        filas = [dict(zip(nombres, f)) for f in report.table_content["dataset"]]
        self.assertTrue(filas)
        self.assertEqual({f["type"] for f in filas}, {"Reactive"})
        cal = [f for f in filas if f["name"] == self.cal.name][0]
        self.assertEqual(cal["molecular_formula"], "CaO")
        self.assertEqual(cal["cas_id_number"], "1305-78-8")
        self.assertEqual(cal["danger_indication"], ", ".join(str(h) for h in self.h_codes))
        self.assertIn("Corrosivo", cal["features"])
        self.assertIn(", ", cal["features"])

    def test_tipo_desconocido_no_filtra(self):
        con_tipo = self.make_report("report_objects", "html", object_type="0")
        sin_tipo = self.make_report("report_objects", "html", object_type="9")
        self.assertLess(report_objects_html(con_tipo), report_objects_html(sin_tipo))

    def test_documento_quita_la_columna_de_laboratorio_si_hay_uno(self):
        uno = self.make_report("report_objects", "xlsx", object_type="0")
        total = report_objects_doc(uno)
        filas = self.read_xlsx(uno)
        self.assertEqual(len(filas) - 2, total)
        self.assertEqual(len([c for c in filas[1] if c is not None]), 8)

        varios = self.make_report("report_objects", "xlsx", object_type="0", laboratory=[1, 2])
        report_objects_doc(varios)
        filas = self.read_xlsx(varios)
        self.assertEqual(len([c for c in filas[1] if c is not None]), 9)
        self.assertEqual(filas[2][0], self.lab.name)


class LimitedObjectsReportTest(ReportTestBase):
    """Solo salen las unidades cuyo inventario toca exactamente un límite."""

    def setUp(self):
        super().setUp()
        cal = Object.objects.get(pk=2)
        self.en_minimo = self.make_shelfobject(
            cal, quantity=5,
            limits=ShelfObjectLimits.objects.create(minimum_limit=5, maximum_limit=10),
        )
        self.caja = self.make_shelfobject(
            cal, quantity=3, is_box=True,
            quantity_units=[{"units": 4, "quantity": 1}, {"units": 6, "quantity": 1}],
            limits=ShelfObjectLimits.objects.create(minimum_limit=0, maximum_limit=2),
        )
        self.lejos = self.make_shelfobject(
            cal, quantity=7,
            limits=ShelfObjectLimits.objects.create(minimum_limit=1, maximum_limit=20),
        )

    def test_html_muestra_limites_y_cajas(self):
        report = self.make_report("report_limit_objects", "html")
        self.assertEqual(report_limit_object_html(report), 2)
        report.refresh_from_db()
        nombres = column_names(report)
        self.assertNotIn("laboratory", nombres)
        filas = {f[nombres.index("quantity")]: dict(zip(nombres, f)) for f in report.table_content["dataset"]}
        self.assertEqual(filas[5]["minimun_limit"], 5)
        self.assertEqual(filas[5]["maximum_limit"], 10)
        caja = filas[2]
        self.assertEqual(caja["minimun_limit"], "-----")
        self.assertEqual(caja["measurement_unit"], "(10) units per box")
        self.assertIn("Box of", caja["object"])

    def test_documento_por_uno_y_varios_laboratorios(self):
        uno = self.make_report("report_limit_objects", "xlsx")
        self.assertEqual(report_limit_object_doc(uno), 2)
        filas = self.read_xlsx(uno)
        self.assertEqual(len([c for c in filas[1] if c is not None]), 8)
        self.assertEqual(filas[2][0], "Primer Estante")

        varios = self.make_report("report_limit_objects", "xlsx", laboratory=[1, 2])
        report_limit_object_doc(varios)
        filas = self.read_xlsx(varios)
        self.assertEqual(filas[2][0], self.lab.name)

    def test_sin_laboratorios_usa_los_de_la_organizacion(self):
        report = self.make_report("report_limit_objects", "html", laboratory=[])
        self.assertEqual(report_limit_object_html(report), 2)


class OrganizationReactiveReportTest(ReportTestBase):
    """Exposición a reactivos por funcionario: un usuario sin perfil no lo tumba."""

    def setUp(self):
        super().setUp()
        self.sin_perfil = User.objects.create(
            username="sinperfil", first_name="Sin", last_name="Perfil"
        )
        self.cal = Object.objects.get(pk=2)
        for user in (self.user, self.sin_perfil):
            ObjectLogChange.objects.create(
                object=self.cal, laboratory=self.lab, user=user,
                measurement_unit=self.unit(),
            )

    def test_filtra_por_usuarios_y_tolera_falta_de_perfil(self):
        report = self.make_report(
            "report_organization_reactive_list", "html", users=[self.sin_perfil.pk]
        )
        self.assertEqual(report_reactive_exposition_html(report), 1)
        report.refresh_from_db()
        fila = dict(zip(column_names(report), report.table_content["dataset"][0]))
        self.assertEqual(fila["name"], "Sin Perfil")
        self.assertEqual(fila["id_card"], "")
        self.assertEqual(fila["substance"], self.cal.name)

    def test_documento_con_perfil(self):
        report = self.make_report(
            "report_organization_reactive_list", "xlsx", users=[self.user.pk]
        )
        # El fixture ya trae un cambio del mismo usuario sobre otro reactivo.
        self.assertEqual(report_organization_reactive_list_doc(report), 2)
        filas = self.read_xlsx(report)
        cal = [f for f in filas[2:] if f[3] == self.cal.name][0]
        self.assertEqual(cal[1], "Organilab Admin")
        self.assertEqual(cal[7], self.user.profile.id_card)
