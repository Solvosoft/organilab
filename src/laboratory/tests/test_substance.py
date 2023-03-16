from django.urls import reverse
from laboratory.tests.utils import BaseLaboratorySetUpTest

class ReviewSubstanceViewTest(BaseLaboratorySetUpTest):

    def test_api_reviewsubstance_list(self):
        url = reverse("laboratory:api-reviewsubstance-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)