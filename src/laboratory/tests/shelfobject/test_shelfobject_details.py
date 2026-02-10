from django.urls import reverse
from .test_shelfobject_api import ShelfObjectAPITest


class ShelfObjectDetailsTest(ShelfObjectAPITest):

    def test_shelfobject_api_details_with_substance_characteristics_and_features(self):
        """
        Test for API details success case with substance characteristics and features
        pk = 2 -> Shelf Object related to substance characteristics with pk = 1
        """
        response = self.client.get(
            reverse(
                "laboratory:api-shelfobject-details",
                kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id, "pk": 2},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response=response, text="Cal 100 gr")
        self.assertContains(response=response, text="CA777")
        self.assertContains(response=response, text="Reactivo")
        self.assertContains(
            response=response, text="security_sheets/test_characteristics.pdf"
        )
        self.assertContains(response=response, text="CHO")

    def test_shelfobject_api_details_without_features(self):
        """
        Test for API details success case without features
        """
        response = self.client.get(
            reverse(
                "laboratory:api-shelfobject-details",
                kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id, "pk": 1},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response=response, text='"name": "Tanque 1000 mL"')
        self.assertNotContains(response=response, text='"object_features":null')

    def test_shelfobject_api_details_without_substance_characteristics(self):
        """
        Test for API details success case without substance characteristics
        Shelf Object with pk = 3 that doesn't have any features key
        """
        response = self.client.get(
            reverse(
                "laboratory:api-shelfobject-details",
                kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id, "pk": 3},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response=response, text='"name": "Cal 100 gr"')
        self.assertNotContains(
            response=response, text='"substance_characteristics":null'
        )

    def test_shelfobject_api_details_shelf_object_only_with_required_fields(self):
        """
        Test for API details when an object with has no laboratory and only have required fields
        Shelf Object with pk = 4 that only have the required fields
        """

        response = self.client.get(
            reverse(
                "laboratory:api-shelfobject-details",
                kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id, "pk": 4},
            )
        )
        self.assertEqual(response.status_code, 404)
        pass

    def test_shelfobject_api_details_not_found(self):
        """
        Test for API details shelf object not found
        pk = 115, Shelf Object that doesn't exist in the DB
        """
        response = self.client.get(
            reverse(
                "laboratory:api-shelfobject-details",
                kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id, "pk": 115},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_shelfobject_api_details_shelfobject_not_in_laboratory(self):
        """
        Test for API details when shelf object doesn't belong to laboratory
        lab_pk = 3, PK that exists in the DB but doesn't contain the pk given
        pk = Shelf Object that belongs to lab_pk = 1
        """
        response = self.client.get(
            reverse(
                "laboratory:api-shelfobject-details",
                kwargs={"org_pk": self.org_pk, "lab_pk": 3, "pk": 1},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_shelfobject_api_details_user_with_permissions_forbidden(self):
        """
        Test for API details when user have permissions in their organization
        but don't have access to the specified laboratory/organization
        """
        self.client.logout()
        self.client.force_login(self.user2)
        response = self.client.get(
            reverse(
                "laboratory:api-shelfobject-details",
                kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id, "pk": 1},
            )
        )
        self.assertEqual(response.status_code, 403)

    def test_shelfobject_api_details_user_without_permissions_forbidden(self):
        """
        Test for API details when user don't have any permissions and
        don't have access to the specified laboratory/organization
        """
        self.client.logout()
        self.client.force_login(self.user3)
        response = self.client.get(
            reverse(
                "laboratory:api-shelfobject-details",
                kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id, "pk": 1},
            )
        )
        self.assertEqual(response.status_code, 403)

    def test_shelfobject_api_details_anonymous_user_forbidden(self):
        """
        Test for API details when anonymous user tries to access
        """
        self.client.logout()
        response = self.client.get(
            reverse(
                "laboratory:api-shelfobject-details",
                kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id, "pk": 1},
            )
        )
        self.assertEqual(response.status_code, 403)
