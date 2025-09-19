from django.contrib.auth.models import User
from django.test import tag
from organilab_test.tests.base import SeleniumBase


class RiskSeleniumBase(SeleniumBase):
    fixtures = ["selenium/risk_management.json"]

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
                "path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div/div/div/a[3]"
            },
        ]


@tag("selenium")
class RiskSeleniumTest(RiskSeleniumBase):

    def test_view_risk(self):

        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div/h3/span",
                "screenshot_name": "view_risk_module",
            },
        ]
        self.create_gif_process(path_list, "view_risk")

    def test_view_risk_sidebar(self):

        path_list = [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div/div/span/span[1]/span"
            },
            {"path": "/html/body/span/span/span/ul/li[1]"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div/div/div/a[1]"
            },
            {"path": "/html/body/div[1]/div/div[1]/div/div[4]/div/ul/li[5]/a"},
            {"path": "/html/body/div[1]/div/div[1]/div/div[4]/div/ul/li[5]/ul/li[1]/a"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div/h3/span"},
        ]
        self.create_gif_process(path_list, "view_risk_sidebar")

    def test_add_risk(self):

        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form/div[2]/div/a"
            },
            {"path": "//*[@id='id_name']", "extra_action": "clearinput"},
            {
                "path": "//*[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Bodega de equipos",
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[2]/div/span"
            },
            {"path": "/html/body/span/span/span/ul/li[1]"},
            {"path": "//*[@id='id_num_workers']", "extra_action": "clearinput"},
            {
                "path": "//*[@id='id_num_workers']",
                "extra_action": "setvalue",
                "value": 5,
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[4]/div/div/span"
            },
            {"path": "/html/body/span/span/span[2]/ul/li[2]"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[5]/div/button"
            },
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div/h3/span"},
        ]
        self.create_gif_process(path_list, "add_risk")

    def test_edit_risk(self):

        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/ul/li[1]/div/div[2]/div/a[1]"
            },
            {"path": "//*[@id='id_name']", "extra_action": "clearinput"},
            {
                "path": "//*[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Bodega de equipos",
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[5]/div/button"
            },
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div/h3/span"},
        ]
        self.create_gif_process(path_list, "edit_risk")

    def test_remove_risk(self):

        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/ul/li[1]/div/div[2]/div/a[2]"
            },
            {"path": "/html/body/div[1]/div/div[3]/div/div/form/input[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div/h3/span"},
        ]
        self.create_gif_process(path_list, "remove_risk")

    def test_add_zone_type(self):

        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form/div[2]/div/a"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[4]/div/div/button"
            },
            {
                "path": "/html/body/div[3]/div/div/div[2]/div/form/div[1]/div/input",
                "extra_action": "clearinput",
            },
            {
                "path": "/html/body/div[3]/div/div/div[2]/div/form/div[1]/div/input",
                "extra_action": "setvalue",
                "value": "Estanteria",
            },
            {
                "path": "/html/body/div[3]/div/div/div[2]/div/form/div[2]/div/select/option[1]"
            },
            {"path": "/html/body/div[3]/div/div/div[3]/button[2]"},
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[4]/div/div/span"
            },
        ]
        self.create_gif_process(path_list, "add_zone_type")

    def test_view_rizk_zone_detail(self):

        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/ul/li[1]/div/div[1]/a"
            },
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/h3/span"},
        ]
        self.create_gif_process(path_list, "view_risk_detail")

    def test_update_risk_two(self):

        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/ul/li[1]/div/div[1]/a"
            },
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[3]/div/div[1]/a[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/h3/span"},
        ]
        self.create_gif_process(path_list, "update_risk_two")

    def test_view_incident(self):

        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/ul/li[1]/div/div[1]/a"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[4]/div/ul/li/div[2]/a[1]"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[1]/div/div/h3",
                "screenshot_name": "view_incident_module",
            },
        ]
        self.create_gif_process(path_list, "view_incidents")

    def test_add_incident(self):

        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/ul/li[1]/div/div[1]/a"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[4]/div/ul/li/div[2]/a[2]"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[1]/div/input",
                "extra_action": "clearinput",
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[1]/div/input",
                "extra_action": "setvalue",
                "value": "Jose dejo caer una bascula al 13 hrs.",
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[2]/div/div/input"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[2]/div/div/span"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[4]/div/div[2]",
                "extra_action": "script",
                "value": 'tinymce.get("id_causes").setContent("<p>Se tropezo con el estante que se encontraba el objecto </p>");',
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[5]/div/div[2]",
                "scroll": "window.scrollTo(0, 300)",
                "extra_action": "script",
                "value": 'tinymce.get("id_infraestructure_impact").setContent("<p><strong>Se daño la ceramica del piso</strong></p>");',
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[6]/div/div[2]",
                "extra_action": "script",
                "value": 'tinymce.get("id_people_impact").setContent("<p><strong>Ninguna</strong></p>");',
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[7]/div/div[2]",
                "scroll": "window.scrollTo(0, 800)",
                "extra_action": "script",
                "value": 'tinymce.get("id_environment_impact").setContent("<p><strong>Ninguno</strong></p>");',
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[8]/div/div[2]",
                "extra_action": "script",
                "value": 'tinymce.get("id_result_of_plans").setContent("<p><strong>Se aplica protocolo de caída de equipos</strong></p>");',
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[9]/div/div[2]",
                "scroll": "window.scrollTo(0, 1200)",
                "extra_action": "script",
                "value": 'tinymce.get("id_mitigation_actions").setContent("<p><strong>Limpieza y recoleccion de materiales esparcidos</strong></p>");',
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[10]/div/div[2]",
                "extra_action": "script",
                "value": 'tinymce.get("id_recomendations").setContent("<p><strong>Tener más cuidado</strong></p>");',
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[12]/div/button",
                "scroll": "window.scrollTo(0, 1500)",
            },
        ]
        self.create_gif_process(path_list, "add_incidents")

    def test_edit_incident(self):
        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/ul/li[1]/div/div[1]/a"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[4]/div/ul/li/div[2]/a[1]"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/ul/li[1]/div/div[2]/div/a[1]"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[1]/div/input",
                "extra_action": "clearinput",
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[1]/div/input",
                "extra_action": "setvalue",
                "value": "Jose dejo caer una bascula al 13 hrs.",
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[9]/div/div[2]",
                "scroll": "window.scrollTo(0, 1200)",
                "extra_action": "script",
                "value": 'tinymce.get("id_mitigation_actions").setContent("<p><strong>Limpieza y recoleccion de materiales esparcidos</strong></p>");',
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[10]/div/div[2]",
                "extra_action": "script",
                "value": 'tinymce.get("id_recomendations").setContent("<p><strong>Tener más cuidado</strong></p>");',
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[3]/form/div[12]/div/button",
                "scroll": "window.scrollTo(0, 1500)",
            },
        ]
        self.create_gif_process(path_list, "update_incidents")

    def test_remove_incident(self):

        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/ul/li[1]/div/div[1]/a"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[4]/div/ul/li/div[2]/a[1]"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/ul/li/div/div[2]/div/a[2]"
            },
            {"path": "/html/body/div[1]/div/div[3]/div/div/form/input[2]"},
        ]
        self.create_gif_process(path_list, "remove_incidents")

    def test_download_incident(self):

        path_list = self.path_base + [
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/ul/li[1]/div/div[1]/a"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[4]/div/ul/li/div[2]/a[1]"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div/ul/li[1]/div/div[1]/a"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[4]/div/ul/li/div[2]/div/button[2]"
            },
            {
                "path": "/html/body/div[1]/div/div[3]/div/div/div[4]/div/ul/li/div[2]/div/ul/li[4]/a"
            },
        ]
        self.create_gif_process(path_list, "download_incidents")
