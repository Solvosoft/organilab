from django.test import tag
from django.utils.timezone import now

from laboratory.tests.selenium_tests.laboratory_view.shelfobject_equipment_view.base import \
    ShelfObjectEquipmentSeleniumTest


@tag('selenium')
class ShelfObjectEquipmentTraining(ShelfObjectEquipmentSeleniumTest):

    def setUp(self):
        super().setUp()
        self.init_path= []


    def test_view_shelfobject_training(self):

        path_list = [
            {"path" :"/html/body/div[1]/div/div[3]/div/div/div[6]/div[1]/h1",
                "scroll":"window.scrollTo(0, 2000)"},
        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "view_shelfobject_equipment_training")

    def test_add_shelfobject_training(self):
        initial_date, initial_date_strftime = self.get_format_increase_decrease_date(now(), 0)
        final_date, final_date_strftime = self.get_format_increase_decrease_date(now(), 1)

        path_list = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[6]/div[1]/h1",
             "scroll": "window.scrollTo(0, 2000)"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[6]/div[2]/div/div[1]/div[2]/div/button[3]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[20]/div/div/div[2]/form/div[1]/div/div/input"},
            {"path": "//*[@data-day='%s']" % initial_date_strftime},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[20]/div/div/div[2]/form/div[2]/div/div/input"},
            {"path": "//*[@data-day='%s']" % final_date_strftime},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[20]/div/div/div[2]/form/div[3]/div/input", "extra_action":"setvalue",
             "value": 1},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[20]/div/div/div[2]/form/div[4]/div/span"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[20]/div/div/div[2]/form/span/span/span/ul/li[1]"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[20]/div/div/div[2]/form/div[5]/div/textarea",
                "extra_action": "setvalue",
                "value": "Luz Castro Lopez"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[20]/div/div/div[2]/form/div[6]/div/textarea",
                "extra_action": "setvalue",
                "value": "Llegar temprano"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[20]/div/div/div[2]/form/div[7]/div/input",
                "extra_action": "setvalue",
                "value": "Oficinas Centrales"},

            {"path": "/html/body/div[1]/div/div[3]/div/div/div[20]/div/div/div[3]/button[2]"},

        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "add_shelfobject_equipment_training")

    def test_edit_shelfobject_training(self):
        initial_date, initial_date_strftime = self.get_format_increase_decrease_date(now(), 1)

        path_list = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[6]/div[1]/h1",
             "scroll": "window.scrollTo(0, 2000)"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[6]/div[2]/div/div[2]/div/table/tbody/tr/td[7]/div/i[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[21]/div/div/div[2]/form/div[2]/div/div/input"},
            {"path": "//*[@data-day='%s']" % initial_date_strftime},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[21]/div/div/div[2]/form/div[4]/div/span/span[1]/span/ul/li[1]/button"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[21]/div/div/div[3]/button[2]", "scroll": "$('#update_training_modal').scrollTop(500);"},

        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "edit_shelfobject_equipment_training")

    def test_delete_shelfobject_training(self):

        path_list = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[6]/div[1]/h1",
             "scroll": "window.scrollTo(0, 2000)"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[6]/div[2]/div/div[2]/div/table/tbody/tr/td[7]/div/i[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[22]/div/div/div[3]/button[2]"},

        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "delete_shelfobject_equipment_training")
