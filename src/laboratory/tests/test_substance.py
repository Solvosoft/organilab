from django.urls import reverse
from laboratory.tests.utils import BaseLaboratorySetUpTest


class ReviewSubstanceViewTest(BaseLaboratorySetUpTest):

    def test_api_approved_reviewsubstance_list_set_limit(self):
        url = reverse("sga:api-reviewsubstance-list", kwargs={"org_pk": self.org.pk})
        data = {"showapprove": "True", "offset": 0, "limit": 50}
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cal")

    def test_api_notapproved_reviewsubstance_list_set_limit(self):
        url = reverse("sga:api-reviewsubstance-list", kwargs={"org_pk": self.org.pk})
        data = {"showapprove": "False", "offset": 0, "limit": 50}
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sulfuro de calcio")

    def test_api_approved_reviewsubstance_list_default_limit(self):
        url = reverse("sga:api-reviewsubstance-list", kwargs={"org_pk": self.org.pk})
        data = {"showapprove": "True"}
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Cal", response.content.decode())

    def test_api_notapproved_reviewsubstance_list_default_limit(self):
        url = reverse("sga:api-reviewsubstance-list", kwargs={"org_pk": self.org.pk})
        data = {"showapprove": "False"}
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Sulfuro de calcio", response.content.decode())

    def test_disposal_substance(self):
        url = reverse("laboratory:disposal_substance", kwargs={"org_pk": self.org.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vick Lab")
