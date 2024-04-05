from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse
from organilab_test.tests.base import SeleniumBase


class ObjectSeleniumBase(SeleniumBase):
    fixtures = ["selenium/laboratory_selenium.json"]
    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)
        self.path_base = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div/div/span/span[1]/span"},
            {"path": "/html/body/span/span/span/ul/li[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div/div/div/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div/div/div[1]/a"},
        ]

@tag('selenium')
class ObjectDropdowmSeleniumTest(ObjectSeleniumBase):
    def test_view_material_dropdown(self):

        path_list = self.path_base+[
            {"path": ".//div[1]/div/div[2]/nav/div[1]/ul[2]/li[6]"},
            {"path": "/html/body/div[1]/div/div[2]/nav/div[1]/ul[2]/li[6]/ul/li[7]/a"},
            {"path": "/html/body/div[1]/div/div[2]/nav/div[1]/ul[2]/li[6]/ul/li[7]/ul/li[3]/a",
                "active_hidden_elements": "/html/body/div[1]/div/div[2]/nav/div[1]/ul[2]/li[6]/ul/li[7]/a"}
        ]
        self.create_gif_process(path_list, "view_material_dropdown")

    def test_view_reactive_dropdown(self):

        path_list = self.path_base+[
            {"path": ".//div[1]/div/div[2]/nav/div[1]/ul[2]/li[6]"},
            {"path": "/html/body/div[1]/div/div[2]/nav/div[1]/ul[2]/li[6]/ul/li[7]/a"},
            {"path":"/html/body/div[1]/div/div[2]/nav/div[1]/ul[2]/li[6]/ul/li[7]/ul/li[1]/a",
             "active_hidden_elements":"/html/body/div[1]/div/div[2]/nav/div[1]/ul[2]/li[6.]/ul/li[7]/a"}
            ]

        self.create_gif_process(path_list, "view_reactive_dropdown")

