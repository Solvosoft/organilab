from django.test import tag

from laboratory.tests.selenium_tests.laboratory_view.base import LaboratoryViewSeleniumTest


@tag('selenium')
class CreateShelfObject(LaboratoryViewSeleniumTest):

    def get_save_button_modal(self, id_modal):
        return "//*[@id='%s']/div/div/div[3]/button[2]" % id_modal

    def create_reactive(self, row_ins_position, select_container_position,
                        container_type, ins_position=""):
        path_list = self.create_shelfobject_reative_start + [
            {"path": "//*[@id='reactive_form']/div[%d]/div/div/div%s/ins" %
                     (row_ins_position, ins_position)},
            {"path": "//*[@id='reactive_form']/div[%d]/div/span/span/span" % select_container_position},
        ] + self.create_shelfobject_reative_end + [
            {"path": self.get_save_button_modal("reactive_modal")}
        ]

        self.create_gif_process(path_list, "create_shelfobject_reactive_with_%s_container" % container_type)

    def test_create_shelfobject_reactive_with_clone_container(self):
        self.create_reactive(5, 6, "clone")

    def test_create_shelfobject_reactive_with_use_selected_container(self):
        self.create_reactive(5, 7, "use_selected",
                             ins_position="[2]")

    def test_create_shelfobject_material(self):
        path_list = self.path_base + [
            {"path": "//*[@id='labroom_1']"},
            {"path": "//*[@id='furniture_2']"},
            {"path": "//*[@id='shelf_3']"},
            {"path": "//*[@id='shelfobjecttable_wrapper']/div/div[2]/div/button[2]",
             "scroll": "window.scrollTo(0, 250)"},
            {"path": "//*[@id='material_form']/div/div/span/span/span"},
            {"path": "//*[@id='material_form']/span/span/span[2]/ul/li"},
            {"path": "//*[@id='material_form']/div[2]/div/span/span/span"},
            {"path": "//*[@id='material_form']/span/span/span[2]/ul/li"},
            {"path": "//*[@id='material_form']/div[3]/div/input"},
            {"path": "//*[@id='material_form']/div[3]/div/input",
             "extra_action": "setvalue", "value": "4"},
            {"path": "//*[@id='material_form']/div[5]/div/textarea"},
            {"path": "//*[@id='material_form']/div[5]/div/textarea",
             "extra_action": "setvalue", "value": "Contenedor de base cilíndrica para "
                                                  "líquidos con capacidad de 1L."},
            {"path": self.get_save_button_modal("material_modal")}
        ]
        self.create_gif_process(path_list, "create_shelfobject_material")

    def test_create_shelfobject_equipment(self):
        path_list = self.path_base + [
            {"path": "//*[@id='labroom_1']"},
            {"path": "//*[@id='furniture_1']"},
            {"path": "//*[@id='shelf_1']"},
            {"path": "//*[@id='shelfobjecttable_wrapper']/div/div[2]/div/button",
             "scroll": "window.scrollTo(0, 250)"},
            {"path": "//*[@id='select2-id_ef-object-container']"},
            {"path": "//*[@id='equipment_form']/span/span/span[2]/ul/li"},
            {"path": "//*[@id='select2-id_ef-status-container']"},
            {"path": "//*[@id='equipment_form']/span/span/span[2]/ul/li"},
            {"path": "//*[@id='equipment_form']/div[3]/div/input"},
            {"path": "//*[@id='equipment_form']/div[3]/div/input",
             "extra_action": "setvalue", "value": "2"},
            {"path": "//*[@id='equipment_form']/div[5]/div/textarea",
             "scroll": "$('#equipment_modal').scrollTop(300);"},
            {"path": "//*[@id='equipment_form']/div[5]/div/textarea",
             "extra_action": "setvalue", "value": "Instrumento para calcular la masa de un objeto."},
            {"path": self.get_save_button_modal("equipment_modal")}
        ]
        self.create_gif_process(path_list, "create_shelfobject_equipment")
