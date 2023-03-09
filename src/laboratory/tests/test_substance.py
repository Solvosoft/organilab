from django.urls import reverse
from laboratory.tests.utils import BaseLaboratorySetUpTest
from sga.models import ReviewSubstance


class SubstanceViewTest(BaseLaboratorySetUpTest):

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

class ReviewSubstanceViewTest(BaseLaboratorySetUpTest):

    def test_api_reviewsubstance_list(self):
        url = reverse("laboratory:api-reviewsubstance-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_api_reviewsubstance_detail(self):
        review_subtance = ReviewSubstance.objects.first()
        data = {
            "org_pk": self.org.pk,
            "showapprove": "True",
        }
        url = reverse("laboratory:api-reviewsubstance-detail", kwargs={"pk": review_subtance.pk, })
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)