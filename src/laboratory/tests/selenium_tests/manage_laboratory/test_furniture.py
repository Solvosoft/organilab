from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse
from laboratory.models import OrganizationStructure
from organilab_test.tests.base import OptimizedSeleniumBase, modifies_db
from organilab_test.tests.selenium_xpaths import select2_result


@tag("selenium")
class FurnitureSeleniumTest(OptimizedSeleniumBase):
    fixtures = ["selenium/base_selenium.json", "selenium/laboratory_delta.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.org = OrganizationStructure.objects.get(pk=1)
        self.select_org_url = self.live_server_url + str(
            reverse("auth_and_perms:select_organization_by_user")
        )
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )

    @modifies_db
    def test_create_furniture(self):
        self.selenium.get(
            url=self.live_server_url
            + str(reverse("laboratory:labindex", kwargs={"org_pk": 1, "lab_pk": 1}))
        )
        path_list = [
            {"path": "//div[contains(@class, 'right_col')]//a[contains(@href, '/rooms/create')]"},
            {"path": "(//button[@data-bs-target='#furnitureModal'])[1]"},
            {
                "path": "//*[@id='furnitureModal']//input[@id='id_name']",
                "extra_action": "clearinput",
            },
            {
                "path": "//*[@id='furnitureModal']//input[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Generico",
            },
            {"path": "//*[@id='furnitureModal']//span[contains(@class, 'select2-selection')]"},
            {"path": select2_result(1)},
            {"path": "//*[@id='furnitureModal']//button[@type='submit']"},
            {"path": "//*[@id='save_button1']//button[@type='submit']", "wait_ready": True},
        ]
        self.create_gif_process(path_list, "add_furniture")

    @modifies_db
    def test_update_furniture(self):
        self.selenium.get(
            url=self.live_server_url
            + str(reverse("laboratory:labindex", kwargs={"org_pk": 1, "lab_pk": 1}))
        )
        path_list = [
            {"path": "//div[contains(@class, 'right_col')]//a[contains(@href, '/rooms/create')]"},
            {"path": "(//button[@data-bs-toggle='popover'])[1]", "sleep": 1},
            {"path": "(//div[contains(@class, 'popover')]//a)[1]", "sleep": 1},
            {
                "path": "//span[@aria-controls='select2-id_labroom-container']",
                "wait_ready": True,
            },
            {"path": "//span[@aria-controls='select2-id_labroom-container']"},
            {"path": ".//*[@id='id_name']", "extra_action": "clearinput"},
            {
                "path": ".//*[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Generico 2",
            },
            {"path": "//span[@aria-controls='select2-id_type-container']"},
            {"path": "//span[@aria-controls='select2-id_type-container']"},
            {"path": "//*[@id='save_button1']//button[@type='submit']"},
        ]
        self.create_gif_process(path_list, "update_furniture")

    @modifies_db
    def test_move_furniture(self):
        self.selenium.get(
            url=self.live_server_url
            + str(reverse("laboratory:labindex", kwargs={"org_pk": 1, "lab_pk": 1}))
        )
        path_list = [
            {"path": "//div[contains(@class, 'right_col')]//a[contains(@href, '/rooms/create')]"},
            {"path": "(//button[@data-bs-toggle='popover'])[1]", "sleep": 1},
            {"path": "(//div[contains(@class, 'popover')]//a)[1]", "sleep": 1},
            {
                "path": "//span[@aria-controls='select2-id_labroom-container']",
                "wait_ready": True,
            },
            {"path": select2_result(2)},
            {"path": ".//*[@id='id_name']", "extra_action": "clearinput"},
            {
                "path": ".//*[@id='id_name']",
                "extra_action": "setvalue",
                "value": "Generico 2",
            },
            {"path": "//*[@id='save_button1']//button[@type='submit']"},
            {"path": "(//button[@data-bs-toggle='popover'])[2]", "sleep": 1},
        ]
        self.create_gif_process(path_list, "move_furniture")

    @modifies_db
    def test_delete_furniture(self):
        self.selenium.get(
            url=self.live_server_url
            + str(reverse("laboratory:labindex", kwargs={"org_pk": 1, "lab_pk": 1}))
        )
        path_list = [
            {"path": "//div[contains(@class, 'right_col')]//a[contains(@href, '/rooms/create')]"},
            {"path": "(//button[@data-bs-toggle='popover'])[1]", "sleep": 1},
            {"path": "(//div[contains(@class, 'popover')]//a)[1]", "sleep": 1},
            {
                "path": "//a[contains(@class, 'btn-danger') and contains(@href, 'delete')]",
                "wait_ready": True,
            },
            {
                "path": "//input[@type='submit']",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "delete_furniture")

    @modifies_db
    def test_add_furniture_type(self):
        self.selenium.get(
            url=self.live_server_url
            + str(reverse("laboratory:labindex", kwargs={"org_pk": 1, "lab_pk": 1}))
        )
        path_list = [
            {"path": "//div[contains(@class, 'right_col')]//a[contains(@href, '/rooms/create')]"},
            {"path": "(//button[@data-bs-toggle='popover'])[1]", "sleep": 1},
            {"path": "(//div[contains(@class, 'popover')]//a)[1]", "sleep": 1},
            {"path": ".//*[@id='add_type_id']", "wait_ready": True},
            {"path": "//*[@id='modal_type_id']//input | //*[@id='modal_type_id']//textarea", "sleep": 1},
            {
                "path": "//*[@id='modal_type_id']//input[@type='text'] | //*[@id='modal_type_id']//textarea",
                "extra_action": "setvalue",
                "value": "Recolector",
            },
            {"path": "//*[@id='modal_type_id']//button[contains(@class, 'btnsubmit')]"},
        ]
        self.create_gif_process(path_list, "add_furniture_type")
