from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse
from laboratory.models import OrganizationStructure
from organilab_test.tests.base import OptimizedSeleniumBase, modifies_db
from organilab_test.tests.selenium_xpaths import select2_result


@tag("selenium")
class ShelvesSeleniumTest(OptimizedSeleniumBase):
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
    def test_create_shelf(self):
        self.selenium.get(
            url=self.live_server_url
            + str(reverse("laboratory:labindex", kwargs={"org_pk": 1, "lab_pk": 1}))
        )
        path_list = [
            {"path": "//div[contains(@class, 'right_col')]//a[contains(@href, '/rooms/create')]"},
            {"path": "(//button[@data-bs-toggle='popover'])[1]", "sleep": 1},
            {"path": "(//div[contains(@class, 'popover')]//a)[1]", "sleep": 1},
            {
                "path": "//*[@id='btnAddRow']",
                "screenshot_name": "view_shelves",
            },
            {
                "path": "(//table[@id='mytab']//a[contains(@class, 'btn-success')])[1]",
                "sleep": 1,
            },
            {"path": ".//*[@id='id_shelf--name']", "extra_action": "clearinput"},
            {
                "path": ".//*[@id='id_shelf--name']",
                "extra_action": "setvalue",
                "value": "Primer Estante",
            },
            {"path": "//span[@aria-controls='select2-id_shelf--type-container']"},
            {"path": select2_result(2)},
            {"path": "//span[@aria-controls='select2-id_shelf--measurement_unit-container']"},
            {"path": select2_result(2)},
            {"path": "//*[@id='createshelfmodal']//button[@type='submit']"},
            {
                "path": "//*[@id='save_button1']//button[@type='submit']",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "add_shelf")

    @modifies_db
    def test_add_cols_rows(self):
        self.selenium.get(
            url=self.live_server_url
            + str(reverse("laboratory:labindex", kwargs={"org_pk": 1, "lab_pk": 1}))
        )
        path_list = [
            {"path": "//div[contains(@class, 'right_col')]//a[contains(@href, '/rooms/create')]"},
            {"path": "(//button[@data-bs-toggle='popover'])[1]", "sleep": 1},
            {"path": "(//div[contains(@class, 'popover')]//a)[2]", "sleep": 1},
            {
                "path": "//*[@id='btnAddRow']",
                "scroll": "window.scrollTo(0, 100)",
            },
            {"path": "//button[@onclick='addColumn()']"},
            {"path": "//button[@onclick='deleteColumns()']"},
            {"path": "//button[@onclick='deleteRows()']"},
            {
                "path": "//button[@onclick='deleteRows()']",
                "screenshot_name": "remove_shelf_row",
            },
        ]
        self.create_gif_process(path_list, "manage_rows_cols")

    @modifies_db
    def test_remove_row_with_shelf(self):
        self.selenium.get(
            url=self.live_server_url
            + str(reverse("laboratory:labindex", kwargs={"org_pk": 1, "lab_pk": 1}))
        )
        path_list = [
            {"path": "//div[contains(@class, 'right_col')]//a[contains(@href, '/rooms/create')]"},
            {"path": "(//button[@data-bs-toggle='popover'])[1]", "sleep": 1},
            {"path": "(//div[contains(@class, 'popover')]//a)[2]", "sleep": 1},
            {"path": "//button[@onclick='deleteRows()']"},
            {"path": "//*[@id='remove_shelf']", "screenshot_name": "remove_shelf_row"},
        ]
        self.create_gif_process(path_list, "manage_rows_cols_shelf")

    @modifies_db
    def test_update_shelf(self):
        self.selenium.get(
            url=self.live_server_url
            + str(reverse("laboratory:labindex", kwargs={"org_pk": 1, "lab_pk": 1}))
        )
        path_list = [
            {"path": "//div[contains(@class, 'right_col')]//a[contains(@href, '/rooms/create')]"},
            {"path": "(//button[@data-bs-toggle='popover'])[1]", "sleep": 1},
            {"path": "(//div[contains(@class, 'popover')]//a)[2]", "sleep": 1},
            {
                "path": "(//li[contains(@class, 'shelfitem')]"
                        "//a[.//i[contains(@class, 'fa-edit')]])[1]",
                "sleep": 1,
            },
            {"path": ".//*[@id='id_shelf--name']", "extra_action": "clearinput"},
            {
                "path": ".//*[@id='id_shelf--name']",
                "extra_action": "setvalue",
                "value": "Estante Actualizado",
            },
            {"path": "//span[@aria-controls='select2-id_shelf--type-container']"},
            {"path": select2_result(3)},
            # processResponse llena #shelfmodalbody (createshelfmodal) también
            # para la edición; el editshelfmodal quedó sin uso en este flujo.
            {"path": "//*[@id='createshelfmodal']//button[@type='submit']"},
            {
                "path": "//*[@id='save_button1']//button[@type='submit']",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "update_shelf")

    @modifies_db
    def test_delete_shelf(self):
        self.selenium.get(
            url=self.live_server_url
            + str(reverse("laboratory:labindex", kwargs={"org_pk": 1, "lab_pk": 1}))
        )
        path_list = [
            {"path": "//div[contains(@class, 'right_col')]//a[contains(@href, '/rooms/create')]"},
            {"path": "(//button[@data-bs-toggle='popover'])[1]", "sleep": 1},
            {"path": "(//div[contains(@class, 'popover')]//a)[2]", "sleep": 1},
            {
                "path": "(//li[contains(@class, 'shelfitem')]"
                        "//a[.//i[contains(@class, 'fa-minus')]])[1]",
                "sleep": 1,
            },
            {"path": "//button[contains(@class, 'swal2-confirm')]", "sleep": 1},
        ]
        self.create_gif_process(path_list, "delete_shelf")

    def test_view_shelf(self):
        # El preludio original (selector de org -> "My laboratories") depende
        # de permisos que el fixture no trae (my_labs rinde vacío para user 1);
        # se entra directo al labindex como el resto de la suite.
        self.selenium.get(
            url=self.live_server_url
            + str(reverse("laboratory:labindex", kwargs={"org_pk": 1, "lab_pk": 1}))
        )
        path_list = [
            {"path": "//div[contains(@class, 'right_col')]//a[contains(@href, '/rooms/create')]"},
            {"path": "(//button[@data-bs-toggle='popover'])[1]", "sleep": 1},
            {"path": "(//div[contains(@class, 'popover')]//a)[2]", "sleep": 1},
        ]
        self.create_gif_process(path_list, "view_shelves")
