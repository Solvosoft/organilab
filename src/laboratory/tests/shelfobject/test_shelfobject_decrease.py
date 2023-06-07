from django.urls import reverse

from laboratory.models import ShelfObject
from laboratory.tests.utils import ShelfObjectSetUp
from laboratory.utils import check_user_access_kwargs_org_lab

class ShelfObjectDecreaseViewTest(ShelfObjectSetUp):
    """
    This test does decrease shelfobject request by post method and action 'fill_decrease_shelfobject'
        located in laboratory/api/shelfobject.py --> ShelfObjectViewSet generic view set class.
    """

    def setUp(self):
        super().setUp()
        self.shelf_object = ShelfObject.objects.get(pk=1)
        self.old_quantity = self.shelf_object.quantity
        self.data = {
            "amount": 2,
            "description": "Caso de estudio",
            "shelf_object": self.shelf_object.pk
        }
        self.url = reverse("laboratory:api-shelfobject-fill-decrease-shelfobject", kwargs={"org_pk": self.org1.pk, "lab_pk": self.lab1_org1.pk})

    def test_shelfobject_decrease_case1(self):
        """
        #EXPECTED CASE(User in this organization with permissions try to decrease shelfobject)

        CHECK TESTS
        1) Check response status code equal to 200.
        2) Check if user has permission to access this organization and laboratory.
        3) Check if new quantity is equal to (old quantity - amount)
        4) Check if new quantity is not equal to old quantity
        """
        response = self.client1_org1.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(check_user_access_kwargs_org_lab(self.org1.pk, self.lab1_org1.pk, self.user1_org1))

        shelf_object = ShelfObject.objects.get(pk=self.data["shelf_object"])
        new_quantity = shelf_object.quantity
        self.assertEqual(new_quantity, self.old_quantity - self.data["amount"])
        self.assertNotEqual(new_quantity, self.old_quantity)

    def test_shelfobject_decrease_case2(self):
        """
        #UNEXPECTED CASE, BUT POSSIBLE(User to other organization without permissions try to decrease shelfobject)

        CHECK TESTS
        1) Check response status code equal to 403.
        2) Check if user doesn't have permission to access this organization and laboratory.
        3) Check if new quantity is not equal to (old quantity - amount)
        4) Check if new quantity is equal to old quantity
        """
        response = self.client2_org2.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(check_user_access_kwargs_org_lab(self.org1.pk, self.lab1_org1.pk, self.user2_org2))

        shelf_object = ShelfObject.objects.get(pk=self.data["shelf_object"])
        new_quantity = shelf_object.quantity
        self.assertNotEqual(new_quantity, self.old_quantity - self.data["amount"])
        self.assertEqual(new_quantity, self.old_quantity)