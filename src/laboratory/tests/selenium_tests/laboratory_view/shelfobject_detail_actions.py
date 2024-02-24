from django.test import tag
from django.utils.timezone import now

from laboratory.tests.selenium_tests.laboratory_view.actions_buttons_shelfobject_table_actions_column import \
    ButtonsActionsTableColumnBase


@tag('selenium')
class ShelfObjectInfoButtonsActions(ButtonsActionsTableColumnBase):

    def setUp(self):
        super().setUp()

        self.path_shelfobject_info = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[6]"}
        ]

    def test_change_shelfobject_status(self):
        path_list = [
            {"path": "//*[@data-modalid='status_modal']"},
            {"path": "//*[@id='status_form']/div/div/span[2]/a"},
            {"path": "/html/body/div[4]/div/div[2]/input[1]"},
            {"path": "/html/body/div[4]/div/div[2]/input[1]",
             "extra_action": "setvalue", "value": "En uso"},
            {"path": "/html/body/div[4]/div/div[3]/button"},
            {"path": "//*[@id='status_form']/div/div/span/span/span"},
            {"path": "/html/body/span/span/span[2]/ul/li[2]"},
            {"path": "//*[@id='status_form']/div[2]/div/textarea"},
            {"path": "//*[@id='status_form']/div[2]/div/textarea",
             "extra_action": "setvalue", "value": "Reactivo esta siendo utilizado en la práctica de laboratorio"},
            {"path": "//*[@id='status_modal']/div/div/div[3]/button[2]"},
            {"path": "//*[@id='observationTable']",
             "extra_action": "script", "value": "window.scrollTo(0, 300)"},
            {"path": "//*[@id='observationTable']/tbody/tr/td[4]"}
        ]

        general_path_list = [self.path_shelfobject_info, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["shelfobjectlog"],
                                            "change_shelfobject_status")

    def test_add_shelfobject_observation(self):
        current_date, str_date = self.get_format_increase_decrease_date(now(), 0)
        path_list = self.scroll_shelfobject_info + [
            {"path": "//*[@data-modalid='observation_modal']"},
            {"path": "//*[@id='observation_form']/div[2]/div/textarea"},
            {"path": "//*[@id='observation_form']/div[2]/div/textarea",
             "extra_action": "setvalue", "value": "Reactivo fue entregado al responsable"
            " con ID 23548 el día %s, para uso de las prácticas con estudiantes." % str_date},
            {"path": "//*[@id='observation_modal']/div/div/div[3]/button[2]"}
        ]

        general_path_list = [self.path_shelfobject_info, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["shelfobjectlog"],
                                            "add_shelfobject_observation")
