"""Reportes de `laboratory.views.reports`: PDF de objetos por laboratorio, código H
en hoja de cálculo, índice de reportes y el SVG de cobertura de FDS.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse

from laboratory.models import (
    Laboratory,
    Object,
    OrganizationStructure,
    ShelfObject,
)
from laboratory.tests.utils import BaseLaboratorySetUpTest
from sga.models import SDSTraceability, SubstanceCharacteristics


def assert_error_page(test, response, status):
    """`HandleErrorMiddleware` convierte 403/404 en redirección a la página de error."""
    test.assertEqual(response.status_code, 302)
    test.assertIn("status=%d" % status, response["Location"])


class ReportShelfObjectsTest(BaseLaboratorySetUpTest):

    def url(self, pk, lab_pk=None):
        return reverse(
            "laboratory:reports_shelf_objects",
            kwargs={"org_pk": self.org.pk, "lab_pk": lab_pk or self.lab.pk, "pk": pk},
        )

    def test_pk_cero_incluye_todos_los_objetos_del_laboratorio(self):
        response = self.client.get(self.url(0))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        esperado = set(
            ShelfObject.objects.filter(
                shelf__furniture__labroom__laboratory=self.lab
            ).values_list("pk", flat=True)
        )
        self.assertTrue(esperado)
        self.assertEqual(
            {so.pk for so in response.context["object_list"]}, esperado
        )

    def test_pk_de_otro_laboratorio_no_se_incluye(self):
        objeto = ShelfObject.objects.filter(
            shelf__furniture__labroom__laboratory=self.lab
        ).first()
        otro_lab = Laboratory.objects.get(name="Lab Ultra")
        response = self.client.get(self.url(objeto.pk, lab_pk=otro_lab.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["object_list"]), [])

    def test_laboratorio_fuera_de_la_organizacion_responde_403(self):
        otra_org = OrganizationStructure.objects.get(name="Organization Testing")
        lab_ajeno = Laboratory.objects.create(name="Lab ajeno", organization=otra_org)
        response = self.client.get(self.url(0, lab_pk=lab_ajeno.pk))
        assert_error_page(self, response, 403)

    def test_organizacion_ajena_responde_403(self):
        otra_org = OrganizationStructure.objects.get(name="Organization Testing")
        url = reverse(
            "laboratory:reports_shelf_objects",
            kwargs={"org_pk": otra_org.pk, "lab_pk": self.lab.pk, "pk": 0},
        )
        response = self.client.get(url)
        assert_error_page(self, response, 403)


class ReportHCodeHojaTest(BaseLaboratorySetUpTest):

    def test_descarga_en_formato_de_hoja(self):
        url = reverse(
            "laboratory:download_h_code_reports", kwargs={"org_pk": self.org.pk}
        )
        response = self.client.get(url, {"format": "xlsx"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("hcode_report.xlsx", response["Content-Disposition"])


class ReportIndexTest(BaseLaboratorySetUpTest):

    def test_usuario_sin_membresia_recibe_404(self):
        user = get_user_model().objects.get(username="tuwp")
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="laboratory", codename="view_report"
            )
        )
        self.client.force_login(user)
        response = self.client.get(
            reverse("laboratory:reports", kwargs={"org_pk": self.org.pk})
        )
        assert_error_page(self, response, 404)


class SDSCoverageSVGTest(BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        self.org_svg = OrganizationStructure.objects.get(name="Chec Org")
        for nombre, fuente in [("Ácido A", "merck"), ("Ácido B", None)]:
            obj = Object.objects.create(name=nombre, type=0, organization=self.org_svg)
            sc = SubstanceCharacteristics.objects.create(object_related=obj)
            if fuente:
                SDSTraceability.objects.create(
                    sga_substance_characteristics=sc, source=fuente
                )

    def test_varias_fuentes_dibujan_un_arco_por_segmento(self):
        url = reverse("laboratory:sds_coverage_svg", kwargs={"org_pk": self.org_svg.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        svg = response.content.decode()
        self.assertEqual(svg.count("<path "), 2)
        self.assertIn("Merck/Sigma-Aldrich (1)", svg)
        self.assertIn("50%</text>", svg)
