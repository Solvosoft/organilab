from django.test import tag

from organilab_test.tests.base import modifies_db
from organilab_test.tests.selenium_xpaths import datatable_search_input
from sga.tests.selenium_tests.base import SgaSeleniumBase


@tag("selenium")
class SubstanceReviewTest(SgaSeleniumBase):
    """Pantalla de revisión y aprobación de sustancias.

    Cubre `approved_substance` (con su DataTable y el filtro "ver aprobadas") y
    `accept_substance`.

    La sustancia en revisión se monta por ORM: llegar hasta aquí por pantalla
    exigiría pasar `send_to_review`, que a su vez exige una ficha de seguridad
    subida por el widget de carga por trozos. Ese camino es el flujo S3, con su
    propia complejidad; repetirlo aquí solo alargaría la corrida sin cubrir
    nada nuevo.
    """

    fixtures = ["selenium/base_selenium.json", "selenium/laboratory_delta.json"]

    def setUp(self):
        super().setUp()
        self.review = self.crear_sustancia_en_revision()

    def crear_sustancia_en_revision(self):
        from laboratory.models import OrganizationStructure
        from sga.models import ReviewSubstance, Substance

        substance = Substance.objects.create(
            comercial_name="Sustancia en revision selenium",
            created_by=self.user,
            organization=OrganizationStructure.objects.get(pk=self.org_pk),
        )
        return ReviewSubstance.objects.create(
            substance=substance, created_by=self.user, is_approved=False
        )

    @modifies_db
    def test_substance_review_flow(self):
        self.navigate_to_sga("approved_substance")
        self.take_screenshot_list(
            [
                {"path": "//*[@id='substancetable']", "presence_only": True,
                 "wait_dt": True},
                {"path": datatable_search_input("substancetable"),
                 "extra_action": "setvalue", "value": "selenium"},
                {"path": "//*[@id='substancetable']", "presence_only": True,
                 "wait_dt": True},
            ],
            "sga_review_substance",
        )
        self.assertIn("Sustancia en revision selenium", self.selenium.page_source)

        # Aprobar: la vista es alcanzable por GET y redirige al listado.
        self.navigate_to_sga("accept_substance", pk=self.review.pk)
        self.review.refresh_from_db()
        self.assertTrue(self.review.is_approved)

        # Y el listado con el filtro de aprobadas la muestra ya marcada.
        self.navigate("approved_substance", org_pk=self.org_pk,
                      _query={"showapprove": 1})
        self.take_screenshot_list(
            [{"path": "//*[@id='substancetable']", "presence_only": True,
              "wait_dt": True}],
            "sga_review_substance",
        )
