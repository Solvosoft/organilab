from django.urls import reverse

from laboratory.models import ShelfObject, Shelf, Object
from laboratory.tests.utils import ShelfObjectSetUp
from laboratory.utils import check_user_access_kwargs_org_lab


class ShelfObjectMoveViewTest(ShelfObjectSetUp):
    """
    These tests do move shelfobject to other shelf request by post method and action 'move_shelfobject_to_shelf'
        located in laboratory/api/shelfobject.py --> ShelfObjectViewSet generic view set class.
    """

    def setUp(self):
        super().setUp()
        self.org = self.org1
        self.lab = self.lab1_org1
        self.user = self.user1_org1
        self.client = self.client1_org1
        self.shelf_object = ShelfObject.objects.get(pk=6)
        self.shelf_object_material = ShelfObject.objects.get(pk=4)
        self.shelf_object_equipment = ShelfObject.objects.get(pk=5)
        self.available_container = ShelfObject.objects.get(pk=3)
        self.container_for_cloning = Object.objects.get(pk=3)
        self.old_shelf = self.shelf_object.shelf
        self.new_shelf_3 = Shelf.objects.get(pk=1)
        self.new_shelf_5 = Shelf.objects.get(pk=3)
        self.new_shelf_4 = Shelf.objects.get(pk=4)
        self.data_shelf_3 = {
            "lab_room": self.new_shelf_3.furniture.labroom.pk,
            "furniture": self.new_shelf_3.furniture.pk,
            "shelf": self.new_shelf_3.pk,
            "shelf_object": self.shelf_object.pk,
            "container_select_option": "use_source",
            "container_for_cloning": "",
            "available_container": "",
        }
        self.data_shelf_4 = {
            "lab_room": self.new_shelf_4.furniture.labroom.pk,
            "furniture": self.new_shelf_4.furniture.pk,
            "shelf": self.new_shelf_4.pk,
            "shelf_object": self.shelf_object.pk,
        }
        self.data_shelf_5 = {
            "lab_room": self.new_shelf_3.furniture.labroom.pk,
            "furniture": self.new_shelf_3.furniture.pk,
            "shelf": self.new_shelf_3.pk,
            "shelf_object": self.shelf_object_material.pk,
        }
        self.url = reverse(
            "laboratory:api-shelfobject-move-shelfobject-to-shelf",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk},
        )

    def test_shelfobject_move_case1(self):
        """
        #EXPECTED CASE(User 1 in this organization with permissions try to move shelfobject to other shelf)
        container -- > 'use_source'

        CHECK TESTS
        1) Check response status code equal to 200.
        2) Check if user has permission to access this organization and laboratory.
        3) Check if pk laboratory related to this shelfobject is equal to declared pk laboratory in url.
        4) Check if pk measurement unit related to this shelfobject is equal to measurement unit related to new shelf.
        5) Check if pk shelfobject is not in old shelf.
        6) Check if pk shelfobject is in new shelf.
        """
        data = self.data_shelf_3.copy()
        data["shelf"] = 3
        response = self.client.post(self.url, data=data)
        response = self.client.post(self.url, data=self.data_shelf_3)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user)
        )
        self.assertEqual(
            self.shelf_object.shelf.furniture.labroom.laboratory.pk, self.lab.pk
        )
        self.assertEqual(
            self.shelf_object.measurement_unit.pk, self.new_shelf_3.measurement_unit.pk
        )
        self.assertNotIn(
            self.shelf_object.pk,
            list(self.old_shelf.get_objects().values_list("pk", flat=True)),
        )
        self.assertIn(
            self.shelf_object.pk,
            list(self.new_shelf_3.get_objects().values_list("pk", flat=True)),
        )

    def test_shelfobject_move_case2(self):
        """
        #UNEXPECTED CASE, BUT POSSIBLE(User 2 to other organization without permissions try to move shelfobject to other shelf)

        CHECK TESTS
        1) Check response status code equal to 403.
        2) Check if user doesn't have permission to access this organization and laboratory.
        3) Check if pk laboratory related to this shelfobject is equal to declared pk laboratory in url.
        4) Check if pk shelfobject is in old shelf.
        5) Check if pk shelfobject is not in new shelf.
        """
        self.client = self.client2_org2
        self.user = self.user2_org2
        response = self.client.post(self.url, data=self.data_shelf_3)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user)
        )
        self.assertEqual(
            self.shelf_object.shelf.furniture.labroom.laboratory.pk, self.lab.pk
        )
        self.assertIn(
            self.shelf_object.pk,
            list(self.old_shelf.get_objects().values_list("pk", flat=True)),
        )
        self.assertNotIn(
            self.shelf_object.pk,
            list(self.new_shelf_3.get_objects().values_list("pk", flat=True)),
        )

    def test_shelfobject_move_case3(self):
        """
        #UNEXPECTED CASE, BUT POSSIBLE(User 1 in this organization with permissions try to move shelfobject to
         other shelf in other laboratory in this same organization)

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if user has access permission to access this organization and laboratory.
        3) Check if pk laboratory related to this shelfobject is equal to declared pk laboratory in url.
        4) Check if pk laboratoryrelated to this shelfobject is not equal to pk laboratory related to new shelf.
        5) Check if pk shelfobject is not in old shelf.
        6) Check if pk shelfobject is in new shelf.
        """
        response = self.client.post(self.url, data=self.data_shelf_4)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user)
        )
        self.assertEqual(
            self.shelf_object.shelf.furniture.labroom.laboratory.pk, self.lab.pk
        )
        self.assertNotEqual(
            self.shelf_object.shelf.furniture.labroom.laboratory.pk,
            self.new_shelf_4.furniture.labroom.laboratory.pk,
        )
        self.assertIn(
            self.shelf_object.pk,
            list(self.old_shelf.get_objects().values_list("pk", flat=True)),
        )
        self.assertNotIn(
            self.shelf_object.pk,
            list(self.new_shelf_4.get_objects().values_list("pk", flat=True)),
        )

    def test_shelfobject_move_case4(self):
        """
        #UNEXPECTED CASE, BUT POSSIBLE(User 2 without permissions in this organization try to move shelfobject to
         other shelf in other laboratory in this same organization)

        CHECK TESTS
        1) Check response status code equal to 403.
        2) Check if user doesn't have permission to access this organization and laboratory.
        3) Check if pk laboratory related to this shelfobject is equal to declared pk laboratory in url.
        4) Check if pk laboratoryrelated to this shelfobject is not equal to pk laboratory related to new shelf.
        5) Check if pk shelfobject is not in old shelf.
        6) Check if pk shelfobject is in new shelf.
        """
        self.client = self.client2_org2
        self.user = self.user2_org2
        response = self.client.post(self.url, data=self.data_shelf_4)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user)
        )
        self.assertEqual(
            self.shelf_object.shelf.furniture.labroom.laboratory.pk, self.lab.pk
        )
        self.assertNotEqual(
            self.shelf_object.shelf.furniture.labroom.laboratory.pk,
            self.new_shelf_4.furniture.labroom.laboratory.pk,
        )
        self.assertIn(
            self.shelf_object.pk,
            list(self.old_shelf.get_objects().values_list("pk", flat=True)),
        )
        self.assertNotIn(
            self.shelf_object.pk,
            list(self.new_shelf_4.get_objects().values_list("pk", flat=True)),
        )

    def test_shelfobject_move_case5(self):
        """
        #EXPECTED CASE(User 1 in this organization with permissions try to move shelfobject to other shelf)
        Container ---> 'new_based_source'

        CHECK TESTS
        1) Check response status code equal to 200.
        2) Check if user has permission to access this organization and laboratory.
        3) Check if pk laboratory related to this shelfobject is equal to declared pk laboratory in url.
        4) Check if pk measurement unit related to this shelfobject is equal to measurement unit related to new shelf.
        5) Check if pk shelfobject is not in old shelf.
        6) Check if pk shelfobject is in new shelf.
        """
        data = self.data_shelf_3
        data["shelf"] = 1
        data["container_select_option"] = "new_based_source"
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user)
        )
        self.assertEqual(
            self.shelf_object.shelf.furniture.labroom.laboratory.pk, self.lab.pk
        )
        self.assertEqual(
            self.shelf_object.measurement_unit.pk, self.new_shelf_3.measurement_unit.pk
        )
        self.assertNotIn(
            self.shelf_object.pk,
            list(self.old_shelf.get_objects().values_list("pk", flat=True)),
        )
        self.assertIn(
            self.shelf_object.pk,
            list(self.new_shelf_3.get_objects().values_list("pk", flat=True)),
        )

    def test_shelfobject_move_case6(self):
        """
        #EXPECTED CASE(User 1 in this organization with permissions try to move shelfobject to other shelf)
        Reactive Object
        Container ---> 'clone'

        CHECK TESTS
        1) Check response status code equal to 200.
        2) Check if user has permission to access this organization and laboratory.
        3) Check if pk laboratory related to this shelfobject is equal to declared pk laboratory in url.
        4) Check if pk measurement unit related to this shelfobject is equal to measurement unit related to new shelf.
        5) Check if pk shelfobject is not in old shelf.
        6) Check if pk shelfobject is in new shelf.
        """
        data = self.data_shelf_3
        data.update(
            {
                "container_select_option": "clone",
                "container_for_cloning": self.container_for_cloning.pk,
                "shelf": 1,
            }
        )
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user)
        )
        self.assertEqual(
            self.shelf_object.shelf.furniture.labroom.laboratory.pk, self.lab.pk
        )
        self.assertEqual(
            self.shelf_object.measurement_unit.pk, self.new_shelf_3.measurement_unit.pk
        )
        self.assertNotIn(
            self.shelf_object.pk,
            list(self.old_shelf.get_objects().values_list("pk", flat=True)),
        )
        self.assertIn(
            self.shelf_object.pk,
            list(self.new_shelf_3.get_objects().values_list("pk", flat=True)),
        )

    def test_shelfobject_move_case7(self):
        """
        #EXPECTED CASE(User 1 in this organization with permissions try to move shelfobject to other shelf)
        Reactive object
        Container ---> 'available'

        CHECK TESTS
        1) Check response status code equal to 200.
        2) Check if user has permission to access this organization and laboratory.
        3) Check if pk laboratory related to this shelfobject is equal to declared pk laboratory in url.
        4) Check if pk measurement unit related to this shelfobject is equal to measurement unit related to new shelf.
        5) Check if pk shelfobject is not in old shelf.
        6) Check if pk shelfobject is in new shelf.
        """
        data = self.data_shelf_3
        data.update(
            {
                "container_select_option": "available",
                "available_container": self.available_container.pk,
                "shelf": 1,
            }
        )
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user)
        )
        self.assertEqual(
            self.shelf_object.shelf.furniture.labroom.laboratory.pk, self.lab.pk
        )
        self.assertEqual(
            self.shelf_object.measurement_unit.pk, self.new_shelf_3.measurement_unit.pk
        )
        self.assertNotIn(
            self.shelf_object.pk,
            list(self.old_shelf.get_objects().values_list("pk", flat=True)),
        )
        self.assertIn(
            self.shelf_object.pk,
            list(self.new_shelf_3.get_objects().values_list("pk", flat=True)),
        )

    def test_shelfobject_move_case8(self):
        """
        #EXPECTED CASE(User 1 in this organization with permissions try to move shelfobject to other shelf)
        Material object

        CHECK TESTS
        1) Check response status code equal to 200.
        2) Check if user has permission to access this organization and laboratory.
        3) Check if pk laboratory related to this shelfobject is equal to declared pk laboratory in url.
        4) Check if pk shelfobject is not in old shelf.
        5) Check if pk shelfobject is in new shelf.
        """
        data = self.data_shelf_5.copy()
        data["shelf"] = 3
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user)
        )
        self.assertEqual(
            self.shelf_object_material.shelf.furniture.labroom.laboratory.pk,
            self.lab.pk,
        )
        self.assertNotIn(
            self.shelf_object_material.pk,
            list(self.old_shelf.get_objects().values_list("pk", flat=True)),
        )
        self.assertIn(
            self.shelf_object_material.pk,
            list(self.new_shelf_5.get_objects().values_list("pk", flat=True)),
        )

    def test_shelfobject_move_case9(self):
        """
        #EXPECTED CASE(User 1 in this organization with permissions try to move shelfobject to other shelf)
        Material object with different measurement unit related to new shelf.

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if user has permission to access this organization and laboratory.
        3) Check if pk laboratory related to this shelfobject is equal to declared pk laboratory in url.
        4) Check if pk shelfobject is in old shelf.
        5) Check if pk shelfobject is not in new shelf.
        """
        old_shelf = self.shelf_object_material.shelf
        data = self.data_shelf_4
        data["shelf_object"] = self.shelf_object_material.pk
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user)
        )
        self.assertEqual(
            self.shelf_object_material.shelf.furniture.labroom.laboratory.pk,
            self.lab.pk,
        )
        self.assertIn(
            self.shelf_object_material.pk,
            list(old_shelf.get_objects().values_list("pk", flat=True)),
        )
        self.assertNotIn(
            self.shelf_object_material.pk,
            list(self.new_shelf_4.get_objects().values_list("pk", flat=True)),
        )

    def test_shelfobject_move_case10(self):
        """
        #EXPECTED CASE(User 1 in this organization with permissions try to move shelfobject to other shelf)
        Equipment object with different measurement unit related to new shelf.

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if user has permission to access this organization and laboratory.
        3) Check if pk laboratory related to this shelfobject is equal to declared pk laboratory in url.
        4) Check if pk shelfobject is in old shelf.
        5) Check if pk shelfobject is not in new shelf.
        """
        old_shelf = self.shelf_object_equipment.shelf
        data = self.data_shelf_4
        data["shelf_object"] = self.shelf_object_equipment.pk
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user)
        )
        self.assertEqual(
            self.shelf_object_equipment.shelf.furniture.labroom.laboratory.pk,
            self.lab.pk,
        )
        self.assertIn(
            self.shelf_object_equipment.pk,
            list(old_shelf.get_objects().values_list("pk", flat=True)),
        )
        self.assertNotIn(
            self.shelf_object_equipment.pk,
            list(self.new_shelf_4.get_objects().values_list("pk", flat=True)),
        )

    def test_shelfobject_move_case11(self):
        """
        #EXPECTED CASE(User 1 in this organization with permissions try to move shelfobject to other shelf)
        Material object with different measurement unit related to new shelf.

        CHECK TESTS
        1) Check response status code equal to 200.
        2) Check if user has permission to access this organization and laboratory.
        3) Check if pk laboratory related to this shelfobject is equal to declared pk laboratory in url.
        4) Check if pk shelfobject is not in old shelf.
        5) Check if pk shelfobject is in new shelf.
        """
        old_shelf = self.shelf_object_material.shelf
        data = self.data_shelf_3
        data["shelf"] = 3
        data["shelf_object"] = self.shelf_object_material.pk
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user)
        )
        self.assertEqual(
            self.shelf_object_material.shelf.furniture.labroom.laboratory.pk,
            self.lab.pk,
        )
        self.assertNotIn(
            self.shelf_object_material.pk,
            list(old_shelf.get_objects().values_list("pk", flat=True)),
        )
        self.assertIn(
            self.shelf_object_material.pk,
            list(self.new_shelf_5.get_objects().values_list("pk", flat=True)),
        )

    def test_shelfobject_move_case12(self):
        """
        #EXPECTED CASE(User 1 in this organization with permissions try to move shelfobject to other shelf)
        Equipment object with different measurement unit related to new shelf.

        CHECK TESTS
        1) Check response status code equal to 200.
        2) Check if user has permission to access this organization and laboratory.
        3) Check if pk laboratory related to this shelfobject is equal to declared pk laboratory in url.
        4) Check if pk shelfobject is not in old shelf.
        5) Check if pk shelfobject is in new shelf.
        """
        old_shelf = self.shelf_object_equipment.shelf
        data = self.data_shelf_3
        data["shelf"] = 3
        data["shelf_object"] = self.shelf_object_equipment.pk
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user)
        )
        self.assertEqual(
            self.shelf_object_equipment.shelf.furniture.labroom.laboratory.pk,
            self.lab.pk,
        )
        self.assertNotIn(
            self.shelf_object_equipment.pk,
            list(old_shelf.get_objects().values_list("pk", flat=True)),
        )
        self.assertIn(
            self.shelf_object_equipment.pk,
            list(self.new_shelf_5.get_objects().values_list("pk", flat=True)),
        )
