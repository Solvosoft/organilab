from django.contrib.auth.models import User
from django.urls import reverse

from organilab_test.tests.base import SeleniumBase


class ManageOrganizationsSeleniumTest(SeleniumBase):
    fixtures = ["selenium/organization_manage.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(
            user=self.user, driver=self.selenium, base_url=self.live_server_url
        )
        self.navigate_to_org_manage()

    def navigate_to_org_manage(self):
        url = self.live_server_url + str(
            reverse("auth_and_perms:organizationManager")
        )
        self.selenium.get(url)
        self.wait_for_page_ready()
        # Suppress DataTable error alerts that may occur before an org is selected
        self.selenium.execute_script(
            "if($.fn.dataTable) $.fn.dataTable.ext.errMode = 'none';"
        )

    # --- Organization node selectors ---

    def org_node_h6(self, pk):
        """Return XPath for the organization name heading that toggles collapse."""
        return "//h6[@data-bs-target='#collapse%d']" % pk

    def org_node_radio(self, pk):
        """Return XPath for the organization radio button."""
        return "//input[@class='nodeorg' and @value='%d']" % pk

    def org_collapse(self, pk):
        """Return XPath for the org collapse container."""
        return "//*[@id='collapse%d']" % pk

    # --- Collapse action button selectors ---

    def org_rolbtnadd(self, pk):
        """Return XPath for the 'Add Rol' button inside a collapse."""
        return "//span[contains(@class, 'rolbtnadd') and @data-id='%d']" % pk

    def org_userbtnadd(self, pk):
        """Return XPath for the 'Related Users' button."""
        return "//a[contains(@class, 'userbtnadd') and @data-id='%d']" % pk

    def org_add_user_link(self, pk):
        """Return XPath for the 'Add User' link."""
        return "//a[contains(@href, '/users/add/%d')]" % pk

    def org_add_lab_link(self, pk):
        """Return XPath for the 'Add Laboratory' link."""
        return "//a[contains(@href, 'create_lab')]"

    def org_rel_lab_btn(self, pk):
        """Return XPath for the 'Related Laboratory' button."""
        return "//a[contains(@class, 'contenttyperelobjbtnadd') and @data-id='%d']" % pk

    # --- Float-end action icon selectors ---

    def org_actions_icon(self, pk):
        """Return XPath for the org actions (wrench) icon."""
        return "//a[contains(@class, 'orgactions') and @data-org='%d']" % pk

    def org_loglist_link(self, pk):
        """Return XPath for the log list link."""
        return "//a[contains(@class, 'loglist') and contains(@href, '/logentry/')]"

    def org_rol_details_btn(self, pk):
        """Return XPath for the rol details button."""
        return "//a[contains(@class, 'rol_details_btn') and @data-org='%d']" % pk

    def org_change_parent_btn(self, pk):
        """Return XPath for the change parent span."""
        return "//span[contains(@class, 'orgbyuser') and @data-org='%d']" % pk

    def org_add_child_btn(self, pk):
        """Return XPath for the 'Add sub-organization' span."""
        return "//span[contains(@class, 'addOrgStructure') and @data-parent='%d']" % pk

    def org_delete_link(self, pk):
        """Return XPath for the 'Delete organization' link."""
        return "//a[contains(@href, '/organization/%d/delete')]" % pk

    # --- Modal selectors ---

    def get_submit_button_path(self, id_modal, button_type="submit"):
        """Return XPath for the submit button inside a modal."""
        return (
            "//*[@id='%s']//div[contains(@class, 'modal-footer')]"
            "//button[@type='%s']" % (id_modal, button_type)
        )

    def get_modal_save_btn(self, id_modal):
        """Return XPath for the Save/primary button in a modal footer."""
        return (
            "//*[@id='%s']//div[contains(@class, 'modal-footer')]"
            "//button[contains(@class, 'btn-primary')]" % id_modal
        )

    # --- Common path fragments ---

    @property
    def path_base(self):
        """Empty path base; navigation handled by navigate_to_org_manage."""
        return []

    def select_org_via_icheck(self, pk):
        """Return path dict to select org via iCheck (avoids click interception).

        iCheck wraps radio buttons with an overlay that intercepts direct
        clicks.  Using iCheck('check') fires the proper ifChecked event.
        """
        return {
            "path": self.org_node_radio(pk),
            "extra_action": "script",
            "value": "$('input.nodeorg[value=%d]').iCheck('check')" % pk,
            "sleep": 1,
        }

    @property
    def select_organization(self):
        """Select the first org node radio button (pk=1) via iCheck."""
        return [
            self.select_org_via_icheck(1),
        ]

    @property
    def button_save_permission_rol(self):
        return [
            {"path": "//*[@id='modal1']//div[contains(@class, 'modal-footer')]//button[contains(@class, 'btn-primary')]"}
        ]

    @property
    def add_permission_rol(self):
        return [
            {"path": "//*[@id='modal1']//div[contains(@class, 'modal-body')]//span[contains(@class, 'select2-selection')]"},
            {"path": "//*[@id='modal1']//span[contains(@class, 'select2-dropdown')]//ul/li"},
        ] + self.button_save_permission_rol

    @property
    def remove_and_save_permission_rol(self):
        return [
            {
                "path": "//*[@id='modal1']//div[contains(@class, 'modal-body')]//input[@name='mergeaction' and @value='sustract']",
                "extra_action": "script",
                "value": "$('#modal1 input[name=mergeaction][value=sustract]').iCheck('check')",
            }
        ] + self.button_save_permission_rol

    @property
    def use_and_save_permission_rol(self):
        return [
            {
                "path": "//*[@id='modal1']//div[contains(@class, 'modal-body')]//input[@name='mergeaction' and @value='full']",
                "extra_action": "script",
                "value": "$('#modal1 input[name=mergeaction][value=full]').iCheck('check')",
            }
        ] + self.button_save_permission_rol
