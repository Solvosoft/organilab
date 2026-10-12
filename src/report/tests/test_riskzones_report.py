from django.urls import reverse

from laboratory.models import Laboratory, Object, OrganizationStructure, Shelf
from report.tests.utils import XHR, ReportTestBase
from report.views import riskzones
from risk_management.compatibility_utils import H_CODE_TO_CLASS, get_h_code_compatibility
from risk_management.models import Buildings, RiskZone, ZoneType
from sga.models import DangerIndication, HCodeCategory, SubstanceCharacteristics


class RiskZoneDataMixin:
    """Edificio de la org 1 con una zona de riesgo que contiene el laboratorio 1."""

    def build_zone(self, labs=None, name="Zona A", building=None):
        building = building or self.building
        zone = RiskZone.objects.create(
            name=name, organization=self.org, num_workers=3,
            zone_type=self.zone_type,
        )
        zone.buildings.add(building)
        zone.laboratories.set(labs if labs is not None else [self.lab])
        return zone

    def setUp(self):
        super().setUp()
        self.zone_type = ZoneType.objects.create(name="Laboratorio")
        self.building = Buildings.objects.create(name="Edificio A", organization=self.org)
        self.building.laboratories.add(self.lab)
        self.cal = Object.objects.get(pk=2)
        self.sga = SubstanceCharacteristics.objects.get(object_related=self.cal)
        # El fixture le da códigos H al Tanque; cada prueba pone los suyos.
        for caracteristicas in SubstanceCharacteristics.objects.all():
            caracteristicas.h_code.clear()

    def incompatible_codes(self):
        codes = list(
            DangerIndication.objects.filter(code__in=list(H_CODE_TO_CLASS)).order_by("code")
            .values_list("code", flat=True)
        )
        for i, a in enumerate(codes):
            for b in codes[i + 1:]:
                if get_h_code_compatibility(a, b) == "R":
                    return a, b
        self.fail("No hay un par de códigos H incompatibles en la base")


class RiskZoneReportTest(RiskZoneDataMixin, ReportTestBase):
    """Reporte de zona de riesgo: cuadro 3/4 y si se supera el umbral."""

    def report(self, file_type="html", **data):
        data.setdefault("risk_zone", [])
        data.setdefault("building", [])
        return self.make_report("risk_zone_report", file_type, **data)

    def rows(self, report):
        report.refresh_from_db()
        names = [c["name"] for c in report.table_content["columns"]]
        return {r[names.index("name")]: dict(zip(names, r)) for r in report.table_content["dataset"]}

    def test_umbral_de_categoria_h_se_evalua(self):
        """Una sustancia del cuadro 4 supera el umbral de su categoría H.

        Los umbrales llegaban como `values_list` y `get_hcode_threshold` solo
        miraba listas: nunca evaluaba nada y el reporte decía «No supera» para
        cualquier cantidad, un falso negativo regulatorio.
        """
        code = DangerIndication.objects.order_by("code").first()
        # 0.001 t = 1 kg; el laboratorio tiene varios litros de Cal.
        HCodeCategory.objects.create(danger_category="health", threshold=0.001).h_code.add(code)
        self.sga.h_code.set([code])
        self.make_shelfobject(self.cal, quantity=5000)  # 5 L
        filas = self.rows(self.run_html(self.report()))
        self.assertEqual(filas[self.cal.name]["square"], "Square 4")
        self.assertEqual(filas[self.cal.name]["threshold"], "Yes Exceeds Threshold")

    def run_html(self, report):
        riskzones.report_risk_zone_html(report)
        return report

    def test_cuadro_4_sin_superar(self):
        code = DangerIndication.objects.order_by("code").first()
        HCodeCategory.objects.create(danger_category="physical", threshold=1000).h_code.add(code)
        self.sga.h_code.set([code])
        filas = self.rows(self.run_html(self.report()))
        self.assertEqual(filas[self.cal.name]["threshold"], "No Exceeds Threshold")
        self.assertEqual(filas[self.cal.name]["cas_id"], self.cal.cas_code)

    def test_cuadro_3_supera_umbral_propio(self):
        Object.objects.filter(pk=self.cal.pk).update(
            is_dangerous=True, has_threshold=True, threshold=0.00001
        )
        filas = self.rows(self.run_html(self.report()))
        self.assertEqual(filas[self.cal.name]["square"], "Square 3 ")
        self.assertEqual(filas[self.cal.name]["threshold"], "Yes Exceeds Threshold")

    def test_sin_cuadro_es_na(self):
        filas = self.rows(self.run_html(self.report()))
        self.assertEqual(filas[self.cal.name]["square"], "None")
        self.assertEqual(filas[self.cal.name]["threshold"], "NA")

    def test_la_cantidad_no_suma_inventario_de_otras_organizaciones(self):
        """El total de una sustancia es el de los laboratorios del reporte.

        Se sumaban todas las unidades de ese objeto en la base, incluidas las de
        otras organizaciones: el umbral se superaba con inventario ajeno.
        """
        Object.objects.filter(pk=self.cal.pk).update(
            is_dangerous=True, has_threshold=True, threshold=1
        )
        ajeno = Laboratory.objects.create(name="Ajeno", organization=self.foreign_org)
        self.make_shelfobject(self.cal, quantity=5_000_000, in_where_laboratory=ajeno)
        filas = self.rows(self.run_html(self.report()))
        self.assertEqual(filas[self.cal.name]["threshold"], "No Exceeds Threshold")

    def test_zona_y_edificio_definen_los_laboratorios(self):
        zona = self.build_zone()
        report = self.report("html", laboratory=[], risk_zone=[zona.pk], building=[self.building.pk])
        filas = self.rows(self.run_html(report))
        self.assertIn(self.cal.name, filas)
        self.assertEqual(filas[self.cal.name]["in_where_laboratory__name"], self.lab.name)

        solo_edificio = self.report("html", laboratory=[], building=[self.building.pk])
        self.assertIn(self.cal.name, self.rows(self.run_html(solo_edificio)))

    def test_sin_filtros_usa_las_zonas_de_la_organizacion(self):
        self.build_zone()
        report = self.report("xlsx", laboratory=[])
        total = riskzones.report_risk_zone_list_doc(report)
        filas = self.read_xlsx(report)
        self.assertEqual(len(filas) - 2, total)
        self.assertIn(self.cal.name, [f[1] for f in filas])

    def test_varios_laboratorios(self):
        filas = self.rows(self.run_html(self.report(laboratory=[1, 2])))
        self.assertIn(self.cal.name, filas)

    def test_get_hcode_threshold(self):
        self.assertTrue(riskzones.get_hcode_threshold([0.001], 2))
        self.assertFalse(riskzones.get_hcode_threshold([0.001], 0.5))
        self.assertFalse(riskzones.get_hcode_threshold(False, 10))
        # Un umbral sin definir (0 o None) no cuenta como superado.
        self.assertFalse(riskzones.get_hcode_threshold([0, None], 10))
        categoria = HCodeCategory(danger_category="health", threshold=0.001)
        self.assertTrue(riskzones.get_hcode_threshold([categoria], 2))


