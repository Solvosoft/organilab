from django.test import tag
from laboratory.tests.selenium_tests.manage_organizations.base import (
    ManageOrganizationsSeleniumTest,
)
from organilab_test.tests.selenium_xpaths import select2_result


@tag("selenium")
class LaboratoryTabTest(ManageOrganizationsSeleniumTest):

    def setUp(self):
        super().setUp()
        # Select org node via iCheck and click "By laboratory" tab
        self.tab_lab = [
            self.select_org_via_icheck(1),
            {"path": "//*[@id='navbylabs']", "sleep": 1},
        ]

        # Select a laboratory in the "By laboratory" tab
        self.select_laboratory_tab_lab = self.tab_lab + [
            {
                "path": "//*[@id='bylabs']//span[contains(@class, 'select2-selection')]",
                "sleep": 1,
            },
            {
                "path": select2_result(1),
            },
            # Picking the lab fires select2:select, which triggers
            # ajax.reload() on #userpermelement.  Without this wait the next
            # step finds the stale (or empty) table.
            {
                "path": "//*[@id='userpermelement']",
                "presence_only": True,
                "wait_dt": True,
            },
        ]

    def test_relate_user_to_org_and_lab_from_tab_lab(self):
        """Test relating a user to a lab from the laboratory tab.

        Flow: Select org -> Click 'By laboratory' tab -> Select lab ->
        Click 'Relate user' button -> Switch to external user tab ->
        Enter email -> Find user -> Switch to organization tab -> Select
        user profile -> Save.

        GIF: docs/source/_static/gif/relate_user_to_org_and_lab_from_tab_lab.gif
        """
        path_list = self.tab_lab + [
            {
                "path": "//*[@id='bylabs']//span[contains(@class, 'select2-selection')]",
                "sleep": 1,
            },
            {
                "path": select2_result(1),
            },
            {
                "path": "//*[@id='relateusertolab']",
                "sleep": 1,
            },
            {
                "path": "//*[@id='profiorgextuser-tab']",
                "sleep": 2,
            },
            {
                "path": "//*[@id='externaluserformcontainer']//input",
                "sleep": 1,
            },
            {
                "path": "//*[@id='externaluserformcontainer']//input",
                "extra_action": "setvalue",
                "value": "ricardom@gmail.com",
            },
            {
                "path": "//*[@id='relemailbtn']",
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 2,
            },
            {
                "path": "//*[@id='profiorg-tab']",
            },
            {
                "path": "//*[@id='profiorgtabbody']//span[contains(@class, 'select2-selection')]",
                "sleep": 1,
            },
            {
                "path": select2_result(1),
            },
            {
                "path": "//*[@id='relprofilewithlaboratorybtn']",
            },
        ]
        self.create_gif_process(path_list, "relate_user_to_org_and_lab_from_tab_lab")

    def test_add_permission_rol_to_user_from_tab_lab(self):
        """Test adding a permission role to a user from the laboratory tab.

        Flow: Select org -> 'By laboratory' tab -> Select lab -> Click
        'Apply as role' icon -> Select role in modal -> Save.

        GIF: docs/source/_static/gif/add_permission_rol_to_user_from_tab_lab.gif
        """
        path_list = (
            self.select_laboratory_tab_lab
            + [{"path": self.rol_btn("userpermelement"), "wait_dt": True, "sleep": 2}]
            + self.add_permission_rol
        )
        self.create_gif_process(path_list, "add_permission_rol_to_user_from_tab_lab")

    def test_remove_permission_rol_to_user_from_tab_lab(self):
        """Test removing a permission role from a user via the laboratory tab.

        Flow: Select org -> 'By laboratory' tab -> Select lab -> Click
        'Apply as role' icon -> Uncheck permission -> Save.

        GIF: docs/source/_static/gif/remove_permission_rol_to_user_from_tab_lab.gif
        """
        path_list = (
            self.select_laboratory_tab_lab
            + [{"path": self.rol_btn("userpermelement"), "wait_dt": True, "sleep": 2}]
            + self.remove_and_save_permission_rol
        )
        self.create_gif_process(path_list, "remove_permission_rol_to_user_from_tab_lab")

    def test_use_selected_permission_rol_to_user_from_tab_lab(self):
        """Test applying an already selected permission role to a user.

        Flow: Select org -> 'By laboratory' tab -> Select lab -> Click
        'Apply as role' -> Remove existing role selection -> Select
        different role -> Check use permission -> Save.

        GIF: docs/source/_static/gif/use_selected_permission_rol_to_user_from_tab_lab.gif
        """
        path_list = (
            self.select_laboratory_tab_lab
            + [
                {"path": self.rol_btn("userpermelement"), "wait_dt": True, "sleep": 2},
                {
                    "path": "//*[@id='modal1']//span[contains(@class, 'select2-selection')]",
                    "sleep": 1,
                },
                {
                    "path": select2_result(2),
                },
            ]
            + self.use_and_save_permission_rol
        )
        self.create_gif_process(
            path_list, "use_selected_permission_rol_to_user_from_tab_lab"
        )

    def test_delete_relation_user_lab_from_tab_lab(self):
        """Test removing a user-lab relationship from the laboratory tab.

        Flow: Select org -> 'By laboratory' tab -> Select lab -> Click
        on user row -> Click delete icon -> Confirm SweetAlert.

        GIF: docs/source/_static/gif/delete_relation_user_lab_from_tab_lab.gif
        """
        path_list = self.select_laboratory_tab_lab + [
            {
                "path": self.delete_profile_btn("userpermelement"),
                "scroll": "window.scrollTo(0, 250)",
                "wait_dt": True,
                "sleep": 3,
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 2,
            },
            # Confirming only closes the dialog; without waiting for the table
            # to reload the test would pass even if nothing was deleted.
            {
                "path": "//*[@id='userpermelement']",
                "presence_only": True,
                "wait_dt": True,
            },
        ]
        self.create_gif_process(path_list, "delete_relation_user_lab_from_tab_lab")

    def test_delete_relation_user_lab_and_deactivate_user_from_tab_lab(self):
        """Test removing user-lab relationship and deactivating the user.

        Flow: Select org -> 'By laboratory' tab -> Select lab -> Click
        user row -> Click delete icon -> Check 'Deactivate user'
        -> Confirm SweetAlert.

        GIF: docs/source/_static/gif/delete_relation_user_lab_and_deactivate_user_from_tab_lab.gif
        """
        path_list = self.select_laboratory_tab_lab + [
            {
                "path": self.delete_profile_btn("userpermelement"),
                "scroll": "window.scrollTo(0, 250)",
                "wait_dt": True,
                "sleep": 3,
            },
            {
                "path": "//*[@id='swal2-checkbox']",
                "sleep": 2,
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
            },
            {
                "path": "//*[@id='userpermelement']",
                "presence_only": True,
                "wait_dt": True,
            },
        ]
        self.create_gif_process(
            path_list, "delete_relation_user_lab_and_deactivate_user_from_tab_lab"
        )
