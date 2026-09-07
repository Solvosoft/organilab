from django.test import tag

from laboratory.tests.selenium_tests.manage_laboratory.base import (
    ManageLaboratorySeleniumBase,
)
from organilab_test.tests.base import modifies_db
from organilab_test.tests.selenium_xpaths import (
    GT_ICON_DELETE,
    GT_ICON_UPDATE,
    datatable_row_icon,
    gt_crud_create_btn,
    gt_modal_delete_btn,
    modal_submit_btn,
)


@tag("selenium")
class LaboratoryCatalogsCrudTest(ManageLaboratorySeleniumBase):
    """CRUD de los catálogos del laboratorio, los tres en un solo flujo.

    `equipmenttype_list`, `instrumentalfamily_list` y `laboratory_process_list`
    comparten la maquinaria ObjectCRUD de gentelella —misma tabla, mismos
    modales `create_obj_modal` / `update_obj_modal` / `delete_obj_modal`—, así
    que probarlas por separado sería arrancar el navegador tres veces para
    ejercitar el mismo JS.

    Lo que NO comparten son los formularios, y conviene no olvidarlo:

      - `EquipmentTypeForm`  -> `name` + `description`
      - `InstrumentalFamilyForm` -> solo `description`
      - `LaboratoryProcessForm`  -> `description` en **TinyMCE** + `laboratory`
        oculto

    Además los tres forms se instancian con `prefix="create"` / `prefix="update"`
    (`laboratory/views/catalogs.py`, `laboratory/views/laboratory.py:896`), así
    que los ids de campo son `id_create-<campo>`, no `id_<campo>`.
    """

    # (ruta, id de tabla, campos del alta, campos de la edición)
    CATALOGOS = (
        (
            "equipmenttype_list",
            "equipmenttype_table",
            {"name": "Tipo selenium", "description": "Creado por selenium"},
        ),
        (
            "instrumentalfamily_list",
            "instrumentalfamily_table",
            {"description": "Familia selenium"},
        ),
        (
            "laboratory_process_list",
            "process_table",
            {"description": "<p>Proceso selenium</p>"},
        ),
    )

    # `description` de LaboratoryProcessForm es un EditorTinymce.
    TINYMCE = {("process_table", "description")}

    @modifies_db
    def test_lab_catalogs_flow(self):
        for urlname, table_id, campos in self.CATALOGOS:
            with self.subTest(catalogo=urlname):
                self.navigate_to_lab(urlname)
                self.take_screenshot_list(
                    self.crud_steps(table_id, campos),
                    "lab_catalog_%s" % table_id,
                )

    # --- Pasos ---

    def fill_steps(self, table_id, prefijo, campos, sufijo=""):
        steps = []
        for campo, valor in campos.items():
            field_id = "id_%s-%s" % (prefijo, campo)
            valor = valor + sufijo if sufijo else valor
            if (table_id, campo) in self.TINYMCE:
                steps += self.tinymce_set_steps(field_id, valor)
            else:
                steps.append(
                    {"path": "//*[@id='%s']" % field_id,
                     "extra_action": "setvalue", "value": valor, "clear": True}
                )
        return steps

    def crud_steps(self, table_id, campos):
        tabla = {"path": "//*[@id='%s']" % table_id, "presence_only": True,
                 "wait_dt": True}
        return (
            [{"path": gt_crud_create_btn(table_id)}]
            + self.fill_steps(table_id, "create", campos)
            + [{"path": modal_submit_btn("create_obj_modal")}, tabla]
            + [{"path": datatable_row_icon(table_id, GT_ICON_UPDATE)}]
            + self.fill_steps(table_id, "update", campos, sufijo=" editado")
            + [{"path": modal_submit_btn("update_obj_modal")}, tabla]
            + [
                {"path": datatable_row_icon(table_id, GT_ICON_DELETE)},
                {"path": gt_modal_delete_btn("delete_obj_modal")},
                tabla,
            ]
        )
