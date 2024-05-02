from django.test import tag

from laboratory.tests.selenium_tests.laboratory_view.shelfobject_equipment_view.base import \
    ShelfObjectEquipmentSeleniumTest

@tag('selenium')
class TableCalibrations(ShelfObjectEquipmentSeleniumTest):

    def setUp(self):
        super().setUp()

    def test_create_shelfobject_equipment_calibration(self):
        path_list = [
            {"path": "//*[@id='calibrate_table_wrapper']/div/div[2]/div/button[2]",
             "scroll": "window.scrollTo(0, 900)"},
            {"path": "//*[@id='id_create_calibrate-calibrate_name']"},
            {"path": "//*[@id='id_create_calibrate-calibrate_name']", "extra_action":
                "setvalue", "value": "Luz Barrantes Torres"},
            {"path": "//*[@id='id_create_calibrate-calibration_date']"},
            {"path": "//*[@id='create_calibrate_form']/div[3]/span/label"},
            {"path": "//*[@id='id_create_calibrate-observation']"},
            {"path": "//*[@id='id_create_calibrate-observation']", "extra_action":
                "setvalue", "value": "Calibración del equipo."},
            {"path": "//*[@id='create_calibrate_modal']/div/div/div[3]/button[2]"}

        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "create_shelfobject_equipment_calibration")

    def test_edit_shelfobject_equipment_calibration(self):
        path_list = [
            {"path": "//*[@id='calibrate_table']/tbody/tr/td[5]/div/i",
             "scroll": "window.scrollTo(0, 900)"},
            {"path": "//*[@id='id_update_calibrate-calibrate_name']",
             "extra_action": "move_cursor_end"},
            {"path": "//*[@id='id_update_calibrate-calibrate_name']",
             "extra_action": "setvalue", "value": " Torres"},
            {"path": "//*[@id='id_update_calibrate-observation']",
             "extra_action": "move_cursor_end"},
            {"path": "//*[@id='id_update_calibrate-observation']",
             "extra_action": "setvalue",
             "value": " El técnico configuró el equipo."},
            {"path": "//*[@id='update_calibrate_modal']/div/div/div[3]/button[2]"}

        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "edit_shelfobject_equipment_calibration")

    def test_delete_shelfobject_equipment_calibration(self):
        path_list = [
            {"path": "//*[@id='calibrate_table']/tbody/tr[2]/td[5]/div/i[2]",
             "scroll": "window.scrollTo(0, 900)"},
            {"path": "//*[@id='delete_calibrate_modal']/div/div/div[3]/button[2]"}

        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "delete_shelfobject_equipment_calibration")
