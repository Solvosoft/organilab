from django.urls import reverse
from .test_shelfobject_api import ShelfObjectAPITest
from laboratory.models import ShelfObjectObservation
from django.contrib.admin.models import LogEntry


class ShelfObjectCreateCommentsTest(ShelfObjectAPITest):

    def test_shelfobject_api_create_comments(self):
        """
        Test for API create_comments when all the data is given correctly
        """
        data = {
            "action_taken": "Object Change",
            "description": "Test Comment for testing",
            "prefix": "",
        }
        response = self.client.post(
            reverse(
                "laboratory:api-shelfobject-create-comments",
                kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id, "pk": 1},
            ),
            data=data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        observation_created = ShelfObjectObservation.objects.last()
        self.assertEqual(
            ShelfObjectObservation.objects.filter(shelf_object=1).count(), 3
        )
        self.assertEqual(observation_created.description, "Test Comment for testing")
        self.assertEqual(observation_created.action_taken, "Object Change")
        log = LogEntry.objects.first()
        self.assertEqual(log.object_id, str(observation_created.id))
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action_flag, 1)

    def test_shelfobject_api_create_comments_wrong_content_type(self):
        """
        Test for API create_comments where the content_type isn't application/json
        content_type = 'application/octet-stream'
        """
        data = {
            "action_taken": "Object Change",
            "description": "Test Comment for testing",
            "prefix": "",
        }
        response = self.client.post(
            reverse(
                "laboratory:api-shelfobject-create-comments",
                kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id, "pk": 1},
            ),
            data=data,
            content_type="application/octet-stream",
        )
        self.assertEqual(response.status_code, 415)

    def test_shelfobject_api_create_comments_no_description(self):
        """
        Test for API create_comments when description is None
        """
        data = {"action_taken": "Object Change", "description": "", "prefix": ""}
        response = self.client.post(
            reverse(
                "laboratory:api-shelfobject-create-comments",
                kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id, "pk": 1},
            ),
            data=data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_shelfobject_api_create_comments_no_action_taken(self):
        """
        Test for API create_comments when action_taken is None
        """
        data = {
            "action_taken": "",
            "description": "Test Comment for testing",
            "prefix": "",
        }
        response = self.client.post(
            reverse(
                "laboratory:api-shelfobject-create-comments",
                kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id, "pk": 1},
            ),
            data=data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_shelfobject_api_create_comments_not_found(self):
        """
        Test for API create_comments shelf object not found
        pk = 115, Shelf Object that doesn't exist in the DB
        """
        data = {
            "action_taken": "Object Change",
            "description": "Test Comment for testing",
            "prefix": "",
        }
        response = self.client.post(
            reverse(
                "laboratory:api-shelfobject-create-comments",
                kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id, "pk": 115},
            ),
            data=data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_shelfobject_api_create_comments_shelfobject_not_in_laboratory(self):
        """
        Test for API create_comments when shelf object doesn't belong to laboratory
        lab_pk = 3, PK that exists in the DB but doesn't contain the pk given
        pk = Shelf Object that belongs to lab_pk = 1
        """
        data = {
            "action_taken": "Object Change",
            "description": "Test Comment for testing",
            "prefix": "",
        }
        response = self.client.post(
            reverse(
                "laboratory:api-shelfobject-create-comments",
                kwargs={"org_pk": self.org_pk, "lab_pk": 3, "pk": 1},
            ),
            data=data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_shelfobject_api_create_comments_user_with_permissions_forbidden(self):
        """
        Test for API create_comments when user have permissions in their organization
        but don't have access to the specified laboratory/organization
        """
        self.client.logout()
        self.client.force_login(self.user2)
        data = {
            "action_taken": "Object Change",
            "description": "Test Comment for testing",
            "prefix": "",
        }
        response = self.client.post(
            reverse(
                "laboratory:api-shelfobject-create-comments",
                kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id, "pk": 1},
            ),
            data=data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_shelfobject_api_create_comments_user_without_permissions_forbidden(self):
        """
        Test for API create_comments when user don't have any permissions and
        don't have access to the specified laboratory/organization
        """
        self.client.logout()
        self.client.force_login(self.user3)
        data = {
            "action_taken": "Object Change",
            "description": "Test Comment for testing",
            "prefix": "",
        }
        response = self.client.post(
            reverse(
                "laboratory:api-shelfobject-create-comments",
                kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id, "pk": 1},
            ),
            data=data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_shelfobject_api_create_comments_anonymous_user_forbidden(self):
        """
        Test for API create_comments when anonymous user tries to access
        """
        self.client.logout()
        data = {
            "action_taken": "Object Change",
            "description": "Test Comment for testing",
            "prefix": "",
        }
        response = self.client.post(
            reverse(
                "laboratory:api-shelfobject-create-comments",
                kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id, "pk": 1},
            ),
            data=data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.client.force_login(self.user)
