from dateutil.relativedelta import relativedelta
from django.urls import reverse
from django.utils.timezone import now
from laboratory.models import ShelfObject
from laboratory.tests.utils import ShelfObjectSetUp
from laboratory.utils import check_user_access_kwargs_org_lab
from reservations_management.models import ReservedProducts, SELECTED


class ShelfObjectReserveViewTest(ShelfObjectSetUp):
    """
    This test does increase shelfobject request by post method and action 'reserve'
        located in laboratory/api/shelfobject.py --> ShelfObjectViewSet generic view set class.
    """

    def setUp(self):
        super().setUp()
        self.org = self.org1
        self.lab = self.lab1_org1
        self.user = self.user1_org1
        self.client = self.client1_org1
        self.shelf_object = ShelfObject.objects.get(pk=1)
        self.initial_date = now() + relativedelta(days=+100)
        self.final_date = now() + relativedelta(days=+200)
        self.data = {
            "amount_required": 2,
            "initial_date": self.initial_date.strftime("%Y-%m-%d %H:%M"),
            "final_date": self.final_date.strftime("%Y-%m-%d %H:%M"),
            "shelf_object": self.shelf_object.pk
        }
        self.filters = {
            "initial_date__date": self.initial_date.date(),
            "final_date__date": self.final_date.date(),
            "amount_required": self.data['amount_required'],
            "shelf_object": self.data['shelf_object'],
            "status": SELECTED,
            "user": self.user
        }

        self.url = reverse("laboratory:api-shelfobject-reserve", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})

    def test_shelfobject_reserve_case1(self):
        """
        #EXPECTED CASE(User 1 in this organization with permissions try to reserve shelfobject)

        CHECK TESTS
        1) Check response status code equal to 200.
        2) Check if user has permission to access this organization and laboratory.
        3) Check if pk laboratory related to this shelfobject is equal to declared pk laboratory in url.
        4) Check if reserved product instance was created.
        """
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))
        self.assertEqual(self.shelf_object.shelf.furniture.labroom.laboratory.pk, self.lab.pk)

        reserved_products = ReservedProducts.objects.filter(**self.filters).distinct()
        self.assertTrue(reserved_products.exists())

    def test_shelfobject_reserve_case2(self):
        """
        #UNEXPECTED CASE, BUT POSSIBLE(User 2 to other organization without permissions try to reserve shelfobject)

        CHECK TESTS
        1) Check response status code equal to 403.
        2) Check if user doesn't have permission to access this organization and laboratory.
        3) Check if pk laboratory related to this shelfobject is equal to declared pk laboratory in url.
        4) Check if reserved product instance wasn't created.
        """
        self.client = self.client2_org2
        self.user = self.user2_org2
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))
        self.assertEqual(self.shelf_object.shelf.furniture.labroom.laboratory.pk, self.lab.pk)

        self.filters.update({"user": self.user})
        reserved_products = ReservedProducts.objects.filter(**self.filters).distinct()
        self.assertFalse(reserved_products.exists())
