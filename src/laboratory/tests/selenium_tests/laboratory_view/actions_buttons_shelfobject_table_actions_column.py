from django.test import tag
from django.utils.timezone import now

from laboratory.tests.selenium_tests.laboratory_view.base import \
    LaboratoryViewSeleniumTest


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
            {"path": "//*[@id='shelfobject_detail_modal_body']",
             "extra_action": "script",
             "value": "$('#shelfobject_detail_modal_body').scrollTop(150);"},
            {"path": "//*[@id='shelfobject_detail_modal_body']",
             "extra_action": "script",
             "value": "$('#shelfobject_detail_modal_body').scrollTop(300);"},
            {"path": "//*[@id='shelfobject_detail_modal_body']",
             "extra_action": "script",
             "value": "$('#shelfobject_detail_modal_body').scrollTop(450);"},
            {"path": "//*[@id='detail_modal_container']/div/div/div[3]/button"}
        ]
        self.create_gif_process(path_list, "view_shelfobject_detail")

    def test_reserve_shelfobject(self):
        initial_date, initial_date_strftime = self.get_format_increase_decrease_date(now(), 1)
        final_date, final_date_strftime = self.get_format_increase_decrease_date(initial_date, 5)

        path_list = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[2]"},
            {"path": "//*[@id='reservesoform']/div/div/input"},
            {"path": "//*[@id='reservesoform']/div/div/input",
             "extra_action": "setvalue", "value": "2"},
            {"path": "//*[@id='reservesoform']/div[2]/div/div/input"},
            {"path": "//*[@data-day='%s']" % initial_date_strftime},
            {"path": "//*[@id='reservesoform']/div[3]/div/div/input"},
            {"path": "//*[@data-day='%s']" % final_date_strftime},
            {"path": self.get_save_button_modal("reservesomodal")}
        ]
        self.create_gif_process(path_list, "reserve_shelfobject")

    def test_increase_shelfobject(self):
        path_list = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[3]"},
            {"path": "//*[@id='increasesoform']/div/div/input"},
            {"path": "//*[@id='increasesoform']/div/div/input",
             "extra_action": "setvalue", "value": "5"},
            {"path": "//*[@id='increasesoform']/div[2]/div/input"},
            {"path": "//*[@id='increasesoform']/div[2]/div/input",
             "extra_action": "setvalue", "value": "R78509"},
            {"path": "//*[@id='increasesoform']/div[3]/div/span/span/span"},
            {"path": "/html/body/span/span/span[2]/ul/li"},
            {"path": self.get_save_button_modal("increasesomodal")},
        ]
        self.create_gif_process(path_list, "increase_shelfobject")

    def test_transfer_out_shelfobject(self):
        path_list = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[4]"},
            {"path": self.get_save_button_modal("reservesomodal")}
        ]
        self.create_gif_process(path_list, "transfer_out_obj_id_modal")

    def test_decrease_shelfobject(self):
        path_list = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[5]"},
            {"path": "//*[@id='decreasesoform']/div/div/input"},
            {"path": "//*[@id='decreasesoform']/div/div/input",
             "extra_action": "setvalue", "value": "3"},
            {"path": "//*[@id='decreasesoform']/div[2]/div/input"},
            {"path": "//*[@id='decreasesoform']/div[2]/div/input",
             "extra_action": "setvalue", "value": "Práctica de laboratorio"},
            {"path": self.get_save_button_modal("decreasesomodal")}
        ]
        self.create_gif_process(path_list, "decrease_shelfobject")

    def test_view_shelfobject_logs(self):
        path_list1 = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[6]"}
        ]
        path_shelfobject_info = ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div/div/div[2]/div/div"
        path_list2 = [
            {"path": path_shelfobject_info, "extra_action": "script", "value": "window.scrollTo(0, 100)"},
            {"path": path_shelfobject_info, "extra_action": "script", "value": "window.scrollTo(0, 200)"},
            {"path": path_shelfobject_info, "extra_action": "script", "value": "window.scrollTo(0, 300)"}
        ]
        general_path_list = [path_list1, path_list2]
        self.create_gif_by_change_focus_tab(general_path_list, ["shelfobjectlog"],"view_shelfobject_logs")

    def test_manage_shelfobject_container(self):
        path_list = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[7]"},
            {"path": self.get_save_button_modal("managecontainermodal")}
        ]
        self.create_gif_process(path_list, "manage_shelfobject_container")

    def test_move_shelfobject(self):
        path_list = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[8]"},
            {"path": self.get_save_button_modal("managecontainermodal")}
        ]
        self.create_gif_process(path_list, "move_shelfobject")

    def test_download_shelfobject_info(self):
        path_list = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[9]"}
        ]
        self.create_gif_process(path_list, "download_shelfobject_info")

    def test_delete_shelfobject(self):
        path_list = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[10]"},
            {"path": self.get_save_button_modal("delete_shelfobject_modal")}
        ]
        self.create_gif_process(path_list, "delete_shelfobject")

    def test_delete_shelfobject_and_its_container(self):
        path_list = self.buttons_actions_path + [
            {"path": "//*[@id='shelfobjecttable']/tbody/tr/td[7]/a[10]"},
            {"path": "//*[@id='divcontainer']/span"},
            {"path": self.get_save_button_modal("delete_shelfobject_modal")}
        ]
        self.create_gif_process(path_list, "delete_shelfobject_and_its_container")
