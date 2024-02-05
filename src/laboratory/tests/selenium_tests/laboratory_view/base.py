from django.contrib.auth.models import User
from django.urls import reverse

from laboratory.models import OrganizationStructure
from organilab_test.tests.base import SeleniumBase


class LaboratoryViewSeleniumTest(SeleniumBase):
    fixtures = ["selenium/laboratory_view.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.select_org_url = self.live_server_url + str(reverse('auth_and_perms:select_organization_by_user'))
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)

        self.path_base = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div/div/span/span[1]/span"},
            {"path": "/html/body/span/span/span[2]/ul/li"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div/div/div/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div/div/div[1]/a"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[2]/ul/li[1]/a"}
        ]
