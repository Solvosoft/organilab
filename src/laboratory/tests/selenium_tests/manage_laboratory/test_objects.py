from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse
from organilab_test.tests.base import OptimizedSeleniumBase, modifies_db


class ObjectSeleniumBase(OptimizedSeleniumBase):
    fixtures = ["selenium/base_selenium.json", "selenium/laboratory_delta.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )

    def navigate_to_lab_index(self):
        url = self.live_server_url + str(
            reverse("laboratory:labindex", kwargs={"org_pk": 1, "lab_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_object_view(self):
        """Navigate to the material/object list page."""
        url = self.live_server_url + str(
            reverse("laboratory:object_view", kwargs={"org_pk": 1, "lab_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_substance_list(self):
        """Navigate to the reactive/substance list page."""
        url = self.live_server_url + str(
            reverse("laboratory:sustance_list", kwargs={"org_pk": 1, "lab_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_object_features(self):
        """Navigate to the object features page."""
        url = self.live_server_url + str(
            reverse("laboratory:objectfeatures_view", kwargs={"org_pk": 1, "lab_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_equipment_list(self):
        """Navigate to the equipment list page."""
        url = self.live_server_url + str(
            reverse("laboratory:equipment_list", kwargs={"org_pk": 1, "lab_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()


@tag("selenium")
class ObjectDropdowmSeleniumTest(ObjectSeleniumBase):

    def test_view_material_dropdown(self):
        """Test viewing the material dropdown in laboratory navbar.

        Flow: Navigate to lab index -> Click Objects dropdown ->
        Select Material sub-item.

        GIF: docs/source/_static/gif/view_material_dropdown.gif
        """
        self.navigate_to_lab_index()
        path_list = [
            {
                "path": "//a[contains(@href, '/object/list')]",
            },
        ]
        self.create_gif_process(path_list, "view_material_dropdown")

    def test_view_reactive_dropdown(self):
        """Test viewing the reactive link in laboratory index page.

        Flow: Navigate to lab index -> Click Reactive link.

        GIF: docs/source/_static/gif/view_reactive_dropdown.gif
        """
        self.navigate_to_lab_index()
        path_list = [
            {
                "path": "//li[contains(@class, 'list-group-item')]//a[contains(@href, '/sustance')]",
            },
        ]
        self.create_gif_process(path_list, "view_reactive_dropdown")


@tag("selenium")
class ObjectSeleniumTest(ObjectSeleniumBase):

    def test_view_material_dropdown(self):
        """Test navigating to materials from lab index page.

        Flow: Navigate to lab index -> Click 'Material' link in
        administration list.

        GIF: docs/source/_static/gif/view_materials.gif
        """
        self.navigate_to_lab_index()
        path_list = [
            {
                "path": "//a[contains(@href, '/object/list')]",
            },
        ]
        self.create_gif_process(path_list, "view_materials")

    @modifies_db
    def test_add_object_material(self):
        """Test creating a new material object via modal.

        Flow: Navigate to object view -> Click create button in DataTable
        toolbar -> Fill modal form (code, name, synonym, description) -> Save.

        GIF: docs/source/_static/gif/add_material_object.gif
        """
        self.navigate_to_object_view()
        path_list = [
            {
                "path": "//*[@id='table_wrapper']//button[contains(@class, 'btn-outline-success')]",
                "sleep": 1,
            },
            {
                "path": "//input[@id='id_create-code']",
                "extra_action": "clearinput",
                "sleep": 1,
            },
            {
                "path": "//input[@id='id_create-code']",
                "extra_action": "setvalue",
                "value": "CE-456",
            },
            {
                "path": "//input[@id='id_create-name']",
                "extra_action": "clearinput",
            },
            {
                "path": "//input[@id='id_create-name']",
                "extra_action": "setvalue",
                "value": "BEA143 Beakers 50 mL",
            },
            {
                "path": "//input[@id='id_create-synonym']",
                "extra_action": "clearinput",
            },
            {
                "path": "//textarea[@id='id_create-description']",
                "extra_action": "clearinput",
            },
            {
                "path": "//textarea[@id='id_create-description']",
                "extra_action": "setvalue",
                "value": "Un vaso de precipitado es un recipiente cilíndrico de vidrio borosilicatado fino que se utiliza muy comúnmente ",
            },
            {
                "path": "//*[@id='create_obj_modal']//button[contains(@class, 'btn-primary')]",
                "scroll": "$('#create_obj_modal .modal-body').scrollTop(350)",
            },
        ]
        self.create_gif_process(path_list, "add_material_object")

    @modifies_db
    def test_edit_object_material(self):
        """Test editing an existing material object via DataTable and modal.

        Flow: Navigate to object view -> Click edit icon on first row ->
        Modify fields in update modal -> Save.

        GIF: docs/source/_static/gif/update_material_object.gif
        """
        self.navigate_to_object_view()
        path_list = [
            {
                "path": "//*[@id='table']//tbody/tr[1]//i[contains(@class, 'fa-edit')]",
                "screenshot_name": "material_object",
                "sleep": 1,
            },
            {
                "path": "//input[@id='id_update-code']",
                "extra_action": "clearinput",
                "sleep": 1,
            },
            {
                "path": "//input[@id='id_update-code']",
                "extra_action": "setvalue",
                "value": "CE-456",
            },
            {
                "path": "//input[@id='id_update-name']",
                "extra_action": "clearinput",
            },
            {
                "path": "//input[@id='id_update-name']",
                "extra_action": "setvalue",
                "value": "BEA143 Beakers 50 mL",
            },
            {
                "path": "//input[@id='id_update-synonym']",
                "extra_action": "clearinput",
            },
            {
                "path": "//textarea[@id='id_update-description']",
                "extra_action": "clearinput",
            },
            {
                "path": "//textarea[@id='id_update-description']",
                "extra_action": "setvalue",
                "value": "Un vaso de precipitado es un recipiente cilíndrico de vidrio borosilicatado fino que se utiliza muy comúnmente ",
            },
            {
                "path": "//*[@id='update_obj_modal']//button[contains(@class, 'btn-primary')]",
                "scroll": "$('#update_obj_modal .modal-body').scrollTop(350)",
            },
        ]
        self.create_gif_process(path_list, "update_material_object")

    @modifies_db
    def test_add_object_material_is_container(self):
        """Test creating a material object that is a container via modal.

        Flow: Navigate to object view -> Click create -> Fill form
        with container-specific fields (is_container, capacity,
        capacity_measurement_unit) -> Save.

        GIF: docs/source/_static/gif/add_material_container_object.gif
        """
        self.navigate_to_object_view()
        path_list = [
            {
                "path": "//*[@id='table_wrapper']//button[contains(@class, 'btn-outline-success')]",
                "sleep": 1,
            },
            {
                "path": "//input[@id='id_create-code']",
                "extra_action": "clearinput",
                "sleep": 1,
            },
            {
                "path": "//input[@id='id_create-code']",
                "extra_action": "setvalue",
                "value": "CE-456",
            },
            {
                "path": "//input[@id='id_create-name']",
                "extra_action": "clearinput",
            },
            {
                "path": "//input[@id='id_create-name']",
                "extra_action": "setvalue",
                "value": "BEA143 Beakers 50 mL",
            },
            {
                "path": "//input[@id='id_create-synonym']",
                "extra_action": "clearinput",
            },
            {
                "path": "//textarea[@id='id_create-description']",
                "extra_action": "clearinput",
            },
            {
                "path": "//textarea[@id='id_create-description']",
                "extra_action": "setvalue",
                "value": "Un vaso de precipitado es un recipiente cilíndrico de vidrio borosilicatado fino que se utiliza muy comúnmente ",
                "scroll": "$('#create_obj_modal .modal-body').scrollTop(200)",
            },
            {
                "path": "//*[@id='create_obj_modal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": "$('#id_create-is_container').prop('checked', true).trigger('change'); $('.is_container').show();",
                "sleep": 1,
            },
            {
                "path": "//*[@id='create_obj_modal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": "$('#id_create-capacity').val(40);",
                "scroll": "$('#create_obj_modal .modal-body').scrollTop(300)",
            },
            {
                "path": "//select[@id='id_create-capacity_measurement_unit']/..//span[contains(@class, 'select2-selection')]",
                "scroll": "$('#create_obj_modal .modal-body').scrollTop(350)",
            },
            {
                "path": "//ul[contains(@class, 'select2-results__options')]/li[1]",
            },
            {
                "path": "//*[@id='create_obj_modal']//button[contains(@class, 'btn-primary')]",
                "scroll": "$('#create_obj_modal .modal-body').scrollTop(500)",
            },
        ]
        self.create_gif_process(path_list, "add_material_container_object")

    @modifies_db
    def test_delete_material(self):
        """Test deleting a material object via DataTable and modal.

        Flow: Navigate to object view -> Click delete icon on first
        row -> Confirm deletion in modal.

        GIF: docs/source/_static/gif/delete_material_object.gif
        """
        self.navigate_to_object_view()
        path_list = [
            {
                "path": "//*[@id='table']//tbody/tr[1]//i[contains(@class, 'fa-trash')]",
                "sleep": 1,
            },
            {
                "path": "//*[@id='delete_obj_modal']//button[contains(@class, 'btn-primary')]",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list, "delete_material_object")

    def test_view_material(self):
        """Test searching for materials using the DataTable search.

        Flow: Navigate to object view -> Enter search term 'Balones' ->
        Clear and search again with 'Ba'.

        GIF: docs/source/_static/gif/search_material_object.gif
        """
        self.navigate_to_object_view()
        path_list = [
            {
                "path": "//*[@id='table_filter']//input | //input[@type='search']",
                "extra_action": "clearinput",
                "wait_ready": True,
            },
            {
                "path": "//*[@id='table_filter']//input | //input[@type='search']",
                "extra_action": "setvalue",
                "value": "Balones",
            },
            {
                "path": "//*[@id='table_filter']//input | //input[@type='search']",
                "extra_action": "clearinput",
                "sleep": 1,
            },
            {
                "path": "//*[@id='table_filter']//input | //input[@type='search']",
                "extra_action": "setvalue",
                "value": "Ba",
            },
        ]
        self.create_gif_process(path_list, "search_material_object")

    def test_view_reactive(self):
        """Test viewing the reactive/substance list.

        Flow: Navigate to substance list -> Verify page content.

        GIF: docs/source/_static/gif/view_reactive_objects.gif
        """
        self.navigate_to_substance_list()
        path_list = [
            {
                "path": "//body",
                "screenshot_name": "reactive_object",
                "extra_action": "script",
                "value": "",
            },
        ]
        self.create_gif_process(path_list, "view_reactive_objects")

    @modifies_db
    def test_add_reactive_object(self):
        """Test creating a new reactive/substance object via modal.

        Flow: Navigate to substance list -> Click create button -> Fill
        substance form (name, code, synonym, description,
        molecular formula, CAS, model, serie, plaque) -> Save.

        GIF: docs/source/_static/gif/add_reactive_object.gif
        """
        self.navigate_to_substance_list()
        path_list = [
            {
                "path": "//*[@id='reactive_table_wrapper']//button[contains(@class, 'btn-outline-success')]",
                "sleep": 1,
            },
            {
                "path": "//input[@id='id_create-name']",
                "extra_action": "setvalue",
                "value": "BEA143 Beakers 50 mL",
                "sleep": 1,
            },
            {
                "path": "//input[@id='id_create-synonym']",
                "extra_action": "setvalue",
                "value": "ss454",
            },
            {
                "path": "//input[@id='id_create-code']",
                "extra_action": "setvalue",
                "value": "CE-456",
            },
            {
                "path": "//textarea[@id='id_create-description']",
                "extra_action": "setvalue",
                "value": "Un vaso de precipitado es un recipiente cilíndrico de vidrio borosilicatado fino que se utiliza muy comúnmente ,",
                "scroll": "$('#create_obj_modal .modal-body').scrollTop(400)",
            },
            {
                "path": "//input[@id='id_create-molecular_formula']",
                "extra_action": "setvalue",
                "value": "AE2",
            },
            {
                "path": "//input[@id='id_create-cas_id_number']",
                "extra_action": "setvalue",
                "value": "12633468",
            },
            {
                "path": "//input[@id='id_create-model']",
                "extra_action": "setvalue",
                "value": "CA-546",
                "scroll": "$('#create_obj_modal .modal-body').scrollTop(600)",
            },
            {
                "path": "//input[@id='id_create-serie']",
                "extra_action": "setvalue",
                "value": "B54897",
            },
            {
                "path": "//input[@id='id_create-plaque']",
                "extra_action": "setvalue",
                "value": "5634646465",
            },
            {
                "path": "//*[@id='create_obj_modal']//button[contains(@class, 'btn-primary')]",
                "scroll": "$('#create_obj_modal .modal-body').scrollTop(800)",
            },
        ]
        self.create_gif_process(path_list, "add_reactive_object")

    @modifies_db
    def test_edit_reactive_object(self):
        """Test editing an existing reactive/substance object via modal.

        Flow: Navigate to substance list -> Click edit icon on first
        row -> Modify fields in update modal -> Save.

        GIF: docs/source/_static/gif/update_reactive_object.gif
        """
        self.navigate_to_substance_list()
        path_list = [
            {
                "path": "//*[@id='reactive_table']//tbody/tr[1]//i[contains(@class, 'fa-edit')]",
                "sleep": 1,
            },
            {
                "path": "//input[@id='id_update-name']",
                "extra_action": "clearinput",
                "sleep": 1,
            },
            {
                "path": "//input[@id='id_update-name']",
                "extra_action": "setvalue",
                "value": "BEA143 Beakers 50 mL",
            },
            {
                "path": "//input[@id='id_update-synonym']",
                "extra_action": "clearinput",
            },
            {
                "path": "//input[@id='id_update-synonym']",
                "extra_action": "setvalue",
                "value": "ss454",
            },
            {
                "path": "//input[@id='id_update-code']",
                "extra_action": "clearinput",
            },
            {
                "path": "//input[@id='id_update-code']",
                "extra_action": "setvalue",
                "value": "CE-456",
            },
            {
                "path": "//textarea[@id='id_update-description']",
                "extra_action": "clearinput",
            },
            {
                "path": "//textarea[@id='id_update-description']",
                "extra_action": "setvalue",
                "value": "Un vaso de precipitado es un recipiente cilíndrico de vidrio borosilicatado fino que se utiliza muy comúnmente ,",
                "scroll": "$('#update_obj_modal .modal-body').scrollTop(400)",
            },
            {
                "path": "//input[@id='id_update-molecular_formula']",
                "extra_action": "clearinput",
            },
            {
                "path": "//input[@id='id_update-molecular_formula']",
                "extra_action": "setvalue",
                "value": "AE2",
            },
            {
                "path": "//input[@id='id_update-cas_id_number']",
                "extra_action": "clearinput",
            },
            {
                "path": "//input[@id='id_update-cas_id_number']",
                "extra_action": "setvalue",
                "value": "12633468",
            },
            {
                "path": "//*[@id='update_obj_modal']//button[contains(@class, 'btn-primary')]",
                "scroll": "$('#update_obj_modal .modal-body').scrollTop(600)",
            },
        ]
        self.create_gif_process(path_list, "update_reactive_object")

    @modifies_db
    def test_delete_reactive(self):
        """Test deleting a reactive/substance object via modal.

        Flow: Navigate to substance list -> Click delete icon on first
        row -> Confirm deletion in modal.

        GIF: docs/source/_static/gif/delete_reactive_object.gif
        """
        self.navigate_to_substance_list()
        path_list = [
            {
                "path": "//*[@id='reactive_table']//tbody/tr[1]//i[contains(@class, 'fa-trash')]",
                "sleep": 1,
            },
            {
                "path": "//*[@id='delete_obj_modal']//button[contains(@class, 'btn-primary')]",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list, "delete_reactive_object")

    def test_search_reactive(self):
        """Test searching for reactive objects using the DataTable search.

        Flow: Navigate to substance list -> Type 'Alcohol' in search
        input -> Verify filtered results.

        GIF: docs/source/_static/gif/search_reactive_object.gif
        """
        self.navigate_to_substance_list()
        path_list = [
            {
                "path": "//input[@type='search']",
                "extra_action": "clearinput",
                "wait_ready": True,
            },
            {
                "path": "//input[@type='search']",
                "extra_action": "setvalue",
                "value": "Alcohol",
            },
        ]
        self.create_gif_process(path_list, "search_reactive_object")


@tag("selenium")
class ObjectFeaturesSeleniumTest(ObjectSeleniumBase):

    def test_view_object_features(self):
        """Test viewing the object features page.

        Flow: Navigate to object features -> Verify DataTable and
        features list are visible.

        GIF: docs/source/_static/gif/view_object_features.gif
        """
        self.navigate_to_object_features()
        path_list = [
            {
                "path": "//body",
                "screenshot_name": "object_features_view",
            },
        ]
        self.create_gif_process(path_list, "view_object_features")

    def test_view_object_features_dropdown(self):
        """Test navigating to object features via the lab index page.

        Flow: Navigate to lab index -> Click 'Object features' link.

        GIF: docs/source/_static/gif/view_object_features_dropdown.gif
        """
        self.navigate_to_lab_index()
        path_list = [
            {
                "path": "//li[contains(@class, 'list-group-item')]//a[contains(@href, '/features/list')]",
            },
        ]
        self.create_gif_process(path_list, "view_object_features_dropdown")

    @modifies_db
    def test_add_object_features(self):
        """Test adding a new object feature via DataTable modal.

        Flow: Navigate to object features -> Click create button ->
        Fill name and description in modal -> Save.

        GIF: docs/source/_static/gif/view_object_features.gif
        """
        self.navigate_to_object_features()
        path_list = [
            {
                "path": "//*[@id='table_wrapper']//button[contains(@class, 'btn-outline-success')]",
                "sleep": 1,
            },
            {
                "path": "//input[@id='id_create-name']",
                "extra_action": "clearinput",
                "sleep": 1,
            },
            {
                "path": "//input[@id='id_create-name']",
                "extra_action": "setvalue",
                "value": "Química Orgánica",
            },
            {
                "path": "//textarea[@id='id_create-description']",
                "extra_action": "clearinput",
            },
            {
                "path": "//textarea[@id='id_create-description']",
                "extra_action": "setvalue",
                "value": "Objetos exclusivos o representativos de la disciplina de quimica orgánica, ejemplo : equipo especial para síntesis.",
            },
            {
                "path": "//*[@id='create_obj_modal']//button[contains(@class, 'btn-primary')]",
            },
        ]
        self.create_gif_process(path_list, "view_object_features")

    @modifies_db
    def test_edit_object_features(self):
        """Test editing an existing object feature via DataTable modal.

        Flow: Navigate to object features -> Click edit icon on first
        row -> Update name and description in modal -> Save.

        GIF: docs/source/_static/gif/view_object_features.gif
        """
        self.navigate_to_object_features()
        path_list = [
            {
                "path": "//*[@id='table']//tbody/tr[1]//i[contains(@class, 'fa-edit')]",
                "sleep": 1,
            },
            {
                "path": "//input[@id='id_update-name']",
                "extra_action": "clearinput",
                "sleep": 1,
            },
            {
                "path": "//input[@id='id_update-name']",
                "extra_action": "setvalue",
                "value": "Química Orgánica",
            },
            {
                "path": "//textarea[@id='id_update-description']",
                "extra_action": "clearinput",
            },
            {
                "path": "//textarea[@id='id_update-description']",
                "extra_action": "setvalue",
                "value": "Objetos exclusivos o representativos de la disciplina de quimica orgánica, ejemplo : equipo especial para síntesis.",
            },
            {
                "path": "//*[@id='update_obj_modal']//button[contains(@class, 'btn-primary')]",
            },
        ]
        self.create_gif_process(path_list, "view_object_features")

    @modifies_db
    def test_delete_object_features(self):
        """Test deleting an object feature via DataTable modal.

        Flow: Navigate to object features -> Click delete icon on first
        row -> Confirm deletion in modal.

        GIF: docs/source/_static/gif/view_object_features.gif
        """
        self.navigate_to_object_features()
        path_list = [
            {
                "path": "//*[@id='table']//tbody/tr[1]//i[contains(@class, 'fa-trash')]",
                "sleep": 1,
            },
            {
                "path": "//*[@id='delete_obj_modal']//button[contains(@class, 'btn-primary')]",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list, "view_object_features")
