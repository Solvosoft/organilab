from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse

from organilab_test.tests.base import SeleniumBase


class LaboratoryViewSeleniumTest(SeleniumBase):
    fixtures = ["selenium/laboratory_view.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)
        self.selenium.get(url=self.live_server_url + str(
            reverse('laboratory:labindex', kwargs={"org_pk": 1, "lab_pk": 1})))

        self.path_base = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[2]/ul/li[1]/a"}
        ]

@tag('selenium')
class LabViewTest(SeleniumBase):
    fixtures = ["selenium/laboratory_view.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)

    def test_go_to_lab_view(self):
        path_list = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div/div/span/span[1]/span"},
            {"path": "/html/body/span/span/span[2]/ul/li"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[2]/div/div/div/a[1]"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div/div/div[1]/a"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[2]/ul/li[1]/a"}
        ]

        self.create_gif_process(path_list, "go_to_lab_view")
