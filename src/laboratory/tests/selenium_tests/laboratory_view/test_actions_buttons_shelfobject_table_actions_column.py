from django.test import tag
from organilab_test.tests.selenium_xpaths import select2_result
from django.utils.timezone import now

from laboratory.tests.selenium_tests.laboratory_view.base import (
    LaboratoryViewSeleniumTest,
)


class ButtonsActionsTableColumnBase(LaboratoryViewSeleniumTest):
    def setUp(self):
        super().setUp()

        self.buttons_actions_path = self.path_base + [
            {"path": "//*[@id='labroom_2']"},
            {"path": "//*[@id='furniture_3']"},
            {"path": "//*[@id='shelf_2']", "scroll": "window.scrollTo(0, 250)"},
        ]

        self.path_shelfobject_info = ".//div[@class='right_col']/div[@class='card']/div[@class='card-body']/div[@class='row']/div/div/div[2]/div/div"

        self.scroll_shelfobject_info = [
            {
                "path": self.path_shelfobject_info,
                "extra_action": "script",
                "value": "window.scrollTo(0, 100)",
            },
            {
                "path": self.path_shelfobject_info,
                "extra_action": "script",
                "value": "window.scrollTo(0, 200)",
            },
            {
                "path": self.path_shelfobject_info,
                "extra_action": "script",
                "value": "window.scrollTo(0, 300)",
            },
        ]


