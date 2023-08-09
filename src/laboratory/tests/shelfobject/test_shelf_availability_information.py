from django.urls import reverse

from laboratory.models import ShelfObject, Shelf
from laboratory.shelfobject.serializers import ShelfSerializer
from laboratory.tests.utils import ShelfSetUp
from laboratory.utils import check_user_access_kwargs_org_lab
import json

class AvailabilityShelfInformationViewTest(ShelfSetUp):
    """

    """

    def setUp(self):
        super().setUp()
        self.org = self.org1
        self.lab = self.lab1_org1
        self.user = self.user1_org1
        self.client = self.client1_org1
        self.shelf = Shelf.objects.get(pk=1)
        self.shelf_object = ShelfObject.objects.get(pk=1)
        self.data = {
            "shelf": self.shelf.pk,
            "position": "top"
        }
        self.url = reverse("laboratory:api-shelfobject-shelf-availability-information", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})

    def test_get_shelf_availability_information_user_with_permissions(self):
        """
        """

        shelf = Shelf.objects.get(pk=self.data['shelf'])
        percentage_hyphen_format = shelf.infinity_quantity or not shelf.measurement_unit
        shelf_serializer_data = ShelfSerializer(shelf, context={'position': self.data['position']}).data
        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))

        content_obj = json.loads(response.content)
        self.assertEqual(shelf_serializer_data['percentage_storage_status'], content_obj['percentage_storage_status'])

        if percentage_hyphen_format:
            self.assertFalse("%" in content_obj['percentage_storage_status'])
        else:
            self.assertTrue("%" in content_obj['percentage_storage_status'])


    def test_get_shelf_availability_information_user_without_permissions(self):
        """
        """
        self.client = self.client2_org2
        self.user = self.user2_org2
        response = self.client.get(self.url, data=self.data)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))

        content_obj = json.loads(response.content)

        self.assertTrue("detail" in content_obj)
