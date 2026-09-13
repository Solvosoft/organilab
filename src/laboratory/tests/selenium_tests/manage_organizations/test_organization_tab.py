from django.test import tag

from laboratory.tests.selenium_tests.manage_organizations.base import ManageOrganizationsSeleniumTest
from organilab_test.tests.selenium_xpaths import select2_result


@tag('selenium')
class OrganizationTabTest(ManageOrganizationsSeleniumTest):

    def setUp(self):
        super().setUp()

        self.tab_org = self.select_organization + [
            {"path": "//*[@id='navbyorgs']", "sleep": 1},
        ]

    def test_relate_user_to_org_and_lab_from_tab_org(self):
        """Test relating a user to org and lab from the organization tab.

        Flow: Select org -> Click 'By organization' tab -> Click relate
        user button -> Switch to external user tab -> Enter email -> Find
        user -> Confirm SweetAlert -> Switch to org tab -> Select profile
        -> Select lab -> Save.

        GIF: docs/source/_static/gif/relate_user_to_org_and_lab_from_tab_org.gif
        """
        path_list = self.tab_org + [
            {
                "path": "//*[@id='relateusertoorg']",
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
        self.create_gif_process(path_list, "relate_user_to_org_and_lab_from_tab_org")

    def test_add_permission_rol_to_user_from_tab_org(self):
        """Test adding a permission role to a user from the organization tab.

        Flow: Select org -> Click 'By organization' tab -> Click
        'Apply as role' icon -> Select role in modal -> Save.

        GIF: docs/source/_static/gif/add_permission_rol_to_user_from_tab_org.gif
        """
        path_list = self.tab_org + [
            {"path": self.rol_btn("orpermelement"), "wait_dt": True, "sleep": 2},
        ] + self.add_permission_rol
        self.create_gif_process(path_list, "add_permission_rol_to_user_from_tab_org")

    def test_remove_permission_rol_to_user_from_tab_org(self):
        """Test removing a permission role from a user via the organization tab.

        Flow: Select org -> Click 'By organization' tab -> Click
        'Apply as role' icon -> Uncheck permission -> Save.

        GIF: docs/source/_static/gif/remove_permission_rol_to_user_from_tab_org.gif
        """
        path_list = self.tab_org + [
            {"path": self.rol_btn("orpermelement"), "wait_dt": True, "sleep": 2},
        ] + self.remove_and_save_permission_rol
        self.create_gif_process(path_list, "remove_permission_rol_to_user_from_tab_org")

    def test_use_selected_permission_rol_to_user_from_tab_org(self):
        """Test applying an already selected permission role from the org tab.

        Flow: Select org -> Click 'By organization' tab -> Click
        'Apply as role' -> Clear existing selection -> Select different
        role -> Check use permission -> Save.

        GIF: docs/source/_static/gif/use_selected_permission_rol_to_user_from_tab_org.gif
        """
        path_list = self.tab_org + [
            {"path": self.rol_btn("orpermelement"), "wait_dt": True, "sleep": 2},
            {
                "path": "//*[@id='modal1']//span[contains(@class, 'select2-selection')]",
                "sleep": 1,
            },
            {
                "path": select2_result(2),
            },
        ] + self.use_and_save_permission_rol
        self.create_gif_process(
            path_list, "use_selected_permission_rol_to_user_from_tab_org"
        )

    def test_delete_relation_user_org_from_tab_org(self):
        """Test removing a user-org relationship from the organization tab.

        Flow: Select org -> Click 'By organization' tab -> Click delete
        icon on user row -> Confirm SweetAlert.

        GIF: docs/source/_static/gif/delete_relation_user_org_from_tab_org.gif
        """
        path_list = self.tab_org + [
            {
                "path": self.delete_profile_btn("orpermelement"),
                "scroll": "window.scrollTo(0, 250)",
                "wait_dt": True,
                "sleep": 2,
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
                "sleep": 2,
            },
            # Confirming only closes the dialog; without waiting for the table
            # to reload the test would pass even if nothing was deleted.
            {
                "path": "//*[@id='orpermelement']",
                "presence_only": True,
                "wait_dt": True,
            },
        ]
        self.create_gif_process(path_list, "delete_relation_user_org_from_tab_org")

    def test_delete_relation_user_org_and_deactivate_user_from_tab_org(self):
        """Test removing user-org relationship and deactivating the user.

        Flow: Select org -> Click 'By organization' tab -> Click delete
        icon on user row -> Check 'Deactivate user' -> Confirm SweetAlert.

        GIF: docs/source/_static/gif/delete_relation_user_org_and_deactivate_user_from_tab_org.gif
        """
        path_list = self.tab_org + [
            {
                "path": self.delete_profile_btn("orpermelement"),
                "scroll": "window.scrollTo(0, 250)",
                "wait_dt": True,
                "sleep": 2,
            },
            {
                "path": "//*[@id='swal2-checkbox']",
                "sleep": 1,
            },
            {
                "path": "//button[contains(@class, 'swal2-confirm')]",
            },
            {
                "path": "//*[@id='orpermelement']",
                "presence_only": True,
                "wait_dt": True,
            },
        ]
        self.create_gif_process(
            path_list, "delete_relation_user_org_and_deactivate_user_from_tab_org"
        )
