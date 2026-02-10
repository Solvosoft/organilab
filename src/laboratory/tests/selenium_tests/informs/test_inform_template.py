from django.contrib.auth.models import User
from django.test import tag
from organilab_test.tests.base import SeleniumBase


@tag("selenium")
class InformsSeleniumTest(SeleniumBase):
    fixtures = ["selenium/laboratory_selenium.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )
        self.path_base = [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div/div/span/span[1]/span"
            },
            {"path": "/html/body/span/span/span/ul/li[1]"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div/div/div/a[1]"
            },
            {"path": "/html/body/div[1]/div/div[1]/div/div[4]/div/ul/li[6]"},
            {
                "path": "/html/body/div[1]/div/div[1]/div/div[4]/div/ul/li[6]/ul/li[2]/a",
                "scroll": "window.scrollTo(0, 200)",
            },
        ]

    def test_view_informs(self):

        path_list = self.path_base
        self.create_gif_process(path_list, "view_inform_templates")

    def test_create_inform_template(self):

        path_list = self.path_base + [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div/button"},
            {
                "path": "/html/body/div[3]/div/div[2]/input[1]",
                "extra_action": "clearinput",
            },
            {
                "path": "/html/body/div[3]/div/div[2]/input[1]",
                "extra_action": "setvalue",
                "value": "Primer Formulario",
            },
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
            {"path": "//*[@id='form_name']"},
        ]
        self.create_gif_process(path_list, "add_inform_template")

    def test_update_name_inform_template(self):

        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[2]"
            },
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/a"},
            {"path": "/html/body/div[3]/div/div[2]/input[1]"},
            {
                "path": "/html/body/div[3]/div/div[2]/input[1]",
                "extra_action": "setvalue",
                "value": "Formulario Prueba",
            },
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
        ]
        self.create_gif_process(path_list, "update_name_inform_template")

    # def test_drag_drop(self):
    #
    #     path_list = self.path_base+[
    #         {"path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[2]"},
    #         {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[2]/div/span[1]",
    #          "extra_action": "drag_and_drop", "x":"/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[2]/div/span[1]",
    #          "y":"/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[2]/div"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/input", "extra_action": "clearinput"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/input",
    #          "extra_action": "setvalue", "value": "Nombre"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div[5]/div[1]/input", "extra_action": "clearinput"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div[5]/div[1]/input",
    #          "extra_action": "setvalue", "value": "Ingrese el nombre"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[2]/div[2]/button[1]"},
    #         {"path": "//*[@id='save_btn']"},
    #         {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/button", "scroll":"window.scrollTo(0, 600)"},
    #         {"path": "/html/body/div[3]/div/div[3]/button[1]"},
    #
    #     ]
    #     self.create_gif_process(path_list, "drag_drop_inform_template")
    #     self.view_form()
    def test_remove_element(self):
        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[2]/td[3]/a[2]"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[2]/div/div[1]/div/div[1]/div[2]/div[1]",
                "hover": "",
                "element": ".component-btn-group",
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[2]/div/div[1]/div/div[1]/div[1]/div[1]"
            },
            {"path": "//*[@id='save_btn']"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/button",
                "scroll": "window.scrollTo(0, 600)",
            },
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
        ]
        self.create_gif_process(path_list, "remove_inform_template_element")
        self.view_form()

    def test_add_textfield_derb(self):
        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[2]"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[2]/div/span[1]",
                "extra_action": "drag_and_drop",
                "x": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[2]/div/span[1]",
                "y": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[2]/div",
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[1]/ul/li[2]/a"
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[3]/div[2]/div/div[1]/input"
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[3]/div[2]/div/div[1]/input",
                "extra_action": "setvalue",
                "value": "Clark",
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[1]/ul/li[3]/a"
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[4]/div[4]/div[1]/input",
                "screenshot_name": "textfield_validations",
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[2]/div[2]/button[1]"
            },
            {"path": "//*[@id='save_btn']"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/button",
                "scroll": "window.scrollTo(0, 600)",
            },
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[1]"
            },
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/button"},
        ]
        self.create_gif_process(path_list, "edit_textfield_inform_template")

    def test_add_textfield_calendar_derb(self):
        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[2]"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[2]/div/span[1]",
                "extra_action": "drag_and_drop",
                "x": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[2]/div/span[1]",
                "y": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[2]/div",
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div[10]/div[1]/div[1]/div/div",
                "scroll": '$(".formio-dialog-content").scrollTop(300)',
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div[10]/div[1]/div[2]/div/div[2]"
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[2]/div[2]/button[1]",
                "scroll": '$(".formio-dialog-content").scrollTop(0)',
            },
            {"path": "//*[@id='save_btn']"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/button",
                "scroll": "window.scrollTo(0, 600)",
            },
            {"path": "/html/body/div[8]/div/div[3]/button[1]"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[1]"
            },
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/button"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[1]"
            },
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/button"},
        ]
        self.create_gif_process(path_list, "add_calendar_inform_template")

    def test_add_number_derb(self):
        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[2]"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[2]/div/span[3]",
                "extra_action": "drag_and_drop",
                "x": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[2]/div/span[3]",
                "y": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[2]/div",
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[1]/ul/li[2]/a"
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[3]/div[5]/div[1]/input"
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[3]/div[5]/div[1]/input",
                "extra_action": "setvalue",
                "value": 2,
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[1]/ul/li[3]/a",
                "screenshot_name": "number_input_data",
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[2]/div[2]/button[1]",
                "screenshot_name": "number_input_validations",
            },
            {"path": "//*[@id='save_btn']"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/button",
                "scroll": "window.scrollTo(0, 600)",
            },
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[1]"
            },
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/button"},
        ]
        self.create_gif_process(path_list, "number_input_inform_template")

    def test_add_password_derb(self):
        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[2]"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[2]/div/span[4]",
                "extra_action": "drag_and_drop",
                "x": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[2]/div/span[4]",
                "y": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[2]/div",
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[1]/ul/li[2]/a"
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[1]/ul/li[3]/a",
                "screenshot_name": "password_input_data",
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[2]/div[2]/button[1]",
                "screenshot_name": "password_input_validations",
            },
            {"path": "//*[@id='save_btn']"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/button",
                "scroll": "window.scrollTo(0, 600)",
            },
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[1]"
            },
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/button"},
        ]
        self.create_gif_process(path_list, "password_input_inform_template")

    def test_add_checkbox_derb(self):
        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[2]"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[2]/div/span[5]",
                "extra_action": "drag_and_drop",
                "x": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[2]/div/span[5]",
                "y": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[2]/div",
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/input"
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/input",
                "extra_action": "setvalue",
                "value": "¿Es peligroso?",
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[1]/ul/li[2]/a"
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[1]/ul/li[3]/a",
                "screenshot_name": "checkbox_input_data",
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[2]/div[2]/button[1]",
                "screenshot_name": "checkbox_input_validations",
            },
            {"path": "//*[@id='save_btn']"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/button",
                "scroll": "window.scrollTo(0, 600)",
            },
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[1]"
            },
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/button"},
        ]
        self.create_gif_process(path_list, "checkbox_input_inform_template")

    # def test_add_select_box_derb(self):
    #     path_list = self.path_base+[
    #         {"path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[2]"},
    #         {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[2]/div/span[6]",
    #             "scroll": "window.scrollTo(0, 100)",
    #             "extra_action": "drag_and_drop",
    #             "x": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[2]/div/span[6]",
    #             "y": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[2]/div"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/input",
    #          "extra_action": "clearinput"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/input",
    #          "extra_action": "setvalue", "value": "Seleccione las licencias que posees"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[1]/ul/li[2]/a"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[3]/div[2]/table/tbody/tr/td[2]/div/div[1]/input",
    #          "extra_action": "clearinput"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[3]/div[2]/table/tbody/tr/td[2]/div/div[1]/input",
    #          "extra_action": "setvalue", "value":"A2"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[3]/div[2]/table/tfoot/tr/td/button"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[3]/div[2]/table/tbody/tr[2]/td[2]/div/div[1]/input",
    #          "extra_action": "clearinput"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[3]/div[2]/table/tbody/tr[2]/td[2]/div/div[1]/input",
    #          "extra_action": "setvalue", "value":"B2"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[1]/ul/li[3]/a",
    #          "screenshot_name":"select_box_input_data"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[2]/div[2]/button[1]",
    #          "screenshot_name":"select_box_input_validations"},
    #         {"path": "//*[@id='save_btn']"},
    #         {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/button", "scroll":"window.scrollTo(0, 600)"},
    #         {"path": "/html/body/div[3]/div/div[3]/button[1]"},
    #         {"path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[1]"},
    #         {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/button"},
    #
    #     ]
    #     self.create_gif_process(path_list, "select_box_inform_template")

    def test_add_radio_derb(self):
        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[2]"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[2]/div/span[8]",
                "scroll": "window.scrollTo(0, 110)",
                "extra_action": "drag_and_drop",
                "x": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[2]/div/span[8]",
                "y": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[2]/div",
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/input",
                "value": "clearinput",
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/input",
                "extra_action": "setvalue",
                "value": "¿Es peligroso?",
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[1]/ul/li[2]/a"
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[3]/div[2]/table/tbody/tr/td[2]/div/div[1]/input",
                "extra_action": "clearinput",
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[3]/div[2]/table/tbody/tr/td[2]/div/div[1]/input",
                "extra_action": "setvalue",
                "value": "Si",
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[1]/ul/li[3]/a",
                "screenshot_name": "radio_input_data",
            },
            {
                "path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[2]/div[2]/button[1]",
                "screenshot_name": "radio_input_validations",
            },
            {"path": "//*[@id='save_btn']"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/button",
                "scroll": "window.scrollTo(0, 600)",
            },
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[1]"
            },
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/button"},
        ]
        self.create_gif_process(path_list, "radio_input_inform_template")

    # def test_add_select_api_derb(self):
    #     path_list = self.path_base+[
    #         {"path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[2]"},
    #         {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[1]/div[1]/h5/button",
    #          "extra_action":"script", "value":" document.querySelector('#group-basic').classList.remove('show')"},
    #         {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[2]/div[1]/h5/button",
    #          "extra_action":"script", "value":" document.querySelector('#group-custom').classList.add('show')"},
    #         {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[2]/div[2]/div/span",
    #             "extra_action": "drag_and_drop",
    #             "x": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[1]/div/div/div[2]/div[2]/div/span",
    #             "y": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div/div/div[2]/div"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/input",
    #          "extra_action": "clearinput"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/input",
    #          "extra_action": "setvalue", "value": "Seleccione un laboratorio"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[1]/ul/li[2]/a"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div/div"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[1]/div/div/div[1]/div[1]/div[1]/div[3]/div[2]/div[1]/div[2]/div/div[3]"},
    #         {"path": "/html/body/div[3]/div/div[2]/div[2]/div[2]/div[2]/div[2]/button[1]", "screenshot_name":"select_api_data"},
    #         {"path": "//*[@id='save_btn']"},
    #         {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/button"},
    #         {"path": "/html/body/div[3]/div/div[3]/button[1]"},
    #
    #     ]
    #     self.create_gif_process(path_list, "select_api_inform_template")
    def test_view_inform_template(self):
        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[3]/td[3]/a[1]"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/button",
                "sleep": 20,
            },
        ]
        self.create_gif_process(path_list, "view_inform_template")

    def test_delete_inform_template(self):
        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[3]/td[3]/a[3]"
            },
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
            {"path": "/html/body/div[3]/div/div[3]/button[1]"},
        ]
        self.create_gif_process(path_list, "remove_inform_template")

    def view_form(self):
        path_list = [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a[1]"
            },
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/button"},
        ]
        self.create_gif_process(path_list, "drag_drop_form")
