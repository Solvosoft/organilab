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
            {"path": "//*[@id='id_name']", "extra_action": "clearinput"},
            {
                "path": "//*[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Bodega de equipos",
            },
            {
                "path": "//div[contains(@class, 'form-group')]//span[contains(@class, 'select2-selection')]",
                "sleep": 2,
            },
            {
                "path": "//ul[contains(@class, 'select2-results__options')]/li[1]",
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
                "sleep": 2,
            },
            {
                "path": "//input[@id='id_create-short_description']",
                "sleep": 1,
                "extra_action": "setvalue",
                "value": "Jose dejo caer una bascula al 13 hrs.",
            },
            {
                "path": "//*[@id='create_obj_modal']//button[contains(@class, 'formadd')]",
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
                "path": "//*[@id='table-incidents']//tbody/tr[1]//i[contains(@class, 'fa-edit') or contains(@class, 'fa-pencil')]",
                "wait_ready": True,
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
                "path": "//*[@id='update_obj_modal']//div[contains(@class, 'modal-footer')]//button[contains(@class, 'formadd')]",
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
                "path": "//*[@id='table-incidents']//tbody/tr[1]//i[contains(@class, 'fa-trash') or contains(@class, 'fa-remove')]",
                "wait_ready": True,
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
