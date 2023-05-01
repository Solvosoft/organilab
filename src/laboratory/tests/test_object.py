from django.urls import reverse

from laboratory.models import ObjectFeatures, Object
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

    def test_objectview_list(self):
        url = reverse("laboratory:objectview_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        data = {
            "type_id": '0'
        }
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tanque 1000 mL")

    def test_objectview_update(self):
        object = Object.objects.get(name="RA 100 gr")
        url = reverse("laboratory:objectview_update", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": object.pk})
        data = {
            "name": "RA Paquete 100 gr",
            "features": [1],
            "code": "RA43",
            "synonym": "RA",
            "is_public": True,
            "model": "RA2022",
            "serie": "Reactive 008",
            "plaque": "RA4300",
            "type": "0"
        }
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_objectview_delete(self):
        object = Object.objects.last()
        url = reverse("laboratory:objectview_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": object.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(object.pk, Object.objects.values_list('pk'))
        success_url = reverse("laboratory:objectview_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response, success_url)

    def test_objectview_create(self):
        total_obj = Object.objects.all().count()
        url = reverse("laboratory:objectview_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        data = {
            "name": "Ácido Clorhídrico",
            "features": [1],
            "code": "AC",
            "synonym": "Ácido",
            "is_public": True,
            "model": "AC2022",
            "serie": "Ácido 222",
            "plaque": "AC4300",
            "type": "1"
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(total_obj+1, Object.objects.all().count())
        success_url = reverse("laboratory:objectview_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})+"?type_id=1"
        self.assertRedirects(response, success_url)

    def test_objects_list_report(self):
        data = {
            "type_id": "1"
        }
        url = reverse("laboratory:reports_objects_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, data=data)
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