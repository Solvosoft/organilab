from django.urls import reverse

from laboratory.models import ShelfObject, Shelf
from laboratory.tests.utils import ShelfObjectSetUp
from laboratory.utils import check_user_access_kwargs_org_lab


class MoveShelfObjectViewTest(ShelfObjectSetUp):
    """
    This test does move shelfobject to other shelf request by post method and action 'move_shelfobject_to_shelf'
        located in laboratory/api/shelfobject.py --> ShelfObjectViewSet generic view set class.
    """

    def test_move_object_case1(self):
        """
        #EXPECTED CASE(User in this organization with permissions try to move shelfobject to other shelf)

        CHECK TESTS
        1) Check response status code equal to 200.
        2) Check if user has access permission to request and move this shelfobject to other shelf.
        3) Check if pk laboratory related to this shelfobject is equal to declared pk laboratory in url.
        4) Check if pk measurement unit related to this shelfobject is equal to measurement unit related to new shelf.
        5) Check if pk shelfobject is not in old shelf.
        6) Check if pk shelfobject is in new shelf.
        """
        shelf_object = ShelfObject.objects.get(pk=1)
        old_shelf = shelf_object.shelf
        new_shelf = Shelf.objects.get(pk=3)
        url = reverse("laboratory:api-shelfobject-move-shelfobject-to-shelf", kwargs={"org_pk": self.org1.pk, "lab_pk": self.lab1_org1.pk})
        data = {
            "lab_room": new_shelf.furniture.labroom.pk,
            "furniture": new_shelf.furniture.pk,
            "shelf": new_shelf.pk,
            "shelf_object": shelf_object.pk
        }
        response = self.client1_org1.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(check_user_access_kwargs_org_lab(self.org1.pk, self.lab1_org1.pk, self.user1_org1))
        self.assertEqual(shelf_object.shelf.furniture.labroom.laboratory.pk, self.lab1_org1.pk)
        self.assertEqual(shelf_object.measurement_unit.pk , new_shelf.measurement_unit.pk)
        self.assertNotIn(shelf_object.pk, list(old_shelf.get_objects().values_list('pk', flat=True)))
        self.assertIn(shelf_object.pk, list(new_shelf.get_objects().values_list('pk', flat=True)))

    def test_move_object_case2(self):
        """
        #UNEXPECTED CASE, BUT POSSIBLE(User to other organization without permissions try to move shelfobject to other shelf)

        CHECK TESTS
        1) Check response status code equal to 403.
        2) Check if user doesn't have access permission to request and move this shelfobject to other shelf.
        3) Check if pk shelfobject is in old shelf.
        4) Check if pk shelfobject is not in new shelf.
        """
        shelf_object = ShelfObject.objects.get(pk=1)
        old_shelf = shelf_object.shelf
        new_shelf = Shelf.objects.get(pk=3)
        url = reverse("laboratory:api-shelfobject-move-shelfobject-to-shelf", kwargs={"org_pk": self.org1.pk, "lab_pk": self.lab1_org1.pk})
        data = {
            "lab_room": new_shelf.furniture.labroom.pk,
            "furniture": new_shelf.furniture.pk,
            "shelf": new_shelf.pk,
            "shelf_object": shelf_object.pk
        }
        response = self.client2_org2.post(url, data=data)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(check_user_access_kwargs_org_lab(self.org1.pk, self.lab1_org1.pk, self.user2_org2))
        self.assertIn(shelf_object.pk, list(old_shelf.get_objects().values_list('pk', flat=True)))
        self.assertNotIn(shelf_object.pk, list(new_shelf.get_objects().values_list('pk', flat=True)))


    def test_move_object_case3(self):
        """
        #UNEXPECTED CASE, BUT POSSIBLE(User in this organization with permissions try to move shelfobject to
         other shelf in other laboratory in this same organization)

        CHECK TESTS
        1) Check response status code equal to 400.
        2) Check if pk laboratoryrelated to this shelfobject is not equal to pk laboratory related to new shelf.
        3) Check if pk shelfobject is not in old shelf.
        4) Check if pk shelfobject is in new shelf.
        """
        shelf_object = ShelfObject.objects.get(pk=1)
        old_shelf = shelf_object.shelf
        new_shelf = Shelf.objects.get(pk=4)
        url = reverse("laboratory:api-shelfobject-move-shelfobject-to-shelf", kwargs={"org_pk": self.org1.pk, "lab_pk": self.lab1_org1.pk})
        data = {
            "lab_room": new_shelf.furniture.labroom.pk,
            "furniture": new_shelf.furniture.pk,
            "shelf": new_shelf.pk,
            "shelf_object": shelf_object.pk
        }
        response = self.client1_org1.post(url, data=data)
        self.assertEqual(response.status_code, 400)
        self.assertNotEqual(shelf_object.shelf.furniture.labroom.laboratory.pk, new_shelf.furniture.labroom.laboratory.pk)
        self.assertIn(shelf_object.pk, list(old_shelf.get_objects().values_list('pk', flat=True)))
        self.assertNotIn(shelf_object.pk, list(new_shelf.get_objects().values_list('pk', flat=True)))

    def test_move_object_case4(self):
        """
        #UNEXPECTED CASE, BUT POSSIBLE(User without permissions in this organization try to move shelfobject to
         other shelf in other laboratory in this same organization)

        CHECK TESTS
        1) Check response status code equal to 403.
        2) Check if pk laboratoryrelated to this shelfobject is not equal to pk laboratory related to new shelf.
        3) Check if pk shelfobject is not in old shelf.
        4) Check if pk shelfobject is in new shelf.
        """
        shelf_object = ShelfObject.objects.get(pk=1)
        old_shelf = shelf_object.shelf
        new_shelf = Shelf.objects.get(pk=4)
        url = reverse("laboratory:api-shelfobject-move-shelfobject-to-shelf", kwargs={"org_pk": self.org1.pk, "lab_pk": self.lab1_org1.pk})
        data = {
            "lab_room": new_shelf.furniture.labroom.pk,
            "furniture": new_shelf.furniture.pk,
            "shelf": new_shelf.pk,
            "shelf_object": shelf_object.pk
        }
        response = self.client2_org2.post(url, data=data)
        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(shelf_object.shelf.furniture.labroom.laboratory.pk, new_shelf.furniture.labroom.laboratory.pk)
        self.assertIn(shelf_object.pk, list(old_shelf.get_objects().values_list('pk', flat=True)))
        self.assertNotIn(shelf_object.pk, list(new_shelf.get_objects().values_list('pk', flat=True)))