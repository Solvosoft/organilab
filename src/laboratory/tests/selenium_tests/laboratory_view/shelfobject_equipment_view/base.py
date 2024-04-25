from django.contrib.auth.models import User
from django.urls import reverse

from organilab_test.tests.base import SeleniumBase


class ShelfObjectEquipmentSeleniumTest(SeleniumBase):
    fixtures = ["selenium/edit_shelfobject_equipment_view.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(pk=1)
        self.force_login(user=self.user, driver=self.selenium, base_url=self.live_server_url)
        self.selenium.get(url=self.live_server_url + str(
            reverse('laboratory:labindex', kwargs={"org_pk": 1, "lab_pk": 1})))

        self.path_base = [
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[2]/div[1]/div[2]/ul/li[1]/a"}, #VISTA LABORATORIO
            {"path": "//*[@id='labroom_1']"},
            {"path": "//*[@id='furniture_1']"},
            {"path": "//*[@id='shelf_1']", "scroll": "window.scrollTo(0, 250)"},
            {"path": "/html/body/div[1]/div/div[3]/div/div/div[19]/div/div[2]/table/tbody/tr[1]/td[7]/a[6]"},
        ]



