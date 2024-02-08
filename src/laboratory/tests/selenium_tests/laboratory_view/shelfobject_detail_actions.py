from django.test import tag

from laboratory.tests.selenium_tests.laboratory_view.actions_buttons_shelfobject_table_actions_column import \
    ButtonsActionsTableColumn


@tag('selenium')
class ButtonsActionsTableColumn(ButtonsActionsTableColumn):

    def setUp(self):
        super().setUp()

        self.path_shelfobject_info = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[6]"}
        ]

    def test_change_shelfobject_status(self):
        path_list = self.path_shelfobject_info + [
            {"path": ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div/div/div[2]/div/div/div/div[2]/a"},
            {"path": "//*[@id='status_form']/div/div/span/span/span"},
            {"path": "/html/body/span/span/span[2]/ul/li"},
            {"path": "//*[@id='status_form']/div[2]/div/textarea"},
            {"path": "//*[@id='status_form']/div[2]/div/textarea",
             "extra_action": "setvalue", "value": "Reactivo esta siendo utilizado en la práctica de laboratorio"},
            {"path": "//*[@id='status_modal']/div/div/div[3]/button[2]"}
        ]
        self.create_gif_process(path_list, "change_shelfobject_status")
