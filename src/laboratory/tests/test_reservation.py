from django.urls import reverse
from django.utils.timezone import now

from laboratory.models import ShelfObject
from laboratory.tests.utils import BaseLaboratorySetUpTest
from reservations_management.models import Reservations, ReservedProducts
import json
from dateutil.relativedelta import relativedelta


class ReservationViewTest(BaseLaboratorySetUpTest):
    def test_get_reservations_list(self):
        url = reverse(
            "laboratory:my_reservations",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.context["object_list"].count(), 1)
        self.assertContains(response, "Tanque 1000 mL")
        self.assertEqual(response.status_code, 200)

    def test_fake_reservation_list(self):
        """
        Fake tests
        """
        url = reverse(
            "laboratory:my_reservations",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )
        response = self.client.get(url)
        self.assertNotEqual(response.context["object_list"].count(), 15)
        self.assertNotContains(response, "Bombillo 3U")
        self.assertNotEqual(response.status_code, 302)

    def test_api_individual_reservation_create(self):
        total = Reservations.objects.all().count()
        data = {"user": self.user.pk, "status": 0, "comments": "", "is_massive": False}
        url = reverse("laboratory:api_individual_reservation_create")
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Reservations.objects.all().count(), total + 1)


class ReservedProductViewTest(BaseLaboratorySetUpTest):

    def test_api_reservation_update(self):
        reserved_products = ReservedProducts.objects.first()
        reservation = reserved_products.reservation.pk

        data = {
            "reservation": reservation,
            "status": 3,
        }
        url = reverse(
            "laboratory:api_reservation_update",
            kwargs={
                "pk": reserved_products.pk,
            },
        )
        response = self.client.put(
            url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        content_obj = json.loads(response.content)
        self.assertEqual(content_obj["status"], data["status"])
        self.assertEqual(content_obj["reservation"], data["reservation"])

    def test_api_reservation_delete(self):
        reserved_products = ReservedProducts.objects.last()
        pk = reserved_products.pk
        url = reverse(
            "laboratory:api_reservation_delete",
            kwargs={
                "pk": pk,
            },
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertNotIn(
            pk, list(ReservedProducts.objects.all().values_list("pk", flat=True))
        )
