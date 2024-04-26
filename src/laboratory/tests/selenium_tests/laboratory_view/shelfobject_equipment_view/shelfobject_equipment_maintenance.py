from django.test import tag
from django.utils.timezone import now

from laboratory.tests.selenium_tests.laboratory_view.shelfobject_equipment_view.base import \
    ShelfObjectEquipmentSeleniumTest


@tag('selenium')
class ShelfObjectEquipmentMaintenance(ShelfObjectEquipmentSeleniumTest):

    def setUp(self):
        super().setUp()
        self.init_path= []


    def test_view_shelfobject_maintanence(self):
        initial_date, initial_date_strftime = self.get_format_increase_decrease_date(now(), 1)

        path_list = [
            {"path" :"/html/body/div[1]/div/div[3]/div/div/div[4]",
                "scroll":"window.scrollTo(0, 1400)"},
        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "view_shelfobject_equipment_maintenance")

    def test_add_shelfobject_maintanence(self):
        initial_date, initial_date_strftime = self.get_format_increase_decrease_date(now(), 1)

        path_list = [
            {"path" :"/html/body/div[1]/div/div[3]/div/div/div[4]",
                "scroll":"window.scrollTo(0, 1400)"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[5]/div[2]/div/div[1]/div[2]/div/button[2]/span/i"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[8]/div/div/div[2]/form/div[1]/div/div/input"},
            {"path": "//*[@data-day='%s']" % initial_date_strftime},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[8]/div/div/div[2]/form/div[2]/div/span"},
            {"path": "/html/body/span/span/span[2]/ul/li[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[8]/div/div/div[2]/form/div[3]/div/textarea"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[8]/div/div/div[2]/form/div[3]/div/textarea", "setvalue": "Repair the equipment"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[8]/div/div/div[3]/button[2]"},

        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "add_shelfobject_equipment_maintenance")

    def test_edit_shelfobject_maintanence(self):

        path_list = [
            {"path" :"/html/body/div[1]/div/div[3]/div/div/div[4]",
                "scroll":"window.scrollTo(0, 1400)"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[5]/div[2]/div/div[2]/div/table/tbody/tr/td[5]/div/i[1]"},
            {"path": "//*[@id='update_maintenance_form']/div[3]/div/textarea", "extra_action":"clearinput"},
            {"path": "//*[@id='update_maintenance_form']/div[3]/div/textarea", "extra_action":"setvalue", "value":"Update the equipment"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[9]/div/div/div[3]/button[2]"},

        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "edit_shelfobject_equipment_maintenance")

    def test_delete_shelfobject_maintanence(self):

        path_list = [
            {"path" :"/html/body/div[1]/div/div[3]/div/div/div[4]",
                "scroll":"window.scrollTo(0, 1400)"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[5]/div[2]/div/div[2]/div/table/tbody/tr/td[5]/div/i[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[10]/div/div/div[3]/button[2]"},

        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "delete_shelfobject_equipment_maintenance")
