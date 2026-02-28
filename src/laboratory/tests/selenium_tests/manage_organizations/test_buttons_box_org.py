from django.test import tag

from laboratory.tests.selenium_tests.manage_organizations.base import ManageOrganizationsSeleniumTest


@tag('selenium')
class ButtonBoxOrgTest(ManageOrganizationsSeleniumTest):

    def test_deactivate_organization(self):
        """Test deactivating an organization via the actions modal.

        Flow: Click org actions icon -> Select 'Deactivate' action in
        Select2 dropdown -> Submit modal.

        GIF: docs/source/_static/gif/deactivate_org.gif
        """
        path_list = [
            {"path": self.org_actions_icon(1), "sleep": 1},
            {
                "path": "//*[@id='actionsmodal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": "$('#id_actions').val('1').trigger('change');",
                "sleep": 3,
            },
            {"path": self.get_submit_button_path("actionsmodal")},
        ]
        self.create_gif_process(path_list, "deactivate_org")

    def test_clone_organization(self):
        """Test cloning an organization via the actions modal.

        Flow: Click org actions icon -> Select 'Clone' action in
        Select2 dropdown -> Submit modal.

        GIF: docs/source/_static/gif/clone_org.gif
        """
        path_list = [
            {"path": self.org_actions_icon(1), "sleep": 1},
            {
                "path": "//*[@id='actionsmodal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": "$('#id_actions').val('2').trigger('change');",
                "sleep": 3,
            },
            {"path": self.get_submit_button_path("actionsmodal")},
        ]
        self.create_gif_process(path_list, "clone_org")

    def test_change_organization_name(self):
        """Test changing an organization name via the actions modal.

        Flow: Click org actions icon -> Select 'Change name' action ->
        Clear and type new name -> Submit modal.

        GIF: docs/source/_static/gif/change_org_name.gif
        """
        path_list = [
            {"path": self.org_actions_icon(1), "sleep": 1},
            {
                "path": "//*[@id='actionsmodal']//div[contains(@class, 'modal-body')]",
                "extra_action": "script",
                "value": "$('#id_actions').val('3').trigger('change');",
                "sleep": 3,
            },
            {
                "path": "//*[@id='actionsmodal']//div[contains(@class, 'modal-body')]//input[@type='text']",
                "sleep": 1,
            },
            {
                "path": "//*[@id='actionsmodal']//div[contains(@class, 'modal-body')]//input[@type='text']",
                "extra_action": "clearinput",
            },
            {
                "path": "//*[@id='actionsmodal']//div[contains(@class, 'modal-body')]//input[@type='text']",
                "extra_action": "setvalue",
                "value": "Organización Principal",
            },
            {"path": self.get_submit_button_path("actionsmodal")},
        ]
        self.create_gif_process(path_list, "change_org_name")

    def test_view_org_logs(self):
        """Test navigating to the organization log list.

        Flow: Click log list icon for org pk=1.

        GIF: docs/source/_static/gif/view_org_logs.gif
        """
        path_list = [
            {"path": self.org_loglist_link(1)},
        ]
        self.create_gif_process(path_list, "view_org_logs")

    def test_view_org_roles(self):
        """Test navigating to view organization roles list.

        Flow: Click rol list link for org pk=1 -> View role entries.

        GIF: docs/source/_static/gif/view_org_roles.gif
        """
        path_list = [
            {
                "path": "//a[contains(@class, 'loglist') and contains(@href, '/rols/list/')]",
            },
        ]
        self.create_gif_process(path_list, "view_org_roles")

    def test_change_org_parent(self):
        """Test changing the parent of an organization.

        Flow: Click change parent icon -> Select new parent in modal
        Select2 -> Submit modal.

        GIF: docs/source/_static/gif/change_org_parent.gif
        """
        path_list = [
            {"path": self.org_change_parent_btn(1)},
            {
                "path": "//*[@id='orgbyusermodal']//span[contains(@class, 'select2-selection')]",
                "sleep": 2,
            },
            {
                "path": "//ul[contains(@class, 'select2-results__options')]/li",
            },
            {"path": self.get_submit_button_path("orgbyusermodal")},
        ]
        self.create_gif_process(path_list, "change_org_parent")

    def test_delete_organization(self):
        """Test deleting an organization.

        Flow: Click delete icon for org pk=1 -> Confirm deletion.

        GIF: docs/source/_static/gif/delete_org.gif
        """
        path_list = [
            {"path": self.org_delete_link(1)},
            {
                "path": "//input[@type='submit']",
                "wait_ready": True,
            },
        ]
        self.create_gif_process(path_list, "delete_org")

    def test_add_organization_descendant(self):
        """Test adding a child organization via modal.

        Flow: Click add sub-organization icon -> Fill name in modal
        -> Submit modal.

        GIF: docs/source/_static/gif/add_org_descendant.gif
        """
        path_list = [
            {"path": self.org_add_child_btn(1)},
            {
                "path": "//*[@id='addOrganizationmodal']//div[contains(@class, 'modal-body')]//input",
                "sleep": 2,
            },
            {
                "path": "//*[@id='addOrganizationmodal']//div[contains(@class, 'modal-body')]//input",
                "extra_action": "setvalue",
                "value": "Organización Hija",
            },
            {"path": self.get_submit_button_path("addOrganizationmodal")},
        ]
        self.create_gif_process(path_list, "add_org_descendant")