@tag('selenium')
class ObjectSeleniumTest(ObjectSeleniumBase):

    def test_view_material_dropdown(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[2]/a[2]"}
        ]
        self.create_gif_process(path_list, "view_materials")

    def test_add_object_material(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[2]/a[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/a"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form"},
            {"path": "//*[@id='id_code']","extra_action":"clearIvput"},
            {"path": "//*[@id='id_code']","extra_action":"setvalue", "value":"CE-456"},
            {"path": "//*[@id='id_name']","extra_action":"clearInput"},
            {"path": "//*[@id='id_name']","extra_action":"setvalue", "value":"BEA143 Beakers 50 mL"},
            {"path": "//*[@id='id_synonym']","extra_action":"clearinput"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form/div[4]/div/span"},
            {"path": "//*[@id='id_description']","extra_action":"clearinput"},
            {"path": "//*[@id='id_description']","extra_action":"setvalue", "value":
               "Un vaso de precipitado es un recipiente cilíndrico de vidrio borosilicatado fino que se utiliza muy comúnmente "
             },
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form/div[6]/div/span/span[1]/span","scroll":"window.scrollTo(0, 350)"},
            {"path": "/html/body/span/span/span/ul/li[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form/div[7]/div/span"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form/input[2]"},
            ]
        self.create_gif_process(path_list, "add_material_object")

    def test_edit_object_material(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[2]/a[2]","screenshot_name":"material_object"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[3]/ul/li[1]/div[2]/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form"},
            {"path": "//*[@id='id_code']","extra_action":"clearIvput"},
            {"path": "//*[@id='id_code']","extra_action":"setvalue", "value":"CE-456"},
            {"path": "//*[@id='id_name']","extra_action":"clearinput"},
            {"path": "//*[@id='id_name']","extra_action":"setvalue", "value":"BEA143 Beakers 50 mL"},
            {"path": "//*[@id='id_synonym']","extra_action":"clearinput"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form/div[4]/div/span"},
            {"path": "//*[@id='id_description']","extra_action":"clearinput"},
            {"path": "//*[@id='id_description']","extra_action":"setvalue", "value":
               "Un vaso de precipitado es un recipiente cilíndrico de vidrio borosilicatado fino que se utiliza muy comúnmente "
               "en el laboratorio, sobre todo, para preparar o calentar sustancias, medir o traspasar líquidos. Es cilíndrico con un fondo plano; se le encuentra de varias capacidades, desde 1 ml hasta de varios litros. Normalmente es de vidrio, de metal o de "
               "un plástico en especial y es aquel cuyo objetivo es contener gases o líquidos. Tiene componentes de teflón u otros materiales resistentes a la corrosión."},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form/div[6]/div/span/span[1]/span","scroll":"window.scrollTo(0, 350)"},
            {"path": "/html/body/span/span/span/ul/li[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form/input[2]"},
            ]
        self.create_gif_process(path_list, "update_material_object")

    def test_add_object_material_is_container(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[2]/a[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/a"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form","screenshot_name":"form_material_object"},
            {"path": "//*[@id='id_code']","extra_action":"clearIvput"},
            {"path": "//*[@id='id_code']","extra_action":"setvalue", "value":"CE-456"},
            {"path": "//*[@id='id_name']","extra_action":"clearInput"},
            {"path": "//*[@id='id_name']","extra_action":"setvalue", "value":"BEA143 Beakers 50 mL"},
            {"path": "//*[@id='id_synonym']","extra_action":"clearinput"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form/div[4]/div/span"},
            {"path": "//*[@id='id_description']","extra_action":"clearinput"},
            {"path": "//*[@id='id_description']","extra_action":"setvalue", "value":
               "Un vaso de precipitado es un recipiente cilíndrico de vidrio borosilicatado fino que se utiliza muy comúnmente "
               "en el laboratorio, sobre todo, para preparar o calentar sustancias, medir o traspasar líquidos. Es cilíndrico con un fondo plano; se le encuentra de varias capacidades, desde 1 ml hasta de varios litros. Normalmente es de vidrio, de metal o de "
               "un plástico en especial y es aquel cuyo objetivo es contener gases o líquidos. Tiene componentes de teflón u otros materiales resistentes a la corrosión."},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form/div[6]/div/span/span[1]/span","scroll":"window.scrollTo(0, 450)"},
            {"path": "/html/body/span/span/span/ul/li[2]"},
            {"path": "//*[@id='id_capacity']", "extra_action": "clearInput"},
            {"path": "//*[@id='id_capacity']", "extra_action": "setvalue", "value": 40},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form/div[9]/div/span/span[1]/span"},
            {"path": ".//span/span/span[2]/ul/li[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form/div[7]/div/span"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/form/input[2]"}
            ]

        self.create_gif_process(path_list, "add_material_container_object")

    def test_delete_material(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[2]/a[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[3]/ul/li[1]/div[2]/a[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/form/input[2]"},

            ]
        self.create_gif_process(path_list, "delete_material_object")

    def test_view_material(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[2]/a[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/form/div/input[1]", "extra_action":"clearinput"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/form/div/input[1]", "extra_action":"setvalue", "value":"Balones"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/form/button"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/form/div/input[1]", "extra_action":"clearinput"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/form/div/input[1]", "extra_action":"setvalue", "value":"Ba"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/form/button"},

            ]
        self.create_gif_process(path_list, "search_material_object")

    def test_view_reactive(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[2]/a[1]","screenshot_name":"reactive_object"}
        ]
        self.create_gif_process(path_list, "view_reactive_objects")


    def test_add_reactive_object(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[2]/a[1]","screenshot_name":"reactive_object"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div[1]/a"},
            {"path": "//*[@id='id_name']", "extra_action": "setvalue", "value": "BEA143 Beakers 50 mL"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div/div/form/div[1]/div[3]/div[1]/span[2]"},
            {"path": "/html/body/span/span/span[2]/ul/li[2]"},
            {"path": "//*[@id='id_synonym']", "extra_action": "setvalue", "value":"ss454"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div/div/form/div[1]/div[3]/div[2]/span[2]/span[1]/span"},
            {"path": "/html/body/span/span/span[2]/ul/li[2]"},
            {"path": "//*[@id='id_code']", "extra_action": "setvalue", "value": "CE-456"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div/div/form/div[1]/div[3]/div[3]/span[2]/span[1]/span"},
            {"path": "/html/body/span/span/span/ul/li[2]"},
            {"path": "//*[@id='id_description']", "extra_action": "setvalue", "value":
                "Un vaso de precipitado es un recipiente cilíndrico de vidrio borosilicatado fino que se utiliza muy comúnmente ,",
                "scroll":"window.scrollTo(0, 400)"
            },
            {"path": "//*[@id='id_molecular_formula']", "extra_action": "setvalue", "value": "AE2"},
            {"path": "//*[@id='id_cas_id_number']", "extra_action": "setvalue", "value": "12633468"},
            {"path": "//*[@id='id_model']", "scroll": "window.scrollTo(0, 400)"},
            {"path": "//*[@id='id_model']", "extra_action": "setvalue",
             "value": "CA-546"},
            {"path": "//*[@id='id_serie']", "extra_action": "setvalue",
             "value": "B54897"},
            {"path": "//*[@id='id_plaque']", "extra_action": "setvalue", "value": "5634646465"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div/div/form/div[1]/div[2]/div[9]/span[2]/span[1]/span"},
            {"path": "/html/body/span/span/span/ul/li[2]"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div/div/form/div[1]/div[3]/div[9]/span[2]/span[1]/span",  "scroll": "window.scrollTo(0, 800)"},
            {"path": "/html/body/span/span/span[2]/ul/li[2]"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div/div/form/div[1]/div[3]/div[10]/span[2]/span[1]/span"},
            {"path": "/html/body/span/span/span/ul/li[2]"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div/div/form/div[1]/div[3]/div[11]/span[2]/span[1]/span"},
            {"path": "/html/body/span/span/span/ul/li[2]"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div/div/form/div[1]/div[3]/div[12]/span[2]/span[1]/span","scroll": "window.scrollTo(0, 1000)"},
            {"path": "/html/body/span/span/span/ul/li[2]"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div/div/form/div[1]/div[3]/div[13]/span[2]/span[1]/span"},
            {"path": "/html/body/span/span/span/ul/li[2]"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div/div/form/div[2]/button", "scroll": "window.scrollTo(0, 1100)"},

        ]
        self.create_gif_process(path_list, "add_reactive_object")


    def test_edit_reactive_object(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[2]/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div[2]/div[2]/div/table/tbody/tr[2]/td[4]/a[1]"},
            {"path": "//*[@id='id_name']", "extra_action": "clearinput"},
            {"path": "//*[@id='id_name']", "extra_action": "setvalue", "value": "BEA143 Beakers 50 mL"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div/div/form/div[1]/div[3]/div[1]/span[2]"},
            {"path": "/html/body/span/span/span[2]/ul/li[2]"},
            {"path": "//*[@id='id_synonym']", "extra_action": "clearinput"},
            {"path": "//*[@id='id_synonym']", "extra_action": "setvalue", "value":"ss454"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div/div/form/div[1]/div[3]/div[2]/span[2]/span[1]/span"},
            {"path": "/html/body/span/span/span[2]/ul/li[2]"},
            {"path": "//*[@id='id_code']", "extra_action": "clearinput"},
            {"path": "//*[@id='id_code']", "extra_action": "setvalue", "value": "CE-456"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div/div/form/div[1]/div[3]/div[3]/span[2]/span[1]/span"},
            {"path": "/html/body/span/span/span/ul/li[2]"},
            {"path": "//*[@id='id_description']", "extra_action": "clearinput"},
            {"path": "//*[@id='id_description']", "extra_action": "setvalue", "value":
                "Un vaso de precipitado es un recipiente cilíndrico de vidrio borosilicatado fino que se utiliza muy comúnmente ,",
                "scroll":"window.scrollTo(0, 400)"
            },
            {"path": "//*[@id='id_molecular_formula']", "extra_action": "clearinput"},
            {"path": "//*[@id='id_molecular_formula']", "extra_action": "setvalue", "value": "AE2"},
            {"path": "//*[@id='id_cas_id_number']", "extra_action": "clearinput"},
            {"path": "//*[@id='id_cas_id_number']", "extra_action": "setvalue", "value": "12633468"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div/div/form/div[1]/div[3]/div[9]/span[2]/span[1]/span",  "scroll": "window.scrollTo(0, 800)"},
            {"path": "/html/body/span/span/span[2]/ul/li[2]"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div/div/form/div[1]/div[3]/div[10]/span[2]/span[1]/span"},
            {"path": "/html/body/span/span/span/ul/li[2]"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div/div/form/div[1]/div[3]/div[11]/span[2]/span[1]/span"},
            {"path": "/html/body/span/span/span/ul/li[2]"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div/div/form/div[1]/div[3]/div[12]/span[2]/span[1]/span","scroll": "window.scrollTo(0, 1000)"},
            {"path": "/html/body/span/span/span/ul/li[2]"},
            {"path": "/html/body/div[1]/div[1]/div[3]/div/div/div/form/div[2]/button"},

        ]
        self.create_gif_process(path_list, "update_reactive_object")

    def test_delete_reactive(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [

            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[2]/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div[2]/div[2]/div/table/tbody/tr[1]/td[4]/a[2]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/form/input[3]"},

            ]
        self.create_gif_process(path_list, "delete_reactive_object")

    def test_search_reactive(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[2]/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div[2]/div[1]/div[2]/div/label/input", "extra_action": "clearinput"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div/div[2]/div[1]/div[2]/div/label/input", "extra_action": "setvalue", "value":"Alcohol"},
            ]
        self.create_gif_process(path_list, "search_reactive_object")


@tag('selenium')
class ObjectFeaturesSeleniumTest(ObjectSeleniumBase):

    def test_view_object_features(self):
        path_list = self.path_base+[
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[3]/a"},
            {"path": ".//div[1]/div/div[3]/div/div/div/div[2]/div/form", "screenshot_name":"object_features_view"},
            ]
        self.create_gif_process(path_list, "view_object_features")

    def test_view_object_features_dropdown(self):
        path_list = self.path_base+[
            {"path": "/html/body/div[1]/div/div[2]/nav/div[1]/ul[2]/li[6]/a"},
            {"path": "/html/body/div[1]/div/div[2]/nav/div[1]/ul[2]/li[6]/ul/li[9]/a"},
            ]
        self.create_gif_process(path_list, "view_object_features_dropdown")

    def test_add_object_features(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[3]/a"},
            {"path": ".//*[@id='id_name']", "extra_action":"clearinput"},
            {"path": ".//*[@id='id_name']", "extra_action":"setvalue",
             "value": "Química Orgánica"},
            {"path": ".//*[@id='id_description']", "extra_action":"clearinput"},
            {"path": ".//*[@id='id_description']", "extra_action":"setvalue",
             "value": "Objetos exclusivos o representativos de la disciplina de quimica orgánica, ejemplo : equipo especial para síntesis."},
            {"path": ".//div[1]/div/div[3]/div/div/div/div[2]/div/form/div[3]/div/button"},
            {"path": ".//div[1]/div/div[3]/div/div/div/div[3]/div[1]/li[3]",
             "scroll": "window.scrollTo(0, 350)"},

        ]
        self.create_gif_process(path_list, "view_object_features")

    def test_edit_object_features(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[3]/a"},
            {"path": ".//div[1]/div/div[3]/div/div/div/div[3]/div[1]/li[1]/div[3]/div/a[1]"},
            {"path": ".//*[@id='id_name']", "extra_action":"clearinput"},
            {"path": ".//*[@id='id_name']", "extra_action":"setvalue",
             "value": "Química Orgánica"},
            {"path": ".//*[@id='id_description']", "extra_action":"clearinput"},
            {"path": ".//*[@id='id_description']", "extra_action":"setvalue",
             "value": "Objetos exclusivos o representativos de la disciplina de quimica orgánica, ejemplo : equipo especial para síntesis."},
            {"path": ".//div[1]/div/div[3]/div/div/div/div[2]/div/form/div[3]/div/button"},
            {"path": ".//div[1]/div/div[3]/div/div/div/div[3]/div[1]/li[1]/div[1]"},

        ]
        self.create_gif_process(path_list, "view_object_features")

    def test_delete_object_features(self):
        self.selenium.get(url= self.live_server_url + str(reverse('laboratory:labindex',kwargs={"org_pk":1,"lab_pk":1})))
        path_list = [
            {"path": ".//div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[3]/a"},
            {"path": ".//div[1]/div/div[3]/div/div/div/div[3]/div[1]/li[1]/div[3]/div/a[2]"},
            {"path": ".//div[1]/div/div[3]/div/div/form/input[2]"},
        ]
        self.create_gif_process(path_list, "view_object_features")




