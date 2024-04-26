from django.test import tag

from laboratory.tests.selenium_tests.laboratory_view.shelfobject_equipment_view.base import \
    ShelfObjectEquipmentSeleniumTest

@tag('selenium')
class TableLogs(ShelfObjectEquipmentSeleniumTest):

    def setUp(self):
        super().setUp()

    def test_create_shelfobject_equipment_log(self):
        path_list = [
            {"path": "//*[@id='log_table_wrapper']"},
            {"path": "//*[@id='log_table_wrapper']/div/div[2]/div/button[2]", "scroll": "window.scrollTo(0, 300)"},
            {"path": "//*[@id='create_log_form']/div/div/textarea"},
            {"path": "//*[@id='create_log_form']/div/div/textarea", "extra_action": "setvalue",
             "value": "La balanza fue utilizada por el grupo 03 de estudiantes en la capacitación del I semestre 2024."},
            {"path": "//*[@id='create_log_modal']/div/div/div[3]/button[2]"}

        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "create_shelfobject_equipment_log")

    def test_edit_shelfobject_equipment_log(self):
        path_list = [
            {"path": "//*[@id='log_table_wrapper']"},
            {"path": "//*[@id='log_table']/tbody/tr/td[4]/div/i",
             "scroll": "window.scrollTo(0, 300)"},
            {"path": "//*[@id='update_log_form']/div/div/textarea"},
            {"path": "//*[@id='update_log_form']/div/div/textarea",
             "extra_action": "move_cursor_end"},
            {"path": "//*[@id='update_log_form']/div/div/textarea", "extra_action":
                "setvalue", "value": " ID Encargado AL342."},
            {"path": "//*[@id='update_log_modal']/div/div/div[3]/button[2]"}

        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "edit_shelfobject_equipment_log")

    def test_delete_shelfobject_equipment_log(self):
        path_list = [
            {"path": "//*[@id='log_table_wrapper']"},
            {"path": "//*[@id='log_table']/tbody/tr[2]/td[4]/div/i[2]",
             "scroll": "window.scrollTo(0, 300)"},
            {"path": "//*[@id='delete_log_modal']/div/div/div[3]/button[2]"}

        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "delete_shelfobject_equipment_log")
