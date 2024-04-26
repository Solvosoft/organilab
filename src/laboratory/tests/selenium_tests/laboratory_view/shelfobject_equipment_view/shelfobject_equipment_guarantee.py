from django.test import tag
from django.utils.timezone import now

from laboratory.tests.selenium_tests.laboratory_view.shelfobject_equipment_view.base import \
    ShelfObjectEquipmentSeleniumTest


@tag('selenium')
class ShelfObjectEquipmentGuarantee(ShelfObjectEquipmentSeleniumTest):

    def setUp(self):
        super().setUp()
        self.init_path= []


    def test_view_shelfobject_guarantee(self):
        initial_date, initial_date_strftime = self.get_format_increase_decrease_date(now(), 1)

        path_list = [
            {"path" :"/html/body/div[1]/div/div[3]/div/div/div[7]/div[1]/h1",
                "scroll":"window.scrollTo(0, document.body.scrollHeight)"},
        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "view_shelfobject_equipment_guarantee")

    def test_add_shelfobject_guarantee(self):
        initial_date, initial_date_strftime = self.get_format_increase_decrease_date(now(), 1)
        final_date, final_date_strftime = self.get_format_increase_decrease_date(now(), 2)

        path_list = [
            {"path" :"/html/body/div[1]/div/div[3]/div/div/div[7]/div[1]/h1",
                "scroll":"window.scrollTo(0, document.body.scrollHeight)"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[7]/div[2]/div/div[1]/div[2]/div/button[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[17]/div/div/div[2]/form/div[1]/div/div/input"},
            {"path": "//*[@data-day='%s']" % initial_date_strftime},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[17]/div/div/div[2]/form/div[2]/div/div/input"},
            {"path": "//*[@data-day='%s']" % final_date_strftime},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[17]/div/div/div[3]/button[2]"},

        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "add_shelfobject_equipment_guarantee")

    def test_edit_shelfobject_guarantee(self):
        initial_date, initial_date_strftime = self.get_format_increase_decrease_date(now(), 1)

        path_list = [
            {"path" :"/html/body/div[1]/div/div[3]/div/div/div[7]/div[1]/h1",
                "scroll":"window.scrollTo(0, document.body.scrollHeight)"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[7]/div[2]/div/div[2]/div/table/tbody/tr/td[5]/div/i[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[18]/div/div/div[2]/form/div[1]/div/div/input"},
            {"path": "//*[@data-day='%s']" % initial_date_strftime},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[18]/div/div/div[3]/button[2]"},

        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "edit_shelfobject_equipment_guarantee")

    def test_delete_shelfobject_guarantee(self):

        path_list = [
            {"path" :"/html/body/div[1]/div/div[3]/div/div/div[7]/div[1]/h1",
                "scroll":"window.scrollTo(0, document.body.scrollHeight)"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[7]/div[2]/div/div[2]/div/table/tbody/tr/td[5]/div/i[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[19]/div/div/div[3]/button[2]"},

        ]
        general_path_list = [self.path_base, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmenteditview"],
                                            "delete_shelfobject_equipment_guarantee")
