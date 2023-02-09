from django.urls import reverse

from laboratory.models import Inform
from laboratory.tests.utils import BaseLaboratorySetUpTest


class InformViewTest(BaseLaboratorySetUpTest):

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

    def test_api_informs_detail(self):
        url = reverse("laboratory:api-informs-detail", kwargs={"pk": 1, })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

class CommentInformViewTest(BaseLaboratorySetUpTest):

    def test_api_inform_list(self):
        url = reverse("laboratory:api-inform-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_api_inform_detail(self):
        url = reverse("laboratory:api-inform-detail", kwargs={"pk": 1, })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

class InformSchedulerViewTest(BaseLaboratorySetUpTest):

    def test_inform_index(self):
        url = reverse("laboratory:inform_index", kwargs={"org_pk": self.org.pk, })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_period_scheduler(self):
        url = reverse("laboratory:add_period_scheduler", kwargs={"org_pk": self.org.pk, })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_edit_period_scheduler(self):
        url = reverse("laboratory:edit_period_scheduler", kwargs={"org_pk": self.org.pk, "pk": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_detail_period_scheduler(self):
        url = reverse("laboratory:detail_period_scheduler", kwargs={"org_pk": self.org.pk, "pk": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)