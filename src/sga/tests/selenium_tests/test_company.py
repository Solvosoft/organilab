from django.test import tag

from organilab_test.tests.base import modifies_db
from organilab_test.tests.selenium_xpaths import SWEETALERT_CONFIRM
from sga.tests.selenium_tests.base import SgaSeleniumBase


@tag("selenium")
class SgaCompanyCrudTest(SgaSeleniumBase):
    """CRUD de empresas emisoras de etiqueta, encadenado.

    A diferencia de los catálogos SGA, aquí el alta y la edición son páginas
    propias (`add_company` / `edit_company`) con un formulario normal, y solo el
    borrado va por JS con SweetAlert (`remove_company`).
    """

    fixtures = ["selenium/base_selenium.json"]

    @modifies_db
    def test_sga_company_crud_flow(self):
        self.navigate_to_sga("get_companies")
        self.take_screenshot_list(
            [
                # Alta: enlace a la página de creación.
                {"path": "//a[contains(@class, 'btn-success')]"},
                {"path": "//*[@id='id_name']", "extra_action": "setvalue",
                 "value": "Empresa selenium", "clear": True},
                {"path": "//*[@id='id_phone']", "extra_action": "setvalue",
                 "value": "22334455", "clear": True},
                {"path": "//*[@id='id_address']", "extra_action": "setvalue",
                 "value": "San José", "clear": True},
                {"path": "//button[@type='submit']", "wait_ready": True},
                # Edición: la vista redirige al listado, así que la fila existe.
                {"path": "//a[contains(@class, 'btn-warning')]"},
                {"path": "//*[@id='id_name']", "extra_action": "setvalue",
                 "value": "Empresa selenium editada", "clear": True},
                {"path": "//button[@type='submit']", "wait_ready": True},
                # Borrado: confirma por SweetAlert, no por modal.
                {"path": "//a[contains(@class, 'btn-danger')]"},
                {"path": SWEETALERT_CONFIRM},
                {"path": "//*[@id='companytable']", "presence_only": True,
                 "wait_ready": True},
            ],
            "sga_company",
        )
