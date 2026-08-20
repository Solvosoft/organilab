from django.test import tag
from laboratory.tests.selenium_tests.manage_organizations.base import (
    ManageOrganizationsSeleniumTest,
)
from organilab_test.tests.selenium_xpaths import select2_result


@tag("selenium")
class ButtonBoxCollapseOrgNameTest(ManageOrganizationsSeleniumTest):

    def setUp(self):
        super().setUp()
        self.role_button_box = [
            {"path": self.org_node_h6(1)},
            {"path": self.org_rolbtnadd(1), "sleep": 1},
        ]

    def test_add_role_to_org_without_copy_permissions_from_others_roles(self):
        """Test adding a new role without copying permissions from existing roles.

        Flow: Expand org node -> Click 'Add Rol' -> Fill role name in
        modal -> Save.

        GIF: docs/source/_static/gif/add_role_to_org_without_copy_permissions_from_others_roles.gif
        """
        path_list = self.role_button_box + [
            {
                "path": "//*[@id='rolname']",
                "sleep": 2,
            },
            {
                "path": "//*[@id='rolname']",
                "extra_action": "setvalue",
                "value": "Gestión de objetos",
            },
            {
                "path": "//*[@id='saveroluserorg']",
            },
        ]
        self.create_gif_process(
            path_list, "add_role_to_org_without_copy_permissions_from_others_roles"
        )

    def test_add_role_to_org_copy_permissions_from_others_roles(self):
        """Test adding a new role and copying permissions from existing roles.

        Flow: Expand org node -> Click 'Add Rol' -> Fill role name ->
        Check 'Copy permissions' -> Select source role -> Save.

        GIF: docs/source/_static/gif/add_role_to_org_copy_permissions_from_others_roles.gif
        """
        path_list = self.role_button_box + [
            {
                "path": "//*[@id='rolname']",
                "sleep": 2,
            },
            {
                "path": "//*[@id='rolname']",
                "extra_action": "setvalue",
                "value": "Administrar Laboratorio",
            },
            {
                "path": "//*[@id='selectroldiv']",
                "extra_action": "script",
                "value": "$('#id_relate_rols').iCheck('check'); setTimeout(function(){ $('#rolS2container').show(); }, 500);",
                "sleep": 2,
            },
            {
                "path": "//*[@id='rolS2container']//span[contains(@class, 'select2-selection')]",
                "sleep": 3,
            },
            {
                "path": select2_result(1),
            },
            {
                "path": "//*[@id='saveroluserorg']",
            },
        ]
        self.create_gif_process(
            path_list, "add_role_to_org_copy_permissions_from_others_roles"
        )

    def test_copy_role_to_org(self):
        """Test copying roles from another organization.

        Flow: Expand org node -> Click 'Add Rol' -> Switch to 'Copy Rols'
        tab -> Select source role -> Save.

        GIF: docs/source/_static/gif/copy_role_to_org.gif
        """
        path_list = self.role_button_box + [
            {
                "path": "//*[@id='btn_copy_rol']",
                "sleep": 2,
            },
            {
                "path": "//*[@id='copy_rol_container']//span[contains(@class, 'select2-selection')]",
                "sleep": 1,
            },
            {
                "path": select2_result(1),
            },
            {
                "path": "//*[@id='saveroluserorg']",
            },
        ]
        self.create_gif_process(path_list, "copy_role_to_org")

    def test_add_user_to_org_from_button_box(self):
        """Test adding a new user from the organization button box.

        Flow: Expand org node -> Click 'Add User' link -> Fill user
        registration form (name, email, phone, ID, job) -> Submit.

        GIF: docs/source/_static/gif/add_user_to_org_from_button_box.gif
        """
        path_list = [
            {"path": self.org_node_h6(1)},
            {"path": self.org_add_user_link(1), "sleep": 1},
            {
                "path": "//form//input[@name='first_name' or @id='id_first_name']",
                "wait_ready": True,
            },
            {
                "path": "//form//input[@name='first_name' or @id='id_first_name']",
                "extra_action": "setvalue",
                "value": "Andrea",
            },
            {"path": "//form//input[@name='last_name' or @id='id_last_name']"},
            {
                "path": "//form//input[@name='last_name' or @id='id_last_name']",
                "extra_action": "setvalue",
                "value": "Rojas Barrantes",
            },
            {"path": "//form//input[@name='email' or @id='id_email']"},
            {
                "path": "//form//input[@name='email' or @id='id_email']",
                "extra_action": "setvalue",
                "value": "andrearb@",
            },
            {
                "path": "//form//input[@name='email' or @id='id_email']",
                "extra_action": "move_cursor_end",
                "reduce_length": 3,
            },
            {
                "path": "//form//input[@name='email' or @id='id_email']",
                "extra_action": "setvalue",
                "value": "gmail.com",
            },
            {"path": "//form//input[@name='phone_number' or @id='id_phone_number']"},
            {
                "path": "//form//input[@name='phone_number' or @id='id_phone_number']",
                "extra_action": "setvalue",
                "value": "50688888888",
            },
            {"path": "//form//input[@name='id_card' or @id='id_id_card']"},
            {
                "path": "//form//input[@name='id_card' or @id='id_id_card']",
                "extra_action": "setvalue",
                "value": "707770777",
            },
            {"path": "//form//input[@name='job_position' or @id='id_job_position']"},
            {
                "path": "//form//input[@name='job_position' or @id='id_job_position']",
                "extra_action": "setvalue",
                "value": "Estudiante",
            },
            {"path": "//form//input[@type='submit'] | //form//button[@type='submit']"},
        ]
        self.create_gif_process(path_list, "add_user_to_org_from_button_box")

    def test_relate_user_to_org_from_button_box(self):
        """Test relating an existing user to a child organization.

        Flow: Expand child org node (pk=2) -> Click 'Related Users' ->
        Select user in modal -> Submit.

        GIF: docs/source/_static/gif/relate_user_to_org_from_button_box.gif
        """
        path_list = [
            {"path": self.org_node_h6(1)},
            {"path": self.org_node_h6(2), "sleep": 1},
            {"path": self.org_userbtnadd(2), "sleep": 1},
            {
                "path": "//*[@id='modaluser2']//span[contains(@class, 'select2-selection')]",
                "sleep": 2,
            },
            {
                "path": select2_result(1),
            },
            {
                "path": "//*[@id='modaluser2']//button[@type='submit']",
            },
        ]
        self.create_gif_process(path_list, "relate_user_to_org_from_button_box")

    def test_add_laboratory_to_org(self):
        """Test adding a new laboratory to an organization.

        Flow: Expand org node -> Click 'Add Laboratory' -> Fill lab form
        (name, phone, location) -> Submit.

        GIF: docs/source/_static/gif/add_laboratory_to_org.gif
        """
        path_list = [
            {"path": self.org_node_h6(1)},
            {"path": self.org_add_lab_link(1), "sleep": 1},
            {
                "path": "//form//input[@name='name' or @id='id_name']",
                "wait_ready": True,
            },
            {
                "path": "//form//input[@name='name' or @id='id_name']",
                "extra_action": "setvalue",
                "value": "Laboratorio Estudiantil",
            },
            {"path": "//form//input[@name='phone_number' or @id='id_phone_number']"},
            {
                "path": "//form//input[@name='phone_number' or @id='id_phone_number']",
                "extra_action": "setvalue",
                "value": "(506)2222-2222",
            },
            {"path": "//form//input[@name='location' or @id='id_location']"},
            {
                "path": "//form//input[@name='location' or @id='id_location']",
                "extra_action": "setvalue",
                "value": "San Pedro, San José",
            },
            {
                "path": "//form//button[@type='submit'] | //form//input[@type='submit']",
                "scroll": "window.scrollTo(0, 300)",
            },
        ]
        self.create_gif_process(path_list, "add_laboratory_to_org")

    def test_relate_external_laboratory_to_org(self):
        """Test relating a laboratory from parent org to a child org.

        Flow: Expand child org node (pk=2) -> Click 'Related Laboratory'
        -> Select lab in modal -> Submit.

        GIF: docs/source/_static/gif/relate_external_laboratory_to_org.gif
        """
        path_list = [
            {"path": self.org_node_h6(1)},
            {"path": self.org_node_h6(2), "sleep": 1},
            {"path": self.org_rel_lab_btn(2), "sleep": 1},
            {
                "path": "//*[@id='relOrganizationmodal']//span[contains(@class, 'select2-selection')]",
                "sleep": 2,
            },
            {
                "path": select2_result(1),
            },
            {"path": self.org_rel_lab_save_btn()},
        ]
        self.create_gif_process(path_list, "relate_external_laboratory_to_org")

    def test_relate_org_base_laboratory_to_org_child(self):
        """Test relating a laboratory from base org to another child org.

        Flow: Expand second root org node (pk=3) -> Expand child (pk=4)
        -> Click 'Related Laboratory' -> Select lab -> Submit.

        GIF: docs/source/_static/gif/relate_org_base_laboratory_to_org_child.gif
        """
        path_list = [
            {"path": self.org_node_h6(3)},
            {"path": self.org_node_h6(4), "sleep": 1},
            {"path": self.org_rel_lab_btn(4), "sleep": 1},
            {
                "path": "//*[@id='relOrganizationmodal']//span[contains(@class, 'select2-selection')]",
                "sleep": 2,
            },
            {
                "path": select2_result(1),
            },
            {"path": self.org_rel_lab_save_btn()},
        ]
        self.create_gif_process(path_list, "relate_org_base_laboratory_to_org_child")
