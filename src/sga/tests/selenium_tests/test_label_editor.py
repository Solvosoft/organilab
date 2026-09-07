from django.test import tag

from organilab_test.tests.base import modifies_db
from organilab_test.tests.selenium_xpaths import (
    SGA_EDITOR_IFRAME,
    modal_submit_btn,
)
from sga.tests.selenium_tests.base import SgaSeleniumBase


@tag("selenium")
class SgaLabelTemplateTest(SgaSeleniumBase):
    """Plantillas de etiqueta SGA: editor, alta y edición.

    Cubre `editor`, `add_personal`, `sgalabel_create`, `sgalabel_step_one`,
    `sgalabel_step_two` y `edit_personal`.

    `edit_personal` merece atención propia: es una de las páginas que estaban en
    `KNOWN_BROKEN`. Reventaba SIEMPRE, no solo sin código de barras, porque
    `sga/views/editor.py:256` leía `display_label.barcotesthtml.htmlde` y ese
    atributo no existe en ningún modelo del proyecto (el campo es
    `DisplayLabel.barcode`). Este flujo es la regresión de ese arreglo.

    La plantilla base se crea por ORM: `TemplateSGA` cuelga de `RecipientSize` y
    ninguna de las dos viene en la fixture, y montarlas por pantalla sería
    recorrer otro CRUD que ya cubre S4.
    """

    fixtures = ["selenium/base_selenium.json"]

    def setUp(self):
        super().setUp()
        self.plantilla = self.crear_plantilla()

    def crear_plantilla(self):
        from laboratory.models import OrganizationStructure
        from sga.models import RecipientSize, TemplateSGA

        recipiente = RecipientSize.objects.create(
            name="Recipiente selenium", height=10, width=10
        )
        return TemplateSGA.objects.create(
            name="Plantilla selenium",
            recipient_size=recipiente,
            json_representation="[]",
            community_share=True,
            is_default=True,
            organization=OrganizationStructure.objects.get(pk=self.org_pk),
        )

    def test_sga_editor_page_loads(self):
        """El editor de plantillas monta su iframe."""
        self.navigate_to_sga("editor")
        self.take_screenshot_list(
            [{"path": SGA_EDITOR_IFRAME, "presence_only": True}],
            "sga_template_editor",
        )

    @modifies_db
    def test_sga_label_template_flow(self):
        # 1. Listado de etiquetas personales y alta por modal.
        self.navigate_to_sga("add_personal")
        self.take_screenshot_list(
            [
                {"path": "//*[@id='newsgalabel']"},
                {"path": "//*[@id='id_name']", "extra_action": "setvalue",
                 "value": "Etiqueta selenium", "clear": True},
            ]
            + self.select_option_steps("id_template", str(self.plantilla.pk))
            + [{"path": modal_submit_btn("newsgalabelmodal"), "wait_ready": True}],
            "sga_label_create",
        )
        # El alta redirige al paso 1 del asistente de etiqueta.
        self.assertIn("step_one", self.selenium.current_url,
                      "el alta de etiqueta no validó; sigue en %s"
                      % self.selenium.current_url)

        etiqueta = self.etiqueta_creada()

        # 2. Paso dos del asistente.
        self.navigate_to_sga("sgalabel_step_two", pk=etiqueta.pk)

        # 3. Edición de la etiqueta personal: la página del bug de la fase 0.
        self.navigate_to_sga("edit_personal", pk=etiqueta.pk)
        self.assertIn("Etiqueta selenium", self.selenium.page_source)

    def etiqueta_creada(self):
        from sga.models import DisplayLabel

        return DisplayLabel.objects.filter(name="Etiqueta selenium").first()