@tag("selenium")
class ButtonsActionsTableColumn(ButtonsActionsTableColumnBase):

    def setUp(self):
        super().setUp()

        self.move_shelfobject_form_path = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-arrows"), "sleep": 10},
            {
                "path": "//*[@id='movesocontainerform']/div/div/span/span/span",
                "scroll": "$('#movesocontainermodal').scrollTop(150);",
            },
            {"path": select2_result(1)},
            {"path": "//*[@id='movesocontainerform']/div[2]/div/span/span/span"},
            {"path": select2_result(1)},
            {"path": "//*[@id='movesocontainerform']/div[3]/div/span/span/span"},
            {"path": select2_result(1)},
        ]

    def test_view_shelfobject_detail(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-eye")},
            {
                "path": "//*[@id='shelfobject_detail_modal_body']",
                "extra_action": "script",
                "value": "$('#shelfobject_detail_modal_body').scrollTop(150);",
            },
            {
                "path": "//*[@id='shelfobject_detail_modal_body']",
                "extra_action": "script",
                "value": "$('#shelfobject_detail_modal_body').scrollTop(300);",
            },
            {
                "path": "//*[@id='shelfobject_detail_modal_body']",
                "extra_action": "script",
                "value": "$('#shelfobject_detail_modal_body').scrollTop(450);",
            },
            {"path": "//*[@id='detail_modal_container']/div/div/div[3]/button"},
        ]
        self.create_gif_process(path_list, "view_shelfobject_detail")

    def test_reserve_shelfobject(self):
        initial_date, initial_date_strftime = self.get_format_increase_decrease_date(
            now(), 2
        )
        final_date, final_date_strftime = self.get_format_increase_decrease_date(
            initial_date, 5
        )

        path_list = self.buttons_actions_path + [
            {
                "path": self.shelfobject_row_action("fa-shopping-basket")},
            {"path": "//*[@id='reservesoform']/div/div/input"},
            {
                "path": "//*[@id='reservesoform']/div/div/input",
                "extra_action": "setvalue",
                "value": "2",
            },
            {"path": "//*[@id='reservesoform']/div[2]/div/div/input", "sleep": 1},
            {"path": "//*[@data-day='%s']" % initial_date_strftime, "sleep": 1},
            {"path": "//*[@id='reservesomodal']//h4 | //*[@id='reservesomodal']//h5", "sleep": 1},
            {"path": "//*[@id='reservesoform']/div[3]/div/div/input"},
            {"path": "//*[@data-day='%s']" % final_date_strftime, "sleep": 1},
            {"path": "//*[@id='reservesomodal']//h4 | //*[@id='reservesomodal']//h5", "sleep": 1},
            {"path": self.get_save_button_modal("reservesomodal"), "sleep": 5},
        ]
        self.create_gif_process(path_list, "reserve_shelfobject")

    def test_increase_shelfobject(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-plus")},
            {"path": "//*[@id='id_increase-amount']"},
            {
                "path": "//*[@id='id_increase-amount']",
                "extra_action": "setvalue",
                "value": "5",
            },
            {"path": "//*[@id='id_increase-bill']"},
            {
                "path": "//*[@id='id_increase-bill']",
                "extra_action": "setvalue",
                "value": "R78509",
            },
            {"path": "//span[@aria-controls='select2-id_increase-measurement_unit-container']"},
            {"path": select2_result(1), "sleep": 1},
            {"path": self.get_save_button_modal("increasesomodal")},
        ]
        self.create_gif_process(path_list, "increase_shelfobject")

    def test_transfer_out_shelfobject(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-window-restore")},
            {"path": "//*[@id='id_amount_to_transfer']"},
            {
                "path": "//*[@id='id_amount_to_transfer']",
                "extra_action": "setvalue",
                "value": "2",
            },
            {"path": "//*[@id='transfer_out_form']/div[2]/div/span/span/span"},
            {"path": select2_result(2)},
            {"path": self.get_save_button_modal("transfer_out_obj_id_modal")},
        ]
        self.create_gif_process(path_list, "transfer_out_shelfobject")

    def test_transfer_out_shelfobject_refuse(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-window-restore")},
            {"path": "//*[@id='id_amount_to_transfer']"},
            {
                "path": "//*[@id='id_amount_to_transfer']",
                "extra_action": "setvalue",
                "value": "2",
            },
            {"path": "//*[@id='transfer_out_form']/div[2]/div/span/span/span"},
            {"path": select2_result(2)},
            {
                "path": "//*[@id='transfer_out_form']//input[@name='mark_as_discard']",
                "extra_action": "script",
                "value": "$('#transfer_out_form input[name=mark_as_discard]')"
                         ".prop('checked', true).trigger('change')",
            },
            {"path": self.get_save_button_modal("transfer_out_obj_id_modal")},
        ]
        self.create_gif_process(path_list, "transfer_out_shelfobject_refuse")

    def test_decrease_shelfobject(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-minus")},
            {"path": "//*[@id='id_decrease-amount']"},
            {
                "path": "//*[@id='id_decrease-amount']",
                "extra_action": "setvalue",
                "value": "3",
            },
            {"path": "//*[@id='id_decrease-description']"},
            {
                "path": "//*[@id='id_decrease-description']",
                "extra_action": "setvalue",
                "value": "Práctica de laboratorio",
            },
            {"path": self.get_save_button_modal("decreasesomodal")},
        ]
        self.create_gif_process(path_list, "decrease_shelfobject")

    def test_view_shelfobject_logs(self):
        path_list1 = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-file-text-o")}
        ]
        general_path_list = [path_list1, self.scroll_shelfobject_info]
        self.create_gif_by_change_focus_tab(
            general_path_list, ["shelfobjectlog"], "view_shelfobject_logs"
        )

    def test_manage_shelfobject_container_clone(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-hourglass-end")},
            {"path": self.container_radio("manageconteinerform", "clone")},
            {"path": "//*[@id='manageconteinerform']/div[2]/div/span/span/span"},
            {"path": select2_result(1)},
            {"path": self.get_save_button_modal("managecontainermodal")},
        ]
        self.create_gif_process(path_list, "manage_shelfobject_container_clone")

    def test_manage_shelfobject_container_available(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-hourglass-end")},
            {"path": self.container_radio("manageconteinerform", "available")},
            {"path": "//*[@id='manageconteinerform']/div[3]/div/span/span/span"},
            {"path": select2_result(2)},
            {"path": self.get_save_button_modal("managecontainermodal")},
        ]
        self.create_gif_process(path_list, "manage_shelfobject_container_available")

    def test_move_shelfobject_with_clone_container(self):
        path_list = self.move_shelfobject_form_path + [
            {"path": self.container_radio("movesocontainerform", "clone")},
            {
                "path": self.container_radio("movesocontainerform", "clone"),
                "extra_action": "script",
                "value": "$('#movesocontainermodal').scrollTop(300);",
            },
            {"path": "//*[@id='movesocontainerform']/div[6]/div/span/span/span"},
            {"path": select2_result(1)},
            {"path": self.get_save_button_modal("movesocontainermodal")},
        ]
        self.create_gif_process(path_list, "move_shelfobject_with_clone_container")

    def test_move_shelfobject_with_available_container(self):
        path_list = self.move_shelfobject_form_path + [
            {"path": self.container_radio("movesocontainerform", "available")},
            {
                "path": self.container_radio("movesocontainerform", "available"),
                "extra_action": "script",
                "value": "$('#movesocontainermodal').scrollTop(300);",
            },
            {"path": "//*[@id='movesocontainerform']/div[7]/div/span/span/span"},
            {"path": select2_result(1)},
            {"path": self.get_save_button_modal("movesocontainermodal")},
        ]
        self.create_gif_process(path_list, "move_shelfobject_with_available_container")

    def test_move_shelfobject_with_use_source_container(self):
        path_list = self.move_shelfobject_form_path + [
            {"path": self.container_radio("movesocontainerform", "use_source")},
            {
                "path": self.container_radio("movesocontainerform", "use_source"),
                "extra_action": "script",
                "value": "$('#movesocontainermodal').scrollTop(300);",
            },
            {"path": self.get_save_button_modal("movesocontainermodal")},
        ]
        self.create_gif_process(path_list, "move_shelfobject_with_use_source_container")

    def test_move_shelfobject_with_new_based_source_container(self):
        path_list = self.move_shelfobject_form_path + [
            {"path": self.container_radio("movesocontainerform", "new_based_source")},
            {
                "path": self.container_radio("movesocontainerform", "new_based_source"),
                "extra_action": "script",
                "value": "$('#movesocontainermodal').scrollTop(300);",
            },
            {"path": self.get_save_button_modal("movesocontainermodal")},
        ]
        self.create_gif_process(
            path_list, "move_shelfobject_with_new_based_source_container"
        )

    def test_download_shelfobject_info(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-download")}
        ]
        self.create_gif_process(path_list, "download_shelfobject_info")

    def test_delete_shelfobject(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-close")},
            {"path": self.get_save_button_modal("delete_shelfobject_modal")},
        ]
        self.create_gif_process(path_list, "delete_shelfobject")

    def test_delete_shelfobject_and_its_container(self):
        path_list = self.buttons_actions_path + [
            {"path": self.shelfobject_row_action("fa-close")},
            {
                "path": "//*[@id='id_delete_container']",
                "extra_action": "script",
                "value": "$('#id_delete_container')"
                         ".prop('checked', true).trigger('change')",
            },
            {"path": self.get_save_button_modal("delete_shelfobject_modal")},
        ]
        self.create_gif_process(path_list, "delete_shelfobject_and_its_container")
