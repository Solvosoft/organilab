from django.test import tag

from laboratory.tests.selenium_tests.laboratory_view.shelfobject_equipment_view.base import \
    ShelfObjectEquipmentSeleniumTest

@tag('selenium')
class TableLogs(ShelfObjectEquipmentSeleniumTest):

    def setUp(self):
        super().setUp()

    def get_general_path_list(self, path_list):
        path_list = [{"path": "//*[@id='log_table_wrapper']"}] + path_list
        return [self.path_base, path_list]

    def test_create_shelfobject_equipment_log(self):
        path_list = [
            {"path": "//*[@id='log_table_wrapper']/div/div[2]/div/button[2]", "scroll": "window.scrollTo(0, 300)"},
            {"path": "//*[@id='create_log_form']/div/div/textarea"},
            {"path": "//*[@id='create_log_form']/div/div/textarea", "extra_action": "setvalue",
             "value": "La balanza fue utilizada por el grupo 03 de estudiantes en la capacitación del I semestre 2024."},
            {"path": "//*[@id='create_log_modal']/div/div/div[3]/button[2]"}
        ]
        self.create_gif_by_change_focus_tab(self.get_general_path_list(path_list),
                                            ["equipmenteditview"],
                                            "create_shelfobject_equipment_log")

    def test_edit_shelfobject_equipment_log(self):
        path_list = [
            {"path": "//*[@id='log_table']/tbody/tr/td[4]/div/i",
             "scroll": "window.scrollTo(0, 300)"},
            {"path": "//*[@id='update_log_form']/div/div/textarea"},
            {"path": "//*[@id='update_log_form']/div/div/textarea",
             "extra_action": "move_cursor_end"},
            {"path": "//*[@id='update_log_form']/div/div/textarea", "extra_action":
                "setvalue", "value": " ID Encargado AL342."},
            {"path": "//*[@id='update_log_modal']/div/div/div[3]/button[2]"}
        ]
        self.create_gif_by_change_focus_tab(self.get_general_path_list(path_list),
                                            ["equipmenteditview"],
                                            "edit_shelfobject_equipment_log")

    def test_delete_shelfobject_equipment_log(self):
        path_list = [
            {"path": "//*[@id='log_table']/tbody/tr[2]/td[4]/div/i[2]",
             "scroll": "window.scrollTo(0, 300)"},
            {"path": "//*[@id='delete_log_modal']/div/div/div[3]/button[2]"}
        ]
        self.create_gif_by_change_focus_tab(self.get_general_path_list(path_list),
                                            ["equipmenteditview"],
                                            "delete_shelfobject_equipment_log")

    def test_view_shelfobject_equipment_logs(self):
        path_list = [
            {"path": "//*[@id='log_table_wrapper']",
             "scroll": "window.scrollTo(0, 300)"}
        ]
        self.create_gif_by_change_focus_tab(self.get_general_path_list(path_list),
                                            ["equipmenteditview"],
                                            "view_shelfobject_equipment_logs")

    def test_search_shelfobject_equipment_logs(self):
        path_list = [
            {"path": "//*[@id='log_table_wrapper']",
             "scroll": "window.scrollTo(0, 300)"},
            {"path": "//*[@id='log_table_wrapper']/div/div/div/label/input"},
            {"path": "//*[@id='log_table_wrapper']/div/div/div/label/input",
             "extra_action": "setvalue", "value": "administrador"},
            {"path": "//*[@id='log_table_wrapper']/div/div/div/label/input"},
            {"path": "//*[@id='log_table_wrapper']/div/div/div/label/input",
             "extra_action": "clearinput"},
            {"path": "//*[@id='log_table_wrapper']/div/div/div/label/input",
             "extra_action": "setvalue", "value": "balanza"},
            {"path": "//*[@id='log_table_wrapper']/div/div[2]/div/button"},
            {"path": "//*[@id='log_table']/thead/tr[2]/th[3]/span/span/span"},
            {"path": "/html/body/span/span/span[2]/ul/li[2]"},
            {"path": "//*[@id='log_table_wrapper']/div/div[2]/div/button"},
            {"path": "//*[@id='log_table']/thead/tr[2]/th[4]/input"},
            {"path": "//*[@id='log_table']/thead/tr[2]/th[4]/input",
             "extra_action": "setvalue", "value": "requiere"},
        ]
        self.create_gif_by_change_focus_tab(self.get_general_path_list(path_list),
                                            ["equipmenteditview"],
                                            "search_shelfobject_equipment_logs")
