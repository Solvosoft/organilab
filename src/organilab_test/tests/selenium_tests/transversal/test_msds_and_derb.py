from django.test import tag

from organilab_test.tests.selenium_tests.transversal.base import (
    TransversalSeleniumBase,
)
from organilab_test.tests.selenium_xpaths import datatable_search_input


@tag("selenium")
class MsdsPagesTest(TransversalSeleniumBase):
    """Las pantallas de `msds`: índice, fichas verificadas y regulaciones."""

    def test_msds_verified_sds_flow(self):
        self.navigate("index_msds", namespace="msds", org_pk=self.org_pk)
        self.take_screenshot_list(
            [{"path": "//*[@id='msdstable']", "presence_only": True,
              "wait_dt": True}],
            "msds_index",
        )

        self.navigate("verified_sds", namespace="msds", org_pk=self.org_pk)
        self.take_screenshot_list(
            [
                {"path": "//*[@id='sds-traceability-table']",
                 "presence_only": True, "wait_dt": True},
                {"path": datatable_search_input("sds-traceability-table"),
                 "extra_action": "setvalue", "value": "a"},
                {"path": "//*[@id='sds-traceability-table']",
                 "presence_only": True, "wait_dt": True},
            ],
            "msds_verified",
        )

        # `regulation_docs` y `download_all_regulations` se montan en la raíz
        # (`organilab/urls.py:104` añade `regulation_urlpath` fuera del
        # include con namespace), así que van sin prefijo "msds:".
        self.navigate("regulation_docs")


@tag("selenium")
class DerbFormListTest(TransversalSeleniumBase):
    """Listado y previsualización de formularios dinámicos (formio).

    El constructor con arrastrar y soltar ya lo cubre
    `laboratory/.../informs/test_inform_template.py`; lo que falta aquí es el
    listado y la previsualización, que no tenían prueba.
    """

    def test_derb_form_list_and_preview_flow(self):
        self.navigate("form_list", namespace="derb", org_pk=self.org_pk)
        self.take_screenshot_list(
            [{"path": "//*[@id='form_table']", "presence_only": True,
              "wait_dt": True}],
            "derb_form_list",
        )

        formulario = self.primer_formulario()
        if formulario is None:
            self.skipTest("la fixture no trae ningún CustomForm que previsualizar")
        self.navigate("preview_form", namespace="derb", org_pk=self.org_pk,
                      form_id=formulario.pk)
        self.navigate("edit_view", namespace="derb", org_pk=self.org_pk,
                      form_id=formulario.pk)

    def primer_formulario(self):
        from derb.models import CustomForm

        return CustomForm.objects.first()
