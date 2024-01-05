from django.contrib.auth.models import User
from django.urls import reverse
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from organilab_test.tests.base import SeleniumBase
from django.utils.translation import gettext_lazy as _
from django.test import tag

@tag('selenium')
class ProcedureTemplateSeleniumTest(SeleniumBase):
    fixtures = ["selenium/procedure_temmplates.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.select_org_url = self.live_server_url + str(reverse('auth_and_perms:select_organization_by_user'))
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)
        self.folder_name = "create_procedure_template"
        self.create_directory_path(folder_name=self.folder_name)

    def test_create_procedure(self):
        pass
