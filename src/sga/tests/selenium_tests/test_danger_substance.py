from django.test import tag

from organilab_test.tests.base import modifies_db
from organilab_test.tests.selenium_xpaths import (
    GT_ICON_DELETE,
    GT_ICON_UPDATE,
    datatable_row_icon,
    gt_crud_create_btn,
    gt_modal_delete_btn,
    modal_submit_btn,
    select2_field,
    select2_result,
)
from sga.tests.selenium_tests.base import SgaSeleniumBase


@tag("selenium")
class DangerSubstanceCrudTest(SgaSeleniumBase):
    """CRUD de sustancias peligrosas y de sus categorías.

    Las dos pantallas sí son ObjectCRUD de gentelella (tabla `#tableobj` y los
    modales `create_obj_modal` / `update_obj_modal` / `delete_obj_modal`), con
    los formularios prefijados `create` / `update`.

    El código H se obtiene con get_or_create, no se crea a secas. Matiz que
    cuesta un fallo si se pasa por alto: `DangerIndication` lo siembran las
    migraciones de sga y `code` es su clave primaria, así que en el primer test
    de la clase la fila ya existe. Solo desaparece DESPUÉS de un test marcado
    con `@modifies_db`, que es cuando `OptimizedSeleniumBase` hace el flush. Con
    `create()` el primer test revienta con IntegrityError y el segundo pasaría:
    idempotente es la única forma que funciona en los dos casos.
    """

    fixtures = ["selenium/base_selenium.json"]

    def setUp(self):
        super().setUp()
        self.hcode = self.crear_codigo_h()

    def crear_codigo_h(self):
        from sga.models import DangerIndication, WarningWord

        palabra = WarningWord.objects.first() or WarningWord.objects.create(
            name="Peligro", weigth=1
        )
        hcode, _creado = DangerIndication.objects.get_or_create(
            code="H200",
            defaults={
                "description": "Explosivo inestable",
                "warning_words": palabra,
            },
        )
        return hcode

    @modifies_db
    def test_danger_substance_catalog_flow(self):
        # 1. Categoría: h_code es un autocomplete por AJAX, hay que buscar.
        self.navigate_to_sga("danger_substance_category")
        self.take_screenshot_list(
            [
                {"path": gt_crud_create_btn("tableobj")},
                {"path": select2_field("id_create-h_code")},
                {"path": "//input[contains(@class, 'select2-search__field')]",
                 "extra_action": "setvalue", "value": "H200"},
                {"path": select2_result(1)},
                {"path": "//*[@id='id_create-threshold']",
                 "extra_action": "setvalue", "value": "5", "clear": True},
                {"path": modal_submit_btn("create_obj_modal")},
                {"path": "//*[@id='tableobj']", "presence_only": True,
                 "wait_dt": True},
            ],
            "sga_danger_category",
        )

        # 2. Sustancia peligrosa: mismo patrón, con multiselect por AJAX.
        self.navigate_to_sga("danger_substance")
        self.take_screenshot_list(
            [
                {"path": gt_crud_create_btn("tableobj")},
                {"path": "//*[@id='id_create-name']", "extra_action": "setvalue",
                 "value": "Sustancia peligrosa selenium", "clear": True},
                {"path": "//*[@id='id_create-cas_code']",
                 "extra_action": "setvalue", "value": "67-64-1", "clear": True},
            ]
            # El select2 MÚLTIPLE no expone la caja de búsqueda igual que el
            # simple, y aquí lo que se prueba es el CRUD, no el autocompletado
            # (que ya queda cubierto por el h_code del bloque anterior).
            + self.select2_preset_steps(
                "id_create-h_codes_match", self.hcode.pk, self.hcode.code
            )
            + [
                {"path": modal_submit_btn("create_obj_modal")},
                {"path": "//*[@id='tableobj']", "presence_only": True,
                 "wait_dt": True},
            ],
            "sga_danger_substance",
        )

        # 3. Edición y borrado de la fila recién creada.
        self.take_screenshot_list(
            [
                {"path": datatable_row_icon("tableobj", GT_ICON_UPDATE)},
                {"path": "//*[@id='id_update-name']", "extra_action": "setvalue",
                 "value": "Sustancia peligrosa editada", "clear": True},
                {"path": modal_submit_btn("update_obj_modal")},
                {"path": "//*[@id='tableobj']", "presence_only": True,
                 "wait_dt": True},
                {"path": datatable_row_icon("tableobj", GT_ICON_DELETE)},
                {"path": gt_modal_delete_btn("delete_obj_modal")},
                {"path": "//*[@id='tableobj']", "presence_only": True,
                 "wait_dt": True},
            ],
            "sga_danger_substance",
        )