class CompatibilityReportTest(RiskZoneDataMixin, ReportTestBase):
    def report(self, file_type="html", **data):
        return self.make_report("compatibility_report", file_type, **data)

    def table(self, **data):
        report = self.report(**data)
        riskzones.report_compatibility_html(report)
        report.refresh_from_db()
        return report.table_content

    def test_par_incompatible_con_motivo(self):
        a, b = self.incompatible_codes()
        self.sga.h_code.set(DangerIndication.objects.filter(code__in=[a, b]))
        zona = self.build_zone()
        contenido = self.table(risk_zone=[zona.pk])
        names = [c["name"] for c in contenido["columns"]]
        filas = [dict(zip(names, f)) for f in contenido["dataset"]]
        self.assertEqual(len(filas), 1)
        fila = filas[0]
        self.assertEqual((fila["h_code_a"], fila["h_code_b"]), (a, b))
        self.assertEqual(fila["compatibility"], "Incompatible")
        self.assertTrue(fila["reason"])
        self.assertIn(self.cal.name, fila["substances_a"])
        self.assertEqual(fila["laboratory_a"], self.lab.name)
        self.assertNotIn("diagnostic", contenido)

    def test_filtro_por_edificio_y_zona_ajena_al_filtro(self):
        a, b = self.incompatible_codes()
        self.sga.h_code.set(DangerIndication.objects.filter(code__in=[a, b]))
        self.build_zone()
        otra = self.build_zone(name="Zona B")
        contenido = self.table(building=[self.building.pk], risk_zone=[otra.pk])
        self.assertEqual({f[1] for f in contenido["dataset"]}, {"Zona B"})

    def diagnostic(self, **data):
        contenido = self.table(**data)
        self.assertEqual(contenido["dataset"], [])
        return contenido["diagnostic"]

    def test_diagnostico_sin_edificios(self):
        Buildings.objects.all().delete()
        self.assertIn("No buildings", self.diagnostic()["message"])

    def test_diagnostico_sin_zonas(self):
        self.assertIn("No risk zones", self.diagnostic()["message"])

    def test_diagnostico_zona_sin_laboratorios(self):
        self.build_zone(labs=[])
        self.assertIn("none have laboratories", self.diagnostic()["message"])

    def test_diagnostico_laboratorio_sin_reactivos(self):
        vacio = Laboratory.objects.create(name="Vacío", organization=self.org)
        self.build_zone(labs=[vacio])
        diag = self.diagnostic()
        self.assertIn("no reactive substances", diag["message"])
        self.assertEqual(diag["stats"]["laboratories"], 1)

    def test_diagnostico_reactivos_sin_codigos(self):
        SubstanceCharacteristics.objects.all().delete()
        self.build_zone()
        self.assertIn("none have H-codes", self.diagnostic()["message"])

    def test_diagnostico_un_solo_codigo(self):
        self.sga.h_code.set([DangerIndication.objects.order_by("code").first()])
        self.build_zone()
        diag = self.diagnostic()
        self.assertIn("Only one unique H-code", diag["message"])
        self.assertEqual(diag["stats"]["unique_h_codes"], 1)

    def test_diagnostico_codigos_en_zonas_distintas(self):
        a, b = self.incompatible_codes()
        self.sga.h_code.set(DangerIndication.objects.filter(code=a))
        otro_lab = Laboratory.objects.create(name="Lab B", organization=self.org)
        tanque = Object.objects.get(pk=1)
        tanque_sga = SubstanceCharacteristics.objects.get(object_related=tanque)
        tanque_sga.h_code.set(DangerIndication.objects.filter(code=b))
        self.make_shelfobject(tanque, shelf=Shelf.objects.get(pk=1), in_where_laboratory=otro_lab)
        SubstanceCharacteristics.objects.exclude(pk__in=[self.sga.pk, tanque_sga.pk]).delete()
        # La zona A solo ve a Cal; la zona B solo al Tanque del otro laboratorio.
        tanque.shelfobject_set.filter(in_where_laboratory=self.lab).delete()
        self.build_zone()
        self.build_zone(labs=[otro_lab], name="Zona B")
        diag = self.diagnostic()
        self.assertIn("Each zone needs at least 2", diag["message"])

    def test_diagnostico_respeta_el_filtro_de_zonas(self):
        zona = self.build_zone()
        otra = self.build_zone(name="Zona B")
        diag = self.diagnostic(risk_zone=[otra.pk])
        self.assertEqual(diag["stats"]["risk_zones"], 1)
        self.assertTrue(zona.pk)

    def test_ods(self):
        a, b = self.incompatible_codes()
        self.sga.h_code.set(DangerIndication.objects.filter(code__in=[a, b]))
        self.build_zone()
        report = self.report("ods", org_pk=self.org.pk)
        del report.data["organization"]
        report.save()
        self.assertEqual(riskzones.report_compatibility_ods(report), 1)
        report.refresh_from_db()
        self.assertTrue(report.file.name.endswith(".ods"))


