from django.test import tag

from laboratory.tests.selenium_tests.manage_laboratory.test_objects import (
    ObjectSeleniumBase,
)


@tag("selenium")
class EquipmentDropdowmSeleniumTest(ObjectSeleniumBase):

    def setUp(self):
        super().setUp()

    def test_view_equipment_dropdown(self):
        """Test viewing the equipment link in laboratory index page.

        Flow: Navigate to lab index -> Click Equipment link.

        GIF: docs/source/_static/gif/view_equipment_dropdown.gif
        """
        self.navigate_to_lab_index()
        path_list = [
            {
                "path": "//a[contains(@href, '/equipment')]",
            },
        ]
        self.create_gif_process(path_list, "view_equipment_dropdown")

    def test_view_equipment(self):
        """Test viewing the equipment list page.

        Flow: Navigate to equipment list -> Scroll through DataTable.

        GIF: docs/source/_static/gif/view_equipments.gif
        """
        self.navigate_to_equipment_list()
        path_list = [
            {
                "path": "//*[@id='equipment_table']",
                "extra_action": "script",
                "value": "window.scrollTo(0, 50)",
            },
            {
                "path": "//*[@id='equipment_table']",
                "extra_action": "script",
                "value": "window.scrollTo(0, 100)",
            },
        ]
        self.create_gif_process(path_list, "view_equipments")

    def test_add_object_equipment(self):
        """Test adding a new equipment object.

        Flow: Navigate to equipment list -> Click create button -> Fill form
        (code, name, synonym, description, features, model, serie,
        plaque, voltage, amperage, providers, special conditions,
        clean period) -> Save.

        GIF: docs/source/_static/gif/add_equipment_object.gif
        """
        self.navigate_to_equipment_list()
        path_list = [
            {
                "path": "//*[@id='equipment_table_wrapper']//button[contains(@class, 'btn-outline-success')]",
                "wait_ready": True,
            },
            {
                "path": "//form[@id='create_obj_form']//input[@name='create-code']",
                "sleep": 2,
            },
            {
                "path": "//form[@id='create_obj_form']//input[@name='create-code']",
                "extra_action": "setvalue",
                "value": "CE-456",
            },
            {
                "path": "//form[@id='create_obj_form']//input[@name='create-name']",
            },
            {
                "path": "//form[@id='create_obj_form']//input[@name='create-name']",
                "extra_action": "setvalue",
                "value": "BEA143 Beakers 50 mL",
            },
            {
                "path": "//form[@id='create_obj_form']//input[@name='create-synonym']",
            },
            {
                "path": "//form[@id='create_obj_form']//input[@name='create-synonym']",
                "extra_action": "setvalue",
                "value": "Vaso de precipitado",
                "scroll": "$('#create_obj_modal').scrollTop(100);",
            },
            {
                "path": "//form[@id='create_obj_form']//textarea[@name='create-description']",
                "scroll": "$('#create_obj_modal').scrollTop(200);",
            },
            {
                "path": "//form[@id='create_obj_form']//textarea[@name='create-description']",
                "extra_action": "setvalue",
                "value": "Un vaso de precipitado es un recipiente cilíndrico de vidrio borosilicatado fino que se utiliza muy comúnmente "
                "en el laboratorio, sobre todo, para preparar o calentar sustancias, medir o traspasar líquidos. Es cilíndrico con un fondo plano; se le encuentra de varias capacidades, desde 1 ml hasta de varios litros. Normalmente es de vidrio, de metal o de "  # noqa: E501
                "un plástico en especial y es aquel cuyo objetivo es contener gases o líquidos. Tiene componentes de teflón u otros materiales resistentes a la corrosión.",
            },
            {
                "path": "//select[@id='id_create-features']/following-sibling::span//span[contains(@class, 'select2-selection')]",
                "scroll": "$('#create_obj_modal').scrollTop(300);",
            },
            {
                "path": "//ul[contains(@class, 'select2-results__options')]/li[1]",
                "scroll": "$('#create_obj_modal').scrollTop(450);",
            },
            {
                "path": "//form[@id='create_obj_form']//input[@name='create-model']",
                "scroll": "$('#create_obj_modal').scrollTop(550);",
            },
            {
                "path": "//form[@id='create_obj_form']//input[@name='create-model']",
                "extra_action": "setvalue",
                "value": "CA-546",
            },
            {
                "path": "//form[@id='create_obj_form']//input[@name='create-serie']",
                "scroll": "$('#create_obj_modal').scrollTop(650);",
            },
            {
                "path": "//form[@id='create_obj_form']//input[@name='create-serie']",
                "extra_action": "setvalue",
                "value": "B54897",
            },
            {
                "path": "//form[@id='create_obj_form']//input[@name='create-plaque']",
            },
            {
                "path": "//form[@id='create_obj_form']//input[@name='create-plaque']",
                "extra_action": "setvalue",
                "value": "5634646465",
            },
            {
                "path": "//form[@id='create_obj_form']//input[@name='create-operation_voltage']",
            },
            {
                "path": "//form[@id='create_obj_form']//input[@name='create-operation_voltage']",
                "extra_action": "setvalue",
                "value": "20",
            },
            {
                "path": "//form[@id='create_obj_form']//input[@name='create-operation_amperage']",
            },
            {
                "path": "//form[@id='create_obj_form']//input[@name='create-operation_amperage']",
                "extra_action": "setvalue",
                "value": "60",
            },
            {
                "path": "//select[@id='id_create-providers']/following-sibling::span//span[contains(@class, 'select2-selection')]",
            },
            {
                "path": "//ul[contains(@class, 'select2-results__options')]/li",
            },
            {
                "path": "//form[@id='create_obj_form']//textarea[@name='create-use_specials_conditions']",
            },
            {
                "path": "//form[@id='create_obj_form']//textarea[@name='create-use_specials_conditions']",
                "extra_action": "setvalue",
                "value": "Utilizar Guantes aislantes, no permitir la manipulación de menores de edad",
            },
            {
                "path": "//form[@id='create_obj_form']//input[@name='create-clean_period_according_to_provider']",
                "extra_action": "clearinput",
            },
            {
                "path": "//form[@id='create_obj_form']//input[@name='create-clean_period_according_to_provider']",
                "extra_action": "setvalue",
                "value": "2",
                "scroll": "$('#create_obj_modal').scrollTop(700)",
            },
            {
                "path": "//*[@id='create_obj_modal']//button[contains(@class, 'btn-primary')]",
            },
        ]
        self.create_gif_process(path_list, "add_equipment_object")

    def test_edit_object_equipment(self):
        """Test editing an existing equipment object.

        Flow: Navigate to equipment list -> Click edit icon on first row ->
        Update synonym, description, model, serie, plaque, voltage,
        amperage, providers, clean period -> Save.

        GIF: docs/source/_static/gif/update_equipment_object.gif
        """
        self.navigate_to_equipment_list()
        path_list = [
            {
                "path": "//*[@id='equipment_table']//tbody/tr[1]//i[contains(@class, 'fa-edit')]",
                "wait_ready": True,
            },
            {
                "path": "//form[@id='update_obj_form']//input[@name='update-synonym']",
                "extra_action": "setvalue",
                "value": "Báscula,Romana",
                "sleep": 1,
            },
            {
                "path": "//form[@id='update_obj_form']//textarea[@name='update-description']",
                "extra_action": "clearinput",
            },
            {
                "path": "//form[@id='update_obj_form']//textarea[@name='update-description']",
                "extra_action": "setvalue",
                "value": "Instrumento científico diseñado para medir la fuerza de la gravedad sobre un objeto.",
            },
            {
                "path": "//form[@id='update_obj_form']//input[@name='update-model']",
                "scroll": "$('#update_obj_form').scrollTop(650)",
            },
            {
                "path": "//form[@id='update_obj_form']//input[@name='update-model']",
                "extra_action": "clearinput",
            },
            {
                "path": "//form[@id='update_obj_form']//input[@name='update-model']",
                "extra_action": "setvalue",
                "value": "CA-546",
            },
            {
                "path": "//form[@id='update_obj_form']//input[@name='update-serie']",
                "extra_action": "clearinput",
            },
            {
                "path": "//form[@id='update_obj_form']//input[@name='update-serie']",
                "extra_action": "setvalue",
                "value": "B54897",
            },
            {
                "path": "//form[@id='update_obj_form']//input[@name='update-plaque']",
                "scroll": "$('#update_obj_form').scrollTop(800)",
            },
            {
                "path": "//form[@id='update_obj_form']//input[@name='update-plaque']",
                "extra_action": "clearinput",
            },
            {
                "path": "//form[@id='update_obj_form']//input[@name='update-plaque']",
                "extra_action": "setvalue",
                "value": "5634646465",
            },
            {
                "path": "//form[@id='update_obj_form']//input[@name='update-operation_voltage']",
                "extra_action": "clearinput",
            },
            {
                "path": "//form[@id='update_obj_form']//input[@name='update-operation_voltage']",
                "extra_action": "setvalue",
                "value": "20",
            },
            {
                "path": "//form[@id='update_obj_form']//input[@name='update-operation_amperage']",
            },
            {
                "path": "//form[@id='update_obj_form']//input[@name='update-operation_amperage']",
                "extra_action": "setvalue",
                "value": "60",
            },
            {
                "path": "//select[@id='id_update-providers']/following-sibling::span//span[contains(@class, 'select2-selection')]",
            },
            {
                "path": "//ul[contains(@class, 'select2-results__options')]/li",
            },
            {
                "path": "//form[@id='update_obj_form']//input[@name='update-clean_period_according_to_provider']",
                "extra_action": "clearinput",
            },
            {
                "path": "//form[@id='update_obj_form']//input[@name='update-clean_period_according_to_provider']",
                "extra_action": "setvalue",
                "value": "2",
            },
            {
                "path": "//*[@id='update_obj_modal']//button[contains(@class, 'btn-primary')]",
                "scroll": "$('#update_obj_modal').scrollTop(350);",
            },
        ]
        self.create_gif_process(path_list, "update_equipment_object")

    def test_delete_equipment(self):
        """Test deleting an equipment object.

        Flow: Navigate to equipment list -> Click delete icon on first row ->
        Confirm deletion in modal.

        GIF: docs/source/_static/gif/delete_equipment_object.gif
        """
        self.navigate_to_equipment_list()
        path_list = [
            {
                "path": "//*[@id='equipment_table']//tbody/tr[1]//i[contains(@class, 'fa-trash')]",
                "wait_ready": True,
            },
            {
                "path": "//*[@id='delete_obj_modal']//button[contains(@class, 'btn-primary')]",
            },
        ]
        self.create_gif_process(path_list, "delete_equipment_object")

    def test_search_equipment_object(self):
        """Test searching for equipment objects using filters.

        Flow: Navigate to equipment list -> Search by general filter ->
        Clear -> Search by name column -> Clear -> Search by code
        column -> Clear.

        GIF: docs/source/_static/gif/search_equipment_object.gif
        """
        self.navigate_to_equipment_list()

        general_search_input = "//*[@id='equipment_table_filter']//input"
        code_input_search = "//*[@id='equipment_table']//thead/tr[2]/th[2]/input"
        name_input_search = "//*[@id='equipment_table']//thead/tr[2]/th[3]/input"
        clean_filters_btn = "//*[@id='equipment_table_wrapper']//button[.//i[contains(@class, 'fa-eraser')]]"

        path_list = [
            {"path": general_search_input, "wait_ready": True},
            {
                "path": general_search_input,
                "extra_action": "setvalue",
                "value": "Balanza",
            },
            {"path": clean_filters_btn},
            {"path": name_input_search},
            {
                "path": name_input_search,
                "extra_action": "setvalue",
                "value": "Balanza Metálica",
            },
            {"path": clean_filters_btn},
            {"path": code_input_search},
            {
                "path": code_input_search,
                "extra_action": "setvalue",
                "value": "BAL713",
            },
            {"path": clean_filters_btn},
        ]
        self.create_gif_process(path_list, "search_equipment_object")
