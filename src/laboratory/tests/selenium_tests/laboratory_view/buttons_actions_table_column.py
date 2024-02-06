from django.test import tag

from laboratory.tests.selenium_tests.laboratory_view.base import LaboratoryViewSeleniumTest


@tag('selenium')
class ButtonsActionsTableColumn(LaboratoryViewSeleniumTest):

    def setUp(self):
        super().setUp()

        self.buttons_actions_path = self.path_base + [
            {"path": "//*[@id='labroom_2']"},
            {"path": "//*[@id='furniture_3']"},
            {"path": "//*[@id='shelf_2']", "scroll": "window.scrollTo(0, 250)"}
        ]

    def test_view_shelfobject_detail(self):
        path_list = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a"},
            {"path": "//*[@id='detail_modal_container']/div/div/div[2]/div[2]/div/a"},
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a",
             "extra_action": "script", "value": "$('#detail_modal_container').scrollTop(200);"},
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a",
             "extra_action": "script",
             "value": "$('#detail_modal_container').scrollTop(400);"},
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a",
             "extra_action": "script",
             "value": "$('#detail_modal_container').scrollTop(600);"},
            {"path": "//*[@id='detail_modal_container']/div/div/div[3]/button"}
        ]
        self.create_gif_process(path_list, "view_shelfobject_detail")

    def test_reserve_shelfobject(self):
        path_list = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[2]"}
        ]
        self.create_gif_process(path_list, "reserve_shelfobject")

    def test_increase_shelfobject(self):
        path_list = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[3]"}
        ]
        self.create_gif_process(path_list, "increase_shelfobject")

    def test_transfer_out_shelfobject(self):
        path_list = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[4]"}
        ]
        self.create_gif_process(path_list, "transfer_out_shelfobject")

    def test_decrease_shelfobject(self):
        path_list = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[5]"}
        ]
        self.create_gif_process(path_list, "decrease_shelfobject")

    def test_view_shelfobject_logs(self):
        path_list = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[6]"}
        ]
        self.create_gif_process(path_list, "view_shelfobject_logs")

    def test_manage_shelfobject_container(self):
        path_list = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[7]"}
        ]
        self.create_gif_process(path_list, "manage_shelfobject_container")

    def test_move_shelfobject(self):
        path_list = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[8]"}
        ]
        self.create_gif_process(path_list, "move_shelfobject")
