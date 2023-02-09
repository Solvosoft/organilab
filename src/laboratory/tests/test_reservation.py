from django.urls import reverse
from laboratory.tests.utils import BaseLaboratorySetUpTest


class ReservationViewTest(BaseLaboratorySetUpTest):
    def test_get_reservations_list(self):
        url = reverse("laboratory:my_reservations", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.context['object_list'].count(), 1)
        self.assertContains(response, "Tanque 1000 mL")
        self.assertEqual(response.status_code, 200)

    def test_fake_reservation_list(self):
        """
            Fake tests
        """
        url = reverse("laboratory:my_reservations", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertNotEqual(response.context['object_list'].count(), 15)
        self.assertNotContains(response, "Bombillo 3U")
        self.assertNotEqual(response.status_code, 302)

    def test_api_individual_reservation_create(self):
        url = reverse("laboratory:api_individual_reservation_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class ReservedProductViewTest(BaseLaboratorySetUpTest):

    def test_date_validator(self):
        url = reverse("laboratory:date_validator")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_api_reservation_update(self):
        url = reverse("laboratory:api_reservation_update")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_api_reservation_delete(self):
        url = reverse("laboratory:api_reservation_delete")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_api_reservation_create(self):
        url = reverse("laboratory:api_reservation_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_api_reservation_detail(self):
        url = reverse("laboratory:api_reservation_detail")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class ProductViewTest(BaseLaboratorySetUpTest):

    def test_object_reservation(self):
        url = reverse("laboratory:object_reservation", kwargs={'modelpk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)