from django.urls import reverse

from laboratory.models import Inform
from laboratory.test.utils import BaseSetUpTest


class InformViewTest(BaseSetUpTest):

    def test_get_inform_list(self):
        url = reverse("laboratory:get_informs", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_inform(self):
        url = reverse("laboratory:complete_inform", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 1})
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Gestión de laboratorio")

        data = {
            "csrfmiddlewaretoken": "",
            "status": "Finalized"
        }
        self.client.post(url, data=data)
        self.assertEqual(data["status"], Inform.objects.get(pk=1).status)

    def test_create_inform(self):
        data = {
            "name": "Uso de instrumentos de laboratorio",
            "custom_form": 1
        }
        url = reverse("laboratory:add_informs", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk,
                                                        "content_type": "laboratory", "model": "laboratory"})
        response = self.client.post(url, data=data)
        success_url = reverse("laboratory:get_informs", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response, success_url)
        self.assertIn("Uso de instrumentos de laboratorio", list(Inform.objects.values_list("name", flat=True)))

    def test_delete_inform(self):
        url = reverse("laboratory:remove_inform", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 1})
        response = self.client.post(url, follow=True)
        success_url = reverse("laboratory:get_informs", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, success_url)