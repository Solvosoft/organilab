from django.urls import reverse

from laboratory.models import LaboratoryRoom, Laboratory
from laboratory.tests.utils import BaseLaboratorySetUpTest


class LaboratoryRoomViewTest(BaseLaboratorySetUpTest):

    def test_get_laboratoryroom_list(self):
        url = reverse("laboratory:rooms_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_laboratoryroom(self):
        data = {
            "name": "Sala de muestras"
        }
        url = reverse("laboratory:rooms_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data)
        success_url = reverse("laboratory:rooms_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response, success_url)
        self.assertIn("Sala de muestras", list(LaboratoryRoom.objects.values_list("name", flat=True)))

    def test_update_laboratoryroom(self):

        url = reverse("laboratory:rooms_update", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 1})
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Sala de inventario")

        data = {
            "name": "Sala de inventario químico"
        }
        response_post = self.client.post(url, data=data)
        success_url = reverse("laboratory:rooms_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response_post, success_url)


    def test_delete_laboratoryroom(self):
        url = reverse("laboratory:rooms_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 1})
        response = self.client.post(url)
        success_url = reverse("laboratory:rooms_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, success_url)

    def test_labroom_building_report(self):
        data = {
            "format": "pdf"
        }
        url = reverse("laboratory:report_building", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_reports_laboratory(self):
        data = {
            "format": "pdf"
        }
        url = reverse("laboratory:reports_laboratory", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)


class LaboratoryViewTest(BaseLaboratorySetUpTest):

    def test_get_laboratory_list(self):
        url = reverse("laboratory:mylabs", kwargs={"org_pk": self.org.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_laboratory(self):
        data = {
            "name": "KSA Lab",
            "phone_number": "(506)2230-9546",
            "location": "San José",
            "geolocation": "9.895804362670006,-84.1552734375",
            "organization": self.org.pk
        }
        url = reverse("laboratory:create_lab", kwargs={"org_pk": self.org.pk})
        response = self.client.post(url, data=data)
        success_url = reverse("auth_and_perms:organizationManager")
        self.assertRedirects(response, success_url)
        self.assertIn("KSA Lab", list(Laboratory.objects.values_list("name", flat=True)))

    def test_update_laboratory(self):
        url = reverse("laboratory:laboratory_update", kwargs={"org_pk": self.org.pk, "pk": 1})
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Vick Lab")

        data = {
            "name": "Organización X",
            "phone_number": "(506)2230-9546",
            "location": "San José",
            "geolocation": "9.895804362670006,-84.1552734375",
            "organization": self.org.pk
        }
        response_post = self.client.post(url, data=data)
        success_url = reverse("laboratory:mylabs", kwargs={"org_pk": self.org.pk})
        self.assertIn("Organización X", list(Laboratory.objects.values_list("name", flat=True)))

    def test_check_laboratory_index(self):
        url = reverse("laboratory:labindex", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.lab.name)

    def test_select_lab(self):
        url = reverse("laboratory:select_lab")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_laboratory_delete(self):
        lab = Laboratory.objects.get(name="DS Cosme")
        url = reverse("laboratory:laboratory_delete", kwargs={"org_pk": self.org.pk, "pk": lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)