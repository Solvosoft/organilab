from django.test import tag

from organilab_test.tests.base import modifies_db
from organilab_test.tests.selenium_xpaths import (
    SGA_ICON_DELETE,
    SGA_ICON_UPDATE,
    SWEETALERT_CONFIRM,
    datatable_row_icon,
    modal_submit_btn,
    sga_catalog_add_btn,
)
from sga.tests.selenium_tests.base import SgaSeleniumBase


@tag("selenium")
class SgaCatalogsCrudTest(SgaSeleniumBase):
    """CRUD de los catálogos SGA, encadenado en un solo flujo.

    Los cuatro catálogos —palabras de advertencia, indicaciones de peligro,
    consejos de prudencia y tamaños de recipiente— son la misma pantalla con
    otro dataset, pero NO usan el ObjectCRUD de gentelella: van sobre
    `laboratory/js/base_modal_management.js` con un JS propio por catálogo. De
    ahí que el botón de alta sea `btn-success` y no `btn-outline-success`, y que
    borrar confirme por SweetAlert en vez de por un modal `.delbtn`.

    El flujo se construye sus propios datos —crea, edita y borra lo que él
    mismo creó—, así que no depende de filas sembradas por fixture ni por
    migración. Eso importa aquí: `TransactionTestCase` hace flush entre tests y
    se lleva por delante lo que sembraron las migraciones.
    """

    # Solo el esquema base: este flujo no necesita catálogos precargados.
    fixtures = ["selenium/base_selenium.json"]

    @modifies_db
    def test_sga_catalogs_crud_flow(self):
        self.navigate_to_sga("warning_words")
        self.take_screenshot_list(
            self.catalog_create_steps(
                table_id="warningwordtable",
                modal_id="warningwordmodal",
                values={"id_name": "Peligro selenium", "id_weigth": "3"},
            )
            + self.catalog_update_steps(
                table_id="warningwordtable",
                modal_id="warningwordmodal",
                values={"id_name": "Peligro selenium editado"},
            )
            + self.catalog_delete_steps(table_id="warningwordtable"),
            "sga_warning_words",
        )

    # --- Pasos reutilizables por los cuatro catálogos ---

    def catalog_create_steps(self, table_id, modal_id, values):
        steps = [
            {"path": sga_catalog_add_btn(table_id)},
        ]
        for field_id, value in values.items():
            steps.append(
                {"path": "//*[@id='%s']" % field_id, "extra_action": "setvalue",
                 "value": value, "clear": True}
            )
        # Guardar dispara un SweetAlert de confirmación que hay que cerrar: es
        # su `.then()` el que recarga la DataTable.
        steps += [
            {"path": modal_submit_btn(modal_id)},
            {"path": SWEETALERT_CONFIRM},
            {"path": "//*[@id='%s']" % table_id, "presence_only": True,
             "wait_dt": True},
        ]
        return steps

    def catalog_update_steps(self, table_id, modal_id, values):
        steps = [
            {"path": datatable_row_icon(table_id, SGA_ICON_UPDATE)},
        ]
        for field_id, value in values.items():
            steps.append(
                {"path": "//*[@id='%s']" % field_id, "extra_action": "setvalue",
                 "value": value, "clear": True}
            )
        steps += [
            {"path": modal_submit_btn(modal_id)},
            {"path": SWEETALERT_CONFIRM},
            {"path": "//*[@id='%s']" % table_id, "presence_only": True,
             "wait_dt": True},
        ]
        return steps

    def catalog_delete_steps(self, table_id):
        # Dos SweetAlerts seguidos: el «¿seguro?» y el «borrado con éxito».
        return [
            {"path": datatable_row_icon(table_id, SGA_ICON_DELETE)},
            {"path": SWEETALERT_CONFIRM},
            {"path": SWEETALERT_CONFIRM},
            {"path": "//*[@id='%s']" % table_id, "presence_only": True,
             "wait_dt": True},
        ]
