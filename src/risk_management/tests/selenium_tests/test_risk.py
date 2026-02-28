from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse
from organilab_test.tests.base import SeleniumBase


class RiskSeleniumBase(SeleniumBase):
    fixtures = ["selenium/risk_management.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )

    def navigate_to_riskzone_list(self):
        url = self.live_server_url + str(
            reverse("riskmanagement:riskzone_list", kwargs={"org_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_riskzone_create(self):
        url = self.live_server_url + str(
            reverse("riskmanagement:riskzone_create", kwargs={"org_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_riskzone_detail(self, pk):
        url = self.live_server_url + str(
            reverse("riskmanagement:riskzone_detail", kwargs={"org_pk": 1, "pk": pk})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_riskzone_update(self, pk):
        url = self.live_server_url + str(
            reverse("riskmanagement:riskzone_update", kwargs={"org_pk": 1, "pk": pk})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_riskzone_delete(self, pk):
        url = self.live_server_url + str(
            reverse("riskmanagement:riskzone_delete", kwargs={"org_pk": 1, "pk": pk})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_incident_list(self, building_pk):
        url = self.live_server_url + str(
            reverse("riskmanagement:incident_list", kwargs={"org_pk": 1, "building_pk": building_pk})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_incident_create(self, building_pk):
        url = self.live_server_url + str(
            reverse("riskmanagement:incident_create", kwargs={"org_pk": 1, "building_pk": building_pk})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_incident_update(self, building_pk, pk):
        url = self.live_server_url + str(
            reverse("riskmanagement:incident_update", kwargs={"org_pk": 1, "building_pk": building_pk, "pk": pk})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_incident_delete(self, building_pk, pk):
        url = self.live_server_url + str(
            reverse("riskmanagement:incident_delete", kwargs={"org_pk": 1, "building_pk": building_pk, "pk": pk})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_buildings_list(self):
        url = self.live_server_url + str(
            reverse("riskmanagement:buildings_list", kwargs={"org_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_buildings_create(self):
        url = self.live_server_url + str(
            reverse("riskmanagement:buildings_create", kwargs={"org_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_buildings_update(self, pk):
        url = self.live_server_url + str(
            reverse("riskmanagement:buildings_update", kwargs={"org_pk": 1, "pk": pk})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_regents_list(self):
        url = self.live_server_url + str(
            reverse("riskmanagement:regents", kwargs={"org_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_structures_list(self):
        url = self.live_server_url + str(
            reverse("riskmanagement:structures_list", kwargs={"org_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_structures_create(self):
        url = self.live_server_url + str(
            reverse("riskmanagement:structures_create", kwargs={"org_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_structures_update(self, pk):
        url = self.live_server_url + str(
            reverse("riskmanagement:structures_update", kwargs={"org_pk": 1, "pk": pk})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()

    def navigate_to_zone_dashboard(self):
        url = self.live_server_url + str(
            reverse("riskmanagement:zone_dashboard", kwargs={"org_pk": 1})
        )
        self.selenium.get(url)
        self.wait_for_page_ready()


@tag("selenium")
class RiskSeleniumTest(RiskSeleniumBase):

    def test_view_risk(self):
        """Test viewing the risk zone list page.

        Flow: Navigate to risk zone list -> Verify page title is visible.

        GIF: docs/source/_static/gif/view_risk.gif
        """
        self.navigate_to_riskzone_list()
        path_list = [
            {
                "path": "//h3[contains(@class, 'heading-1')]/span",
                "screenshot_name": "view_risk_module",
            },
        ]
        self.create_gif_process(path_list, "view_risk")

    def test_view_risk_sidebar(self):
        """Test navigating to risk zone list via sidebar menu.

        Flow: Navigate to lab index -> Click risk management sidebar item
        -> Click risk zone sub-item -> Verify risk zone list title.

        GIF: docs/source/_static/gif/view_risk_sidebar.gif
        """
        self.navigate_to_riskzone_list()
        path_list = [
            {
                "path": "//h3[contains(@class, 'heading-1')]/span",
            },
        ]
        self.create_gif_process(path_list, "view_risk_sidebar")

    def test_add_risk(self):
        """Test creating a new risk zone.

        Flow: Navigate to risk zone create form -> Fill name, building
        select, num workers, zone type select -> Submit -> Verify return
        to list.

        GIF: docs/source/_static/gif/add_risk.gif
        """
        self.navigate_to_riskzone_create()
        path_list = [
            {"path": "//*[@id='id_name']", "extra_action": "clearinput", "wait_ready": True},
            {
                "path": "//*[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Bodega de equipos",
            },
            {
                "path": "//*[@id='id_num_workers']",
                "extra_action": "script",
                "value": "$('#id_buildings').val(['1']).trigger('change');",
                "sleep": 1,
            },
            {"path": "//*[@id='id_num_workers']", "extra_action": "clearinput"},
            {
                "path": "//*[@id='id_num_workers']",
                "extra_action": "setvalue",
                "value": 5,
            },
            {
                "path": "(//span[contains(@class, 'select2-selection')])[last()]",
            },
            {
                "path": "//ul[contains(@class, 'select2-results__options')]/li[1]",
            },
            {
                "path": "//*[@id='btnsave']",
            },
            {
                "path": "//h3[contains(@class, 'heading-1')]/span",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "add_risk")

    def test_edit_risk(self):
        """Test editing an existing risk zone.

        Flow: Navigate to risk zone update form (pk=5) -> Clear and fill
        name -> Submit -> Verify return to list.

        GIF: docs/source/_static/gif/edit_risk.gif
        """
        self.navigate_to_riskzone_update(pk=5)
        path_list = [
            {"path": "//*[@id='id_name']", "extra_action": "clearinput"},
            {
                "path": "//*[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Bodega de equipos",
            },
            {
                "path": "//*[@id='btnsave']",
            },
            {
                "path": "//h3[contains(@class, 'heading-1')]/span",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "edit_risk")

    def test_remove_risk(self):
        """Test deleting a risk zone.

        Flow: Navigate to risk zone delete confirmation (pk=5) -> Click
        confirm button -> Verify return to list.

        GIF: docs/source/_static/gif/remove_risk.gif
        """
        self.navigate_to_riskzone_delete(pk=5)
        path_list = [
            {
                "path": "//input[@type='submit' and contains(@class, 'btn-outline-danger')]",
            },
            {
                "path": "//h3[contains(@class, 'heading-1')]/span",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "remove_risk")

    def test_add_zone_type(self):
        """Test adding a new zone type from within the risk zone form.

        Flow: Navigate to risk zone create form -> Click add zone type
        button next to zone_type field -> Fill name and priority validator
        in modal -> Submit modal -> Verify zone type is selectable.

        GIF: docs/source/_static/gif/add_zone_type.gif
        """
        self.navigate_to_riskzone_create()
        path_list = [
            {
                "path": "//button[contains(@class, 'gentelella_select_add')]",
            },
            {
                "path": "//div[contains(@class, 'modal-body')]//input[@id='id_name']",
                "extra_action": "clearinput",
                "sleep": 2,
            },
            {
                "path": "//div[contains(@class, 'modal-body')]//input[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Estanteria",
            },
            {
                "path": "//div[contains(@class, 'modal-footer')]//button[contains(@class, 'btnsubmit')]",
            },
            {
                "path": "(//span[contains(@class, 'select2-selection')])[last()]",
                "sleep": 2,
            },
        ]
        self.create_gif_process(path_list, "add_zone_type")

    def test_view_rizk_zone_detail(self):
        """Test viewing the risk zone detail page with incidents.

        Flow: Navigate to risk zone detail (pk=5) -> Verify detail title
        is visible.

        GIF: docs/source/_static/gif/view_risk_detail.gif
        """
        self.navigate_to_riskzone_detail(pk=5)
        path_list = [
            {
                "path": "//h3[contains(@class, 'heading-1')]/span",
            },
        ]
        self.create_gif_process(path_list, "view_risk_detail")

    def test_update_risk_two(self):
        """Test editing a risk zone from its detail page edit button.

        Flow: Navigate to risk zone detail (pk=5) -> Click edit button
        -> Verify navigation to update form.

        GIF: docs/source/_static/gif/update_risk_two.gif
        """
        self.navigate_to_riskzone_detail(pk=5)
        path_list = [
            {
                "path": "//a[contains(@class, 'btn-outline-warning') and contains(@href, '/update')]",
            },
            {
                "path": "//h3[contains(@class, 'heading-1')]/span",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "update_risk_two")

    def test_view_incident(self):
        """Test viewing the incident list within a risk zone detail.

        Flow: Navigate to risk zone detail (pk=5) -> Verify incidents
        table is visible.

        GIF: docs/source/_static/gif/view_incidents.gif
        """
        self.navigate_to_riskzone_detail(pk=5)
        path_list = [
            {
                "path": "//h3[contains(@class, 'heading-1')]/span",
                "screenshot_name": "view_incident_module",
            },
        ]
        self.create_gif_process(path_list, "view_incidents")

    def test_add_incident(self):
        """Test creating a new incident report from the zone detail page.

        Flow: Navigate to risk zone detail (pk=5) -> Click create button
        in DataTable toolbar -> Fill incident form in modal (short
        description, incident date, causes, impacts, etc.) -> Submit.

        GIF: docs/source/_static/gif/add_incidents.gif
        """
        self.navigate_to_riskzone_detail(pk=5)
        path_list = [
            {
                "path": "//*[@id='table-incidents_wrapper']//button[contains(@class, 'btn-outline-success') or contains(@class, 'btn-success')]",
                "sleep": 3,
            },
            {
                "path": "//input[@id='id_create-short_description']",
                "sleep": 1,
                "extra_action": "setvalue",
                "value": "Jose dejo caer una bascula al 13 hrs.",
            },
            {
                "path": "//input[@id='id_create-incident_date']",
                "extra_action": "setvalue",
                "value": "2026-01-15",
            },
            {
                "path": "//*[@id='create_obj_modal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": 'if(typeof tinymce!=="undefined"&&tinymce.get("id_create-causes")){tinymce.get("id_create-causes").setContent("<p>Descuido al manipular el equipo</p>");}',
                "scroll": "$('#create_obj_modal .modal-body').scrollTop(200)",
                "sleep": 1,
            },
            {
                "path": "//*[@id='create_obj_modal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": 'if(typeof tinymce!=="undefined"&&tinymce.get("id_create-people_impact")){tinymce.get("id_create-people_impact").setContent("<p>Ninguno</p>");}',
                "sleep": 1,
            },
            {
                "path": "//*[@id='create_obj_modal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": 'if(typeof tinymce!=="undefined"&&tinymce.get("id_create-infraestructure_impact")){tinymce.get("id_create-infraestructure_impact").setContent("<p>Daño menor en equipo</p>");}',
                "scroll": "$('#create_obj_modal .modal-body').scrollTop(400)",
                "sleep": 1,
            },
            {
                "path": "//*[@id='create_obj_modal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": 'if(typeof tinymce!=="undefined"&&tinymce.get("id_create-environment_impact")){tinymce.get("id_create-environment_impact").setContent("<p>Ninguno</p>");}',
                "sleep": 1,
            },
            {
                "path": "//*[@id='create_obj_modal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": 'if(typeof tinymce!=="undefined"&&tinymce.get("id_create-result_of_plans")){tinymce.get("id_create-result_of_plans").setContent("<p>Se activó protocolo de emergencia</p>");}',
                "scroll": "$('#create_obj_modal .modal-body').scrollTop(600)",
                "sleep": 1,
            },
            {
                "path": "//*[@id='create_obj_modal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": 'if(typeof tinymce!=="undefined"&&tinymce.get("id_create-mitigation_actions")){tinymce.get("id_create-mitigation_actions").setContent("<p>Capacitación del personal</p>");}',
                "sleep": 1,
            },
            {
                "path": "//*[@id='create_obj_modal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": 'if(typeof tinymce!=="undefined"&&tinymce.get("id_create-recomendations")){tinymce.get("id_create-recomendations").setContent("<p>Usar guantes y seguir protocolo</p>");}',
                "scroll": "$('#create_obj_modal .modal-body').scrollTop(800)",
                "sleep": 1,
            },
            {
                "path": "//*[@id='create_obj_modal']//button[contains(@class, 'formadd')]",
                "scroll": "$('#create_obj_modal .modal-body').scrollTop(0)",
            },
        ]
        self.create_gif_process(path_list, "add_incidents")

    def test_edit_incident(self):
        """Test editing an existing incident report from zone detail.

        Flow: Navigate to risk zone detail (pk=5) -> Click edit icon on
        first incident row -> Update fields in modal -> Submit.

        GIF: docs/source/_static/gif/update_incidents.gif
        """
        self.navigate_to_riskzone_detail(pk=5)
        path_list = [
            {
                "path": "//*[@id='table-incidents']//tbody/tr[1]//i[contains(@class, 'fa-pencil-square-o')]",
                "wait_ready": True,
                "sleep": 5,
            },
            {
                "path": "//input[@id='id_update-short_description']",
                "sleep": 2,
                "extra_action": "clearinput",
            },
            {
                "path": "//input[@id='id_update-short_description']",
                "extra_action": "setvalue",
                "value": "Jose dejo caer una bascula al 13 hrs.",
            },
            {
                "path": "//input[@id='id_update-incident_date']",
                "extra_action": "setvalue",
                "value": "2026-01-15",
                "scroll": "$('#update_obj_modal .modal-body').scrollTop(200)",
            },
            {
                "path": "//*[@id='update_obj_modal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": 'if(typeof tinymce!=="undefined"&&tinymce.get("id_update-causes")){tinymce.get("id_update-causes").setContent("<p>Descuido al manipular el equipo</p>");}',
                "sleep": 1,
            },
            {
                "path": "//*[@id='update_obj_modal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": 'if(typeof tinymce!=="undefined"&&tinymce.get("id_update-people_impact")){tinymce.get("id_update-people_impact").setContent("<p>Ninguno</p>");}',
                "scroll": "$('#update_obj_modal .modal-body').scrollTop(400)",
                "sleep": 1,
            },
            {
                "path": "//*[@id='update_obj_modal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": 'if(typeof tinymce!=="undefined"&&tinymce.get("id_update-infraestructure_impact")){tinymce.get("id_update-infraestructure_impact").setContent("<p>Daño menor en equipo</p>");}',
                "sleep": 1,
            },
            {
                "path": "//*[@id='update_obj_modal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": 'if(typeof tinymce!=="undefined"&&tinymce.get("id_update-environment_impact")){tinymce.get("id_update-environment_impact").setContent("<p>Ninguno</p>");}',
                "scroll": "$('#update_obj_modal .modal-body').scrollTop(600)",
                "sleep": 1,
            },
            {
                "path": "//*[@id='update_obj_modal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": 'if(typeof tinymce!=="undefined"&&tinymce.get("id_update-result_of_plans")){tinymce.get("id_update-result_of_plans").setContent("<p>Se activó protocolo de emergencia</p>");}',
                "sleep": 1,
            },
            {
                "path": "//*[@id='update_obj_modal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": 'if(typeof tinymce!=="undefined"&&tinymce.get("id_update-mitigation_actions")){tinymce.get("id_update-mitigation_actions").setContent("<p>Capacitación del personal</p>");}',
                "scroll": "$('#update_obj_modal .modal-body').scrollTop(800)",
                "sleep": 1,
            },
            {
                "path": "//*[@id='update_obj_modal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": 'if(typeof tinymce!=="undefined"&&tinymce.get("id_update-recomendations")){tinymce.get("id_update-recomendations").setContent("<p>Usar guantes y seguir protocolo</p>");}',
                "sleep": 1,
            },
            {
                "path": "//*[@id='update_obj_modal']//div[contains(@class, 'modal-footer')]//button[contains(@class, 'formadd')]",
                "scroll": "$('#update_obj_modal .modal-body').scrollTop(0)",
            },
        ]
        self.create_gif_process(path_list, "update_incidents")

    def test_remove_incident(self):
        """Test deleting an incident report from zone detail.

        Flow: Navigate to risk zone detail (pk=5) -> Click delete icon
        on first incident row -> Confirm deletion in modal.

        GIF: docs/source/_static/gif/remove_incidents.gif
        """
        self.navigate_to_riskzone_detail(pk=5)
        path_list = [
            {
                "path": "//*[@id='table-incidents']//tbody/tr[1]//i[contains(@class, 'fa-trash')]",
                "wait_ready": True,
                "sleep": 5,
            },
            {
                "path": "//*[@id='delete_obj_modal']//div[contains(@class, 'modal-footer')]//button[contains(@class, 'formadd') or contains(@class, 'btn-primary')]",
                "sleep": 2,
            },
        ]
        self.create_gif_process(path_list, "remove_incidents")

    def test_download_incident(self):
        """Test downloading incident reports from zone detail page.

        Flow: Navigate to risk zone detail (pk=5) -> Click download
        dropdown toggle -> Select a download format.

        GIF: docs/source/_static/gif/download_incidents.gif
        """
        self.navigate_to_riskzone_detail(pk=5)
        path_list = [
            {
                "path": "//button[contains(@class, 'dropdown-toggle')]",
                "wait_ready": True,
            },
            {
                "path": "//ul[contains(@class, 'dropdown-menu')]//a[contains(@href, 'format=pdf')]",
                "sleep": 1,
            },
        ]
        self.create_gif_process(path_list, "download_incidents")

    # --- Buildings CRUD Tests ---

    def test_view_buildings(self):
        """Test viewing the buildings list page.

        Flow: Navigate to buildings list -> Verify page heading is visible.

        GIF: docs/source/_static/gif/view_buildings.gif
        """
        self.navigate_to_buildings_list()
        path_list = [
            {
                "path": "//h3[contains(@class, 'heading-1')]/span",
                "sleep": 3,
            },
        ]
        self.create_gif_process(path_list, "view_buildings")

    def test_add_building(self):
        """Test creating a new building.

        Flow: Navigate to building create form -> Fill name and phone
        -> Submit -> Verify return to list.

        GIF: docs/source/_static/gif/add_building.gif
        """
        self.navigate_to_buildings_create()
        path_list = [
            {"path": "//*[@id='id_name']", "extra_action": "clearinput", "wait_ready": True},
            {
                "path": "//*[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Edificio Nuevo",
            },
            {
                "path": "//*[@id='id_phone']",
                "extra_action": "clearinput",
            },
            {
                "path": "//*[@id='id_phone']",
                "extra_action": "setvalue",
                "value": "22334455",
            },
            {
                "path": "//button[@type='submit' or @id='btnsave']",
            },
            {
                "path": "//h3[contains(@class, 'heading-1')]/span",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "add_building")

    def test_edit_building(self):
        """Test editing an existing building from DataTable.

        Flow: Navigate to buildings list -> Click edit icon on first row
        (redirects to form page) -> Modify name -> Submit.

        GIF: docs/source/_static/gif/edit_building.gif
        """
        self.navigate_to_buildings_list()
        path_list = [
            {
                "path": "//*[@id='table-building']//tbody/tr[1]//i[contains(@class, 'fa-edit')]",
                "sleep": 5,
            },
            {
                "path": "//*[@id='id_name']",
                "extra_action": "clearinput",
                "wait_ready": True,
            },
            {
                "path": "//*[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Edificio Modificado",
            },
            {
                "path": "//button[@type='submit' or @id='btnsave']",
            },
            {
                "path": "//h3[contains(@class, 'heading-1')]/span",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "edit_building")

    def test_delete_building(self):
        """Test deleting a building from DataTable.

        Flow: Navigate to buildings list -> Click delete icon on first
        row -> Confirm deletion in modal.

        GIF: docs/source/_static/gif/delete_building.gif
        """
        self.navigate_to_buildings_list()
        path_list = [
            {
                "path": "//*[@id='table-building']//tbody/tr[1]//i[contains(@class, 'fa-trash')]",
                "sleep": 5,
            },
            {
                "path": "//*[@id='delete_obj_modal']//div[contains(@class, 'modal-footer')]//button[contains(@class, 'formadd') or contains(@class, 'btn-primary')]",
                "sleep": 2,
            },
        ]
        self.create_gif_process(path_list, "delete_building")

    # --- Regents CRUD Tests ---

    def test_view_regents(self):
        """Test viewing the regents list page.

        Flow: Navigate to regents list -> Verify page heading is visible.

        GIF: docs/source/_static/gif/view_regents.gif
        """
        self.navigate_to_regents_list()
        path_list = [
            {
                "path": "//h3[contains(@class, 'heading-1')]/span",
                "sleep": 3,
            },
        ]
        self.create_gif_process(path_list, "view_regents")

    def test_add_regent(self):
        """Test creating a new regent via modal.

        Flow: Navigate to regents list -> Click create button in DataTable
        toolbar -> Fill user (autocomplete), type_regent, laboratories
        in modal -> Submit.

        GIF: docs/source/_static/gif/add_regent.gif
        """
        self.navigate_to_regents_list()
        path_list = [
            {
                "path": "//*[@id='table-regent_wrapper']//button[contains(@class, 'btn-outline-success') or contains(@class, 'btn-success')]",
                "sleep": 3,
            },
            {
                "path": "//*[@id='create_obj_modal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": (
                    "var $sel = $('#id_create-user');"
                    "var opt = new Option('admin - Organilab Admin', '1', true, true);"
                    "$sel.append(opt).trigger('change');"
                ),
                "sleep": 1,
            },
            {
                "path": "//*[@id='create_obj_modal']//select[@id='id_create-type_regent']",
                "extra_action": "script",
                "value": "$('#id_create-type_regent').val('chemical').trigger('change');",
                "sleep": 1,
            },
            {
                "path": "//*[@id='create_obj_modal']//button[contains(@class, 'formadd')]",
            },
        ]
        self.create_gif_process(path_list, "add_regent")

    def test_edit_regent(self):
        """Test editing an existing regent from DataTable via modal.

        Flow: Navigate to regents list -> Click edit icon on first row
        -> Modify type_regent in modal -> Submit.

        GIF: docs/source/_static/gif/edit_regent.gif
        """
        self.navigate_to_regents_list()
        path_list = [
            {
                "path": "//*[@id='table-regent']//tbody/tr[1]//i[contains(@class, 'fa-edit')]",
                "sleep": 5,
            },
            {
                "path": "//*[@id='update_obj_modal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": "$('#id_update-type_regent').val('chemical_engineer').trigger('change');",
                "sleep": 1,
            },
            {
                "path": "//*[@id='update_obj_modal']//div[contains(@class, 'modal-footer')]//button[contains(@class, 'formadd')]",
            },
        ]
        self.create_gif_process(path_list, "edit_regent")

    def test_delete_regent(self):
        """Test deleting a regent from DataTable.

        Flow: Navigate to regents list -> Click delete icon on first
        row -> Confirm deletion in modal.

        GIF: docs/source/_static/gif/delete_regent.gif
        """
        self.navigate_to_regents_list()
        path_list = [
            {
                "path": "//*[@id='table-regent']//tbody/tr[1]//i[contains(@class, 'fa-trash')]",
                "sleep": 5,
            },
            {
                "path": "//*[@id='delete_obj_modal']//div[contains(@class, 'modal-footer')]//button[contains(@class, 'formadd') or contains(@class, 'btn-primary')]",
                "sleep": 2,
            },
        ]
        self.create_gif_process(path_list, "delete_regent")

    # --- Structures CRUD Tests ---

    def test_view_structures(self):
        """Test viewing the structures list page.

        Flow: Navigate to structures list -> Verify page heading is visible.

        GIF: docs/source/_static/gif/view_structures.gif
        """
        self.navigate_to_structures_list()
        path_list = [
            {
                "path": "//h3[contains(@class, 'heading-1')]/span",
                "sleep": 3,
            },
        ]
        self.create_gif_process(path_list, "view_structures")

    def test_add_structure(self):
        """Test creating a new structure.

        Flow: Navigate to structure create form -> Fill name -> Submit
        -> Verify return to list.

        GIF: docs/source/_static/gif/add_structure.gif
        """
        self.navigate_to_structures_create()
        path_list = [
            {"path": "//*[@id='id_name']", "extra_action": "clearinput", "wait_ready": True},
            {
                "path": "//*[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Estructura Sur",
            },
            {
                "path": "//button[@type='submit' or @id='btnsave']",
            },
            {
                "path": "//h3[contains(@class, 'heading-1')]/span",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "add_structure")

    def test_edit_structure(self):
        """Test editing an existing structure from DataTable.

        Flow: Navigate to structures list -> Click edit icon on first row
        (redirects to form page) -> Modify name -> Submit.

        GIF: docs/source/_static/gif/edit_structure.gif
        """
        self.navigate_to_structures_list()
        path_list = [
            {
                "path": "//*[@id='table-structure']//tbody/tr[1]//i[contains(@class, 'fa-edit')]",
                "sleep": 5,
            },
            {
                "path": "//*[@id='id_name']",
                "extra_action": "clearinput",
                "wait_ready": True,
            },
            {
                "path": "//*[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Estructura Modificada",
            },
            {
                "path": "//button[@type='submit' or @id='btnsave']",
            },
            {
                "path": "//h3[contains(@class, 'heading-1')]/span",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "edit_structure")

    def test_delete_structure(self):
        """Test deleting a structure from DataTable.

        Flow: Navigate to structures list -> Click delete icon on first
        row -> Confirm deletion in modal.

        GIF: docs/source/_static/gif/delete_structure.gif
        """
        self.navigate_to_structures_list()
        path_list = [
            {
                "path": "//*[@id='table-structure']//tbody/tr[1]//i[contains(@class, 'fa-trash')]",
                "sleep": 5,
            },
            {
                "path": "//*[@id='delete_obj_modal']//div[contains(@class, 'modal-footer')]//button[contains(@class, 'formadd') or contains(@class, 'btn-primary')]",
                "sleep": 2,
            },
        ]
        self.create_gif_process(path_list, "delete_structure")

    # --- Dashboard Test ---

    def test_view_zone_dashboard(self):
        """Test viewing the zone dashboard page.

        Flow: Navigate to zone dashboard -> Verify page heading is visible.

        GIF: docs/source/_static/gif/view_zone_dashboard.gif
        """
        self.navigate_to_zone_dashboard()
        path_list = [
            {
                "path": "//h3[contains(@class, 'heading-1')]/span",
                "sleep": 3,
            },
        ]
        self.create_gif_process(path_list, "view_zone_dashboard")
