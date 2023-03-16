from django.urls import reverse

from laboratory.models import ObjectFeatures
from laboratory.tests.utils import BaseLaboratorySetUpTest

class ObjectViewTest(BaseLaboratorySetUpTest):

    def test_get_substance_list(self):
        url = reverse("laboratory:sustance_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_substance(self):
        url = reverse("laboratory:sustance_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 2})
        response = self.client.post(url)
        success_url = reverse("laboratory:sustance_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, success_url)

    def test_sustance_add(self):
        url = reverse("laboratory:sustance_add", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_sustance_manage(self):
        url = reverse("laboratory:sustance_manage", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_sustance_list_json(self):
        url = reverse("laboratory:sustance_list_json", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_object_report(self):
        data = {
            "type_id": "1",
            "format": "pdf",
            "pk": 1
        }
        url = reverse("laboratory:reports_objects", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_objects_list_report(self):
        data = {
            "type_id": "1"
        }
        url = reverse("laboratory:reports_objects_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_reactive_precursor_object_list_report(self):
        url = reverse("laboratory:reactive_precursor_object_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_object_change_logs_report(self):

        url = reverse("laboratory:object_change_logs", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_precursor_report(self):
        data = {
            "consecutive": 1,
            "month": 2,
            "year": 2018
        }
        url = reverse("laboratory:precursor_report", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)

class SustanceCharacteristicsViewTest(BaseLaboratorySetUpTest):

    def test_organizationreactivepresence(self):
        url = reverse("laboratory:organizationreactivepresence", kwargs={"org_pk": self.org.pk, })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_download_h_code_reports(self):
        url = reverse("laboratory:download_h_code_reports", kwargs={"org_pk": self.org.pk, })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_h_code_reports(self):
        url = reverse("laboratory:h_code_reports", kwargs={"org_pk": self.org.pk, })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

class ObjectFeaturesViewTest(BaseLaboratorySetUpTest):

    def test_update_objectfeature(self):
        objfeature = ObjectFeatures.objects.first()
        url = reverse("laboratory:object_feature_update", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": objfeature.pk})

        response_get = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Es un reactivo en la industria química")

        data = {
            "name": "Reactivo 1",
            "description": "Es un reactivo en la industria química empacado en saco de 50kg o bolsas de 2kg."
        }
        response_post = self.client.post(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        success_url = reverse("laboratory:object_feature_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response_post.status_code, 302)
        self.assertRedirects(response_post, success_url)
        self.assertIn("Reactivo 1", list(ObjectFeatures.objects.values_list("name", flat=True)))

    def test_create_objectfeature(self):
        data = {
            "name": "Guantes",
            "description": "Brinda protección en manos y brazos a la hora de manipular cualquier material que lo requiera.",
        }
        url = reverse("laboratory:object_feature_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data)
        success_url = reverse("laboratory:object_feature_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, success_url)
        self.assertIn("Guantes", list(ObjectFeatures.objects.values_list("name", flat=True)))

    def test_delete_objectfeature(self):
        objfeature = ObjectFeatures.objects.first()
        url = reverse("laboratory:object_feature_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": objfeature.pk})
        response = self.client.post(url)
        success_url = reverse("laboratory:object_feature_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, success_url)