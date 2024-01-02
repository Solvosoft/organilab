from django.contrib.auth.models import User
from django.urls import reverse
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from organilab_test.tests.base import SeleniumBase
from django.utils.translation import gettext_lazy as _


class OrganizationSeleniumTest(SeleniumBase):
    fixtures = ["selenium/organization_manage.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.select_org_url = self.live_server_url + str(reverse('auth_and_perms:select_organization_by_user'))
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)
        self.folder_name = "create_org"
        self.create_directory_path(folder_name=self.folder_name)

    def test_create_organization(self):
        self.screenShots("1_select_org", time_out=3)
        action = ActionChains(self.selenium)

        org_and_perms = self.selenium.find_element(By.XPATH, ".//ul[@class='nav side-menu']/li[2]/a")
        action.move_to_element(org_and_perms).perform()
        org_and_perms.click()
        self.screenShots("2_org_and_perms", time_out=3)

        manage_orgs = self.selenium.find_element(By.XPATH, ".//ul[@class='nav side-menu']/li[2]/ul/li/a")
        action.move_to_element(manage_orgs).perform()
        manage_orgs.click()
        self.screenShots("3_manage_orgs", time_out=3)

        btn_add_org = self.selenium.find_element(By.XPATH, ".//span[@class='addOrgStructureEmpty']")
        action.move_to_element(btn_add_org).perform()
        btn_add_org.click()
        self.screenShots("4_btn_add_org", time_out=3)

        name_input = self.selenium.find_element(By.XPATH, ".//div[@id='addOrganizationmodal']/div/div[@class='modal-content']/form/div[@class='modal-body']/div/div/input[@id='id_name']")

        self.screenShots("5_add_org_form", time_out=3)
        action.move_to_element(name_input).perform()
        name_input.click()
        self.screenShots("6_name_input_click", time_out=3)

        name_input.send_keys(_("Organization Name"))
        self.screenShots("7_name_input_set_value", time_out=3)

        btn_create_org = self.selenium.find_element(By.XPATH, ".//div[@id='addOrganizationmodal']/div/div[@class='modal-content']/form/div[@class='modal-footer']/button[@type='submit']")
        action.move_to_element(btn_create_org).perform()
        btn_create_org.click()
        self.screenShots("8_btn_create_org_click", time_out=3)

        self.create_gifs(self.dir, self.folder_name)