class HazardMapVisualTest(RiskZoneDataMixin, ReportTestBase):
    def url(self, org=None):
        return reverse("report:hazard_map_visual", kwargs={"org_pk": org or self.org.pk})

    def test_laboratorios_pedidos(self):
        response = self.client.get(self.url(), {"laboratory": [self.lab.pk], "title": "Mapa"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [m["laboratory"] for m in response.context["map_data"]], [self.lab.name]
        )
        self.assertEqual(response.context["title"], "Mapa")

    def test_organizacion_ajena_es_404(self):
        response = self.client.get(self.url(self.foreign_org.pk), **XHR)
        self.assertEqual(response.status_code, 404)

    def test_sin_laboratorios_es_404(self):
        vacia = OrganizationStructure.objects.create(name="Vacía")
        vacia.users.add(self.user)
        response = self.client.get(self.url(vacia.pk), **XHR)
        self.assertEqual(response.status_code, 404)

    def test_laboratorio_de_otra_organizacion_no_se_muestra(self):
        """El mapa solo dibuja laboratorios de la organización de la URL.

        Los pks venían de la query string sin cruzarlos con la organización, y
        cualquier miembro podía ver el mapa de peligros de un laboratorio ajeno.
        """
        ajeno = Laboratory.objects.create(name="Ajeno", organization=self.foreign_org)
        response = self.client.get(self.url(), {"laboratory": [ajeno.pk]}, **XHR)
        self.assertEqual(response.status_code, 404)

        response = self.client.get(
            self.url(), {"laboratory": [ajeno.pk, self.lab.pk, "x"]}
        )
        self.assertEqual(
            [m["laboratory"] for m in response.context["map_data"]], [self.lab.name]
        )


class HazardMapReportTest(RiskZoneDataMixin, ReportTestBase):
    def test_html_y_pdf(self):
        report = self.make_report("hazard_map_report", "pdf")
        self.assertEqual(riskzones.report_hazard_map_html(report), 1)
        report.refresh_from_db()
        self.assertEqual(report.table_content["map_data"][0]["laboratory"], self.lab.name)
        self.assertEqual(riskzones.report_hazard_map_pdf(report, "http://testserver/"), 1)
        report.refresh_from_db()
        with report.file.open("rb") as fh:
            self.assertEqual(fh.read(4), b"%PDF")

    def test_sin_laboratorios_usa_los_de_la_organizacion(self):
        report = self.make_report("hazard_map_report", "html", laboratory=[])
        self.assertEqual(
            riskzones.report_hazard_map_html(report), len(set(self.org.get_my_laboratories))
        )
