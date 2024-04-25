from django.test import tag
from django.urls import reverse

from laboratory.tests.selenium_tests.manage_laboratory.test_objects import \
    ObjectSeleniumBase


@tag('selenium')
class EquipmentDropdowmSeleniumTest(ObjectSeleniumBase):

    def setUp(self):
        super().setUp()

        self.url = self.live_server_url + str(
            reverse('laboratory:labindex', kwargs={"org_pk": 1, "lab_pk": 1}))

        self.equipment_path = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[2]/div[2]/ul/li[2]/a[3]"}
        ]

    def test_view_equipment_dropdown(self):
        path_list = self.path_base + [
            {"path": ".//div[1]/div/div[2]/nav/div[1]/ul[2]/li[6]"},
            {"path": "/html/body/div[1]/div/div[2]/nav/div[1]/ul[2]/li[6]/ul/li[7]/a"},
            {
                "path": "/html/body/div[1]/div/div[2]/nav/div[1]/ul[2]/li[6]/ul/li[7]/ul/li[5]/a",
                "active_hidden_elements": "/html/body/div[1]/div/div[2]/nav/div[1]/ul[2]/li[6]/ul/li[7]/a"}
        ]

        self.create_gif_process(path_list, "view_equipment_dropdown")

    def test_view_equipment(self):
        self.selenium.get(url=self.url)

        path_list = [
            {"path": "//*[@id='equipment_table']",
             "extra_action": "script", "value": "window.scrollTo(0, 50)"},
            {"path": "//*[@id='equipment_table']",
             "extra_action": "script", "value": "window.scrollTo(0, 100)"}
        ]

        general_path_list = [self.equipment_path, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmentlistview"],
                                            "view_equipments")

    def test_add_object_equipment(self):
        self.selenium.get(url=self.url)

        path_list = [
            {"path": "//*[@id='equipment_table_wrapper']/div/div[2]/div/button[2]"},
            {"path": "//*[@id='create_obj_form']/div/div/input"},
            {"path": "//*[@id='create_obj_form']/div/div/input", "extra_action": "setvalue", "value": "CE-456"},
            {"path": "//*[@id='create_obj_form']/div[2]/div/input"},
            {"path": "//*[@id='create_obj_form']/div[2]/div/input", "extra_action": "setvalue",
             "value": "BEA143 Beakers 50 mL"},
            {"path": "//*[@id='create_obj_form']/div[3]/div/input"},
            {"path": "//*[@id='create_obj_form']/div[3]/div/input", "extra_action": "setvalue",
             "value": "Vaso de precipitado", "scroll": "$('#create_obj_modal').scrollTop(100);"},
            {"path": "//*[@id='create_obj_form']/div[5]/div/textarea", "scroll": "$('#create_obj_modal').scrollTop(200);"},
            {"path": "//*[@id='create_obj_form']/div[5]/div/textarea", "extra_action": "setvalue",
             "value": "Un vaso de precipitado es un recipiente cilíndrico de vidrio borosilicatado fino que se utiliza muy comúnmente "
                      "en el laboratorio, sobre todo, para preparar o calentar sustancias, medir o traspasar líquidos. Es cilíndrico con un fondo plano; se le encuentra de varias capacidades, desde 1 ml hasta de varios litros. Normalmente es de vidrio, de metal o de "
                      "un plástico en especial y es aquel cuyo objetivo es contener gases o líquidos. Tiene componentes de teflón u otros materiales resistentes a la corrosión."},
            {"path": "//*[@id='create_obj_form']/div[6]/div/span/span/span",
             "scroll": "$('#create_obj_modal').scrollTop(300);"},
            {"path": "/html/body/span/span/span/ul/li[2]", "scroll": "$('#create_obj_modal').scrollTop(450);"},
            {"path": "//*[@id='create_obj_form']/div[7]/div/input", "scroll": "$('#create_obj_modal').scrollTop(550);"},
            {"path": "//*[@id='create_obj_form']/div[7]/div/input", "extra_action": "setvalue", "value": "CA-546"},
            {"path": "//*[@id='create_obj_form']/div[8]/div/input", "scroll": "$('#create_obj_modal').scrollTop(650);"},
            {"path": "//*[@id='create_obj_form']/div[8]/div/input", "extra_action": "setvalue", "value": "B54897"},
            {"path": "//*[@id='create_obj_form']/div[9]/div/input"},
            {"path": "//*[@id='create_obj_form']/div[9]/div/input", "extra_action": "setvalue", "value": "5634646465"},
            {"path": "//*[@id='create_obj_form']/div[12]/div/input"},
            {"path": "//*[@id='create_obj_form']/div[12]/div/input", "extra_action": "setvalue", "value": "20"},
            {"path": "//*[@id='create_obj_form']/div[13]/div/input"},
            {"path": "//*[@id='create_obj_form']/div[13]/div/input", "extra_action": "setvalue", "value": "60"},
            {"path": "//*[@id='create_obj_form']/div[14]/div/span"},
            {"path": "/html/body/span/span/span/ul/li"},
            {"path": "//*[@id='create_obj_form']/div[15]/div/textarea"},
            {"path": "//*[@id='create_obj_form']/div[15]/div/textarea", "extra_action":"setvalue",
             "value": "Utilizar Guantes aislantes, no permitir la manipulaciṕn de menores de edad"},
            {"path": "//*[@id='create_obj_form']/div[17]/div/input", "extra_action": "clearinput"},
            {"path": "//*[@id='create_obj_form']/div[17]/div/input", "extra_action":"setvalue",
             "value": "2", "scroll": "$('#create_obj_modal').scrollTop(700)"},
            {"path": "//*[@id='create_obj_modal']/div/div/div[3]/button[2]"},
        ]

        general_path_list = [self.equipment_path, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmentlistview"],
                                            "add_equipment_object")

    def test_edit_object_equipment(self):
        self.selenium.get(url=self.url)

        path_list = [
            {"path": "//*[@id='equipment_table']/tbody/tr[1]/td[3]/div/i"},
            {"path": "//*[@id='update_obj_form']/div[3]/div/input",
             "extra_action": "setvalue", "value": "Báscula,Romana"},

            {"path": "//*[@id='update_obj_form']/div[5]/div/textarea", "extra_action": "clearinput"},
            {"path": "//*[@id='update_obj_form']/div[5]/div/textarea",
             "extra_action": "setvalue", "value":
                 "Instrumento científico diseñado para medir la fuerza de la gravedad sobre un objeto."},

            {"path": "//*[@id='update_obj_form']/div[7]/div/input", "scroll": "$('#update_obj_form').scrollTop(650)"},
            {"path": "//*[@id='update_obj_form']/div[7]/div/input", "extra_action": "clearinput"},
            {"path": "//*[@id='update_obj_form']/div[7]/div/input", "extra_action": "setvalue", "value": "CA-546"},

            {"path": "//*[@id='update_obj_form']/div[8]/div/input", "extra_action": "clearinput"},
            {"path": "//*[@id='update_obj_form']/div[8]/div/input",
             "extra_action": "setvalue", "value": "B54897"},

            {"path": "//*[@id='update_obj_form']/div[9]/div/input", "scroll": "$('#update_obj_form').scrollTop(800)"},
            {"path": "//*[@id='update_obj_form']/div[9]/div/input", "extra_action": "clearinput"},
            {"path": "//*[@id='update_obj_form']/div[9]/div/input",
             "extra_action": "setvalue", "value": "5634646465"},

            {"path": "//*[@id='update_obj_form']/div[12]/div/input", "extra_action": "clearinput"},
            {"path": "//*[@id='update_obj_form']/div[12]/div/input",
             "extra_action": "setvalue", "value": "20"},

            {"path": "//*[@id='update_obj_form']/div[13]/div/input"},
            {"path": "//*[@id='update_obj_form']/div[13]/div/input",
             "extra_action": "setvalue", "value": "60"},

            {"path": "//*[@id='update_obj_form']/div[14]/div/span"},
            {"path": "/html/body/span/span/span/ul/li"},

            {"path": "//*[@id='update_obj_form']/div[17]/div/input",
             "extra_action": "clearinput"},
            {"path": "//*[@id='update_obj_form']/div[17]/div/input",
             "extra_action": "setvalue",
             "value": "2"},
            {"path": "//*[@id='update_obj_modal']/div/div/div[3]/button[2]", "scroll": "$('#update_obj_modal').scrollTop(350);"}
        ]

        general_path_list = [self.equipment_path, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmentlistview"],
        "update_equipment_object")

    def test_delete_equipment(self):
        self.selenium.get(url=self.url)

        path_list = [
            {"path": "//*[@id='equipment_table']/tbody/tr[1]/td[3]/div/i[2]"},
            {"path": "//*[@id='delete_obj_modal']/div/div/div[3]/button[2]"}
        ]

        general_path_list = [self.equipment_path, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmentlistview"],
                                            "delete_equipment_object")

    def test_search_equipment_object(self):
        self.selenium.get(url=self.url)

        general_search_input = "//*[@id='equipment_table_wrapper']/div/div/div/label/input"
        code_input_search = "//*[@id='equipment_table']/thead/tr[2]/th[2]/input"
        name_input_search = "//*[@id='equipment_table']/thead/tr[2]/th[3]/input"
        clean_filters_btn = "//*[@id='equipment_table_wrapper']/div/div[2]/div/button"

        path_list = [
            {"path": general_search_input},
            {"path": general_search_input, "extra_action": "setvalue", "value": "Balanza"},
            {"path": clean_filters_btn}, {"path": name_input_search},
            {"path": name_input_search, "extra_action": "setvalue", "value": "Balanza Metálica"},
            {"path": clean_filters_btn}, {"path": code_input_search},
            {"path": code_input_search, "extra_action": "setvalue", "value": "BAL713"},
            {"path": clean_filters_btn}
        ]
        general_path_list = [self.equipment_path, path_list]
        self.create_gif_by_change_focus_tab(general_path_list, ["equipmentlistview"],
                                            "search_equipment_object")
