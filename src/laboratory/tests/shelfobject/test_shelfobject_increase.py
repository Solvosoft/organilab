from django.urls import reverse

from laboratory.models import ShelfObject, Provider
from laboratory.tests.utils import ShelfObjectSetUp
from laboratory.utils import check_user_access_kwargs_org_lab


class ShelfObjectIncreaseViewTest(ShelfObjectSetUp):
    """
    This test does increase shelfobject request by post method and action 'fill_increase_shelfobject'
        located in laboratory/api/shelfobject.py --> ShelfObjectViewSet generic view set class.
    """

    def setUp(self):
        super().setUp()
        self.org = self.org1
        self.lab = self.lab1_org1
        self.user = self.user1_org1
        self.client = self.client1_org1
        self.shelf_object = ShelfObject.objects.get(pk=1)
        self.shelf_object_material = ShelfObject.objects.get(pk=4)
        self.shelf_object_equipment = ShelfObject.objects.get(pk=5)
        self.shelf = self.shelf_object.shelf
        self.provider = Provider.objects.get(pk=1)
        self.old_quantity = self.shelf_object.quantity
        self.data = {
            "amount": 2,
            "bill": "905678",
            "provider": self.provider.pk,
            "shelf_object": self.shelf_object.pk
        }
        self.total = self.shelf.get_total_refuse(
            include_containers=False, measurement_unit=self.shelf_object.measurement_unit) \
                     + self.data["amount"]
        self.url = reverse("laboratory:api-shelfobject-fill-increase-shelfobject", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})

    def test_shelfobject_increase_case1(self):
        """
        #EXPECTED CASE(User 1 in this organization with permissions try to increase shelfobject)

        CHECK TESTS
        1) Check response status code equal to 200.
        2) Check if user has permission to access this organization and laboratory.
        3) Check if total_quantity is less or equal than shelf storage capacity.
        4) Check if new quantity is equal to (old quantity + amount)
        5) Check if new quantity is not equal to old quantity
        """

        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))
        self.assertTrue(self.total <= self.shelf.quantity)

        shelf_object = ShelfObject.objects.get(pk=self.data["shelf_object"])
        new_quantity = shelf_object.quantity
        self.assertEqual(new_quantity, self.old_quantity + self.data["amount"])
        self.assertNotEqual(new_quantity, self.old_quantity)

    def test_shelfobject_increase_case2(self):
        """
        #UNEXPECTED CASE, BUT POSSIBLE(User 2 to other organization without permissions try to increase shelfobject)

        CHECK TESTS
        1) Check response status code equal to 403.
        2) Check if user doesn't have permission to access this organization and laboratory.
        3) Check if total_quantity greater than shelf storage capacity.
        4) Check if new quantity is not equal to (old quantity + amount)
        5) Check if new quantity is equal to old quantity
        """
        self.client = self.client2_org2
        self.user = self.user2_org2
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))
        self.assertTrue(self.total <= self.shelf.quantity)

        shelf_object = ShelfObject.objects.get(pk=self.data["shelf_object"])
        new_quantity = shelf_object.quantity
        self.assertNotEqual(new_quantity, self.old_quantity + self.data["amount"])
        self.assertEqual(new_quantity, self.old_quantity)

    def test_shelfobject_increase_case3(self):
        """
        #UNEXPECTED CASE, BUT POSSIBLE(User 1 with permissions in this organization try to increase shelfobject
         with provider related to other laboratory)

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if user doesn't have permission to access this organization and laboratory.
        3) Check if total_quantity greater than shelf storage capacity.
        4) Check if new quantity is not equal to (old quantity + amount)
        5) Check if new quantity is equal to old quantity
        """
        self.provider = Provider.objects.get(pk=2)
        self.data['provider'] = self.provider.pk
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))
        self.assertTrue(self.total <= self.shelf.quantity)

        shelf_object = ShelfObject.objects.get(pk=self.data["shelf_object"])
        new_quantity = shelf_object.quantity
        self.assertNotEqual(new_quantity, self.old_quantity + self.data["amount"])
        self.assertEqual(new_quantity, self.old_quantity)


    def test_shelfobject_increase_case4(self):
        """
        #EXPECTED CASE(User 1 in this organization with permissions try to increase shelfobject)
        Material Object

        CHECK TESTS
        1) Check response status code equal to 200.
        2) Check if user has permission to access this organization and laboratory.
        3) Check if total_quantity is less or equal than shelf storage capacity.
        4) Check if new quantity is equal to (old quantity + amount)
        5) Check if new quantity is not equal to old quantity
        """
        data = self.data
        self.old_quantity = self.shelf_object_material.quantity
        data['shelf_object'] = self.shelf_object_material.pk
        self.total = self.shelf_object_material.shelf.get_total_refuse(
            include_containers=False) + self.data["amount"]
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))
        self.assertTrue(self.total <= self.shelf_object_material.shelf.quantity)
        shelf_object = ShelfObject.objects.get(pk=self.data["shelf_object"])
        new_quantity = shelf_object.quantity
        self.assertEqual(new_quantity, self.old_quantity + self.data["amount"])
        self.assertNotEqual(new_quantity, self.old_quantity)

    def test_shelfobject_increase_case5(self):
        """
        #EXPECTED CASE(User 1 in this organization with permissions try to increase shelfobject)
        Equipment Object

        CHECK TESTS
        1) Check response status code equal to 200.
        2) Check if user has permission to access this organization and laboratory.
        3) Check if total_quantity is less or equal than shelf storage capacity.
        4) Check if new quantity is equal to (old quantity + amount)
        5) Check if new quantity is not equal to old quantity
        """
        data = self.data
        self.old_quantity = self.shelf_object_equipment.quantity
        data['shelf_object'] = self.shelf_object_equipment.pk
        self.total = self.shelf_object_equipment.shelf.get_total_refuse(
            include_containers=False) + self.data["amount"]
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))
        self.assertTrue(self.total <= self.shelf_object_equipment.shelf.quantity)
        shelf_object = ShelfObject.objects.get(pk=self.data["shelf_object"])
        new_quantity = shelf_object.quantity
        self.assertEqual(new_quantity, self.old_quantity + self.data["amount"])
        self.assertNotEqual(new_quantity, self.old_quantity)

    def test_shelfobject_increase_case6(self):
        """
        #EXPECTED CASE(User 1 in this organization with permissions try to increase shelfobject)
        Material Object

        CHECK TESTS
        1) Check response status code equal to 403.
        2) Check if user has permission to access this organization and laboratory.
        5) Check if new quantity is equal to old quantity
        """
        data = self.data
        self.old_quantity = self.shelf_object_material.quantity
        data['shelf_object'] = self.shelf_object_material.pk
        self.total = self.shelf_object_material.shelf.get_total_refuse(
            include_containers=False)
        self.lab = self.lab3_org1
        self.url = reverse("laboratory:api-shelfobject-fill-increase-shelfobject",
                           kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))
        shelf_object = ShelfObject.objects.get(pk=self.data["shelf_object"])
        new_quantity = shelf_object.quantity
        self.assertEqual(new_quantity, self.old_quantity)

    def test_shelfobject_increase_case7(self):
        """
        #EXPECTED CASE(User 1 in this organization with permissions try to increase shelfobject)
        Equipment Object

        CHECK TESTS
        1) Check response status code equal to 403.
        2) Check if user has permission to access this organization and laboratory.
        5) Check if new quantity is equal to old quantity
        """
        data = self.data
        self.old_quantity = self.shelf_object_equipment.quantity
        data['shelf_object'] = self.shelf_object_equipment.pk
        self.total = self.shelf_object_equipment.shelf.get_total_refuse(
            include_containers=False)
        self.lab = self.lab3_org1
        self.url = reverse("laboratory:api-shelfobject-fill-increase-shelfobject",
                           kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))
        shelf_object = ShelfObject.objects.get(pk=self.data["shelf_object"])
        new_quantity = shelf_object.quantity
        self.assertEqual(new_quantity, self.old_quantity)
