from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from laboratory.models import Laboratory, OrganizationStructure, Protocol, Provider, Inform


class BaseSetUpTest(TestCase):
    fixtures = ["../fixtures/initialdata.json", "../fixtures/laboratory_data.json"]

    def setUp(self):
        self.user = get_user_model().objects.filter(username="german").first()
        self.org = OrganizationStructure.objects.first()
        self.lab = Laboratory.objects.first()
        self.client.force_login(self.user)

class ProviderViewTest(BaseSetUpTest):


    def test_get_provider_list(self):
        url = reverse("laboratory:list_provider", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


    def test_get_provider_detail(self):
        url = reverse("laboratory:update_lab_provider", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Karine Products")


    def test_post_provider(self):
        data = {
            "name": "NatVou",
            "phone_number": "(506)2240-8035",
            "email": "natvou@example.com",
            "legal_identity": "3-876-763",
            "laboratory": self.lab
        }
        url = reverse("laboratory:add_provider", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data)
        success_url = reverse("laboratory:list_provider", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response, success_url)
        self.assertIn("NatVou", list(Provider.objects.values_list("name", flat=True)))


class ProtocolViewTest(BaseSetUpTest):

    def test_get_protocol_list(self):
        url = reverse("laboratory:protocol_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_protocol(self):
        url = reverse("laboratory:protocol_update", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 1})

        # Checking by method get if initial data protocol exists
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Lavado de manos")

        # Updating protocol
        data = {
            "name": "Lavado de manos",
            "short_description": "Higienización de las manos previa al ingreso del laboratorio y manipulación de los instrumentos del mismo.",
            "file": open('test.pdf', 'rb'),
            "laboratory": self.lab
        }
        response_post = self.client.post(url, data=data)
        success_url = reverse("laboratory:protocol_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response_post, success_url)

    def test_create_protocol(self):
        data = {
            "name": "Manejo de desechos",
            "short_description": "Manipulación de desechos ordinarios y reciclables y su destino.",
            "file": open('test.pdf', 'rb')
        }
        url = reverse("laboratory:protocol_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data)
        success_url = reverse("laboratory:protocol_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response, success_url)
        self.assertIn("Manejo de desechos", list(Protocol.objects.values_list("name", flat=True)))


    def test_delete_protocol(self):
        url = reverse("laboratory:protocol_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 1})
        response = self.client.delete(url)
        success_url = reverse("laboratory:protocol_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, success_url)


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
            "name": "Gestión de laboratorio y uso de instrumentos",
            "custom_form": 1
        }
        response_post = self.client.post(url, data=data)
        success_url = reverse("laboratory:get_informs", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response_post, success_url)
        self.assertIn("Uso de instrumentos de laboratorio", list(Inform.objects.values_list("name", flat=True)))

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
        response = self.client.delete(url, follow=True)
        success_url = reverse("laboratory:get_informs", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, success_url)