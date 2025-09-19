from django.contrib.admin.models import LogEntry
from laboratory.models import ShelfObjectObservation, ShelfObject
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .test_shelfobject_api import ShelfObjectAPITest
from ...utils import check_user_access_kwargs_org_lab


class ShelfObjectDeleteTest(ShelfObjectAPITest):

    def test_shelfobject_api_delete(self):
        """
        Test for API delete success case, where the data is correctly given
        """

        delete_url = reverse(
            "laboratory:api-shelfobject-delete",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id},
        )
        response = self.client.delete(
            delete_url, data={"shelfobj": 1}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            ShelfObjectObservation.objects.filter(shelf_object=1).count(), 0
        )
        log = LogEntry.objects.first()
        self.assertEqual(log.object_id, "1")
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action_flag, 3)

    def test_shelfobject_api_delete_not_found(self):
        """
        Test for API delete shelf object not found
        shelfobj = 115, Shelf Object that doesn't exist in the DB
        """
        delete_url = reverse(
            "laboratory:api-shelfobject-delete",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id},
        )
        response = self.client.delete(
            delete_url, data={"shelfobj": 115}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_shelfobject_api_delete_shelfobject_not_in_laboratory(self):
        """
        Test for API delete when shelf object doesn't belong to laboratory
        lab_pk = 3, PK that exists in the DB but doesn't contain the pk given
        pk = Shelf Object that belongs to lab_pk = 1
        """
        delete_url = reverse(
            "laboratory:api-shelfobject-delete",
            kwargs={"org_pk": self.org_pk, "lab_pk": 3},
        )
        response = self.client.delete(
            delete_url, data={"shelfobj": 2}, content_type="application/json"
        )
        self.assertContains(
            response=response,
            text=_("Object does not exist in the laboratory."),
            status_code=400,
        )

    def test_shelfobject_api_delete_user_with_permissions_forbidden(self):
        """
        Test for API delete when user have permissions in their organization
        but don't have access to the specified laboratory/organization
        """
        delete_url = reverse(
            "laboratory:api-shelfobject-delete",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id},
        )
        self.client.logout()
        self.client.force_login(self.user2)
        response = self.client.delete(
            delete_url, data={"shelfobj": 1}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)

    def test_shelfobject_api_delete_user_without_permissions_forbidden(self):
        """
        Test for API delete when user don't have any permissions and
        don't have access to the specified laboratory/organization
        """
        delete_url = reverse(
            "laboratory:api-shelfobject-delete",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id},
        )
        self.client.logout()
        self.client.force_login(self.user3)
        response = self.client.delete(
            delete_url, data={"shelfobj": 1}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)

    def test_shelfobject_api_delete_anonymous_user_forbidden(self):
        """
        Test for API delete when anonymous user tries to access
        """
        delete_url = reverse(
            "laboratory:api-shelfobject-delete",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id},
        )
        self.client.logout()
        response = self.client.delete(
            delete_url, data={"shelfobj": 1}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        self.client.force_login(self.user)

    def test_shelfobject_api_delete_wrong_key(self):
        """
        Test for API delete when the data is wrong
        """
        delete_url = reverse(
            "laboratory:api-shelfobject-delete",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id},
        )
        response = self.client.delete(
            delete_url, data={"shelfobj_wrong": 1}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_shelfobject_api_delete_wrong_content_type(self):
        """
        Test for API delete unsupported media type
        content_type = 'application/octet-stream'
        """
        delete_url = reverse(
            "laboratory:api-shelfobject-delete",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id},
        )
        response = self.client.delete(delete_url, data={"shelfobj": 1})
        self.assertEqual(response.status_code, 415)

    def test_delete_reactive_and_container(self):
        """
        Function test api shelf object delete

        - Check response status code 200
        - Check if user has permission to access this organization and laboratory.
        - Check if a specific shelf object inside a laboratory was deleted.
        - Check if a specific shelf object container inside a laboratory was or was not deleted.
        """
        old_total_shelfobject = ShelfObject.objects.all().count()
        shelfobject = ShelfObject.objects.get(pk=8)
        container = shelfobject.container
        delete_url = reverse(
            "laboratory:api-shelfobject-delete",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id},
        )
        data = {"shelfobj": shelfobject.pk, "delete_container": True}
        response = self.client.delete(
            delete_url, data=data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org_pk, self.lab.pk, self.user)
        )
        new_total_shelfobject = ShelfObject.objects.all().count()

        so_exists = ShelfObject.objects.filter(pk=shelfobject.pk).exists()
        self.assertFalse(so_exists)

        if container:

            container_exists = ShelfObject.objects.filter(pk=container.pk).exists()
            if data["delete_container"]:
                self.assertFalse(container_exists)
            else:
                self.assertTrue(container_exists)
        self.assertEqual(old_total_shelfobject - 2, new_total_shelfobject)

    def test_delete_reactive_exclude_container(self):
        """
        - Check response status code 200
        - Check if user has permission to access this organization and laboratory.
        - Check if a specific shelf object inside a laboratory was deleted.
        - Check if a specific shelf object container inside a laboratory was or was not deleted.
        """
        old_total_shelfobject = ShelfObject.objects.all().count()
        shelfobject = ShelfObject.objects.get(pk=10)
        container = shelfobject.container
        delete_url = reverse(
            "laboratory:api-shelfobject-delete",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id},
        )
        data = {"shelfobj": shelfobject.pk, "delete_container": False}
        response = self.client.delete(
            delete_url, data=data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org_pk, self.lab.pk, self.user)
        )
        new_total_shelfobject = ShelfObject.objects.all().count()

        so_exists = ShelfObject.objects.filter(pk=shelfobject.pk).exists()
        self.assertFalse(so_exists)

        if container:

            container_exists = ShelfObject.objects.filter(pk=container.pk).exists()
            if data["delete_container"]:
                self.assertFalse(container_exists)
            else:
                self.assertTrue(container_exists)

        self.assertEqual(old_total_shelfobject - 1, new_total_shelfobject)

    def test_delete_reactive_without_container(self):
        """
        Function test api shelf object delete

        - Check response status code 200
        - Check if user has permission to access this organization and laboratory.
        - Check if a specific shelf object inside a laboratory was deleted.
        """
        old_total_shelfobject = ShelfObject.objects.all().count()
        shelfobject = ShelfObject.objects.get(pk=11)
        delete_url = reverse(
            "laboratory:api-shelfobject-delete",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id},
        )
        data = {"shelfobj": shelfobject.pk}
        response = self.client.delete(
            delete_url, data=data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org_pk, self.lab.pk, self.user)
        )
        new_total_shelfobject = ShelfObject.objects.all().count()

        so_exists = ShelfObject.objects.filter(pk=shelfobject.pk).exists()
        self.assertFalse(so_exists)
        self.assertEqual(old_total_shelfobject - 1, new_total_shelfobject)

    def test_delete_material_obj(self):
        """
        Function test api shelf object delete

        - Check response status code 200
        - Check if user has permission to access this organization and laboratory.
        - Check if a specific shelf object inside a laboratory was deleted.
        """
        old_total_shelfobject = ShelfObject.objects.all().count()
        shelfobject = ShelfObject.objects.get(pk=12)
        delete_url = reverse(
            "laboratory:api-shelfobject-delete",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id},
        )
        data = {"shelfobj": shelfobject.pk}
        response = self.client.delete(
            delete_url, data=data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org_pk, self.lab.pk, self.user)
        )
        new_total_shelfobject = ShelfObject.objects.all().count()

        so_exists = ShelfObject.objects.filter(pk=shelfobject.pk).exists()
        self.assertFalse(so_exists)
        self.assertEqual(old_total_shelfobject - 1, new_total_shelfobject)

    def test_delete_equipment_obj(self):
        """
        Function test api shelf object delete

        - Check response status code 200
        - Check if user has permission to access this organization and laboratory.
        - Check if a specific shelf object inside a laboratory was deleted.
        """
        old_total_shelfobject = ShelfObject.objects.all().count()
        shelfobject = ShelfObject.objects.get(pk=13)
        delete_url = reverse(
            "laboratory:api-shelfobject-delete",
            kwargs={"org_pk": self.org_pk, "lab_pk": self.lab.id},
        )
        data = {"shelfobj": shelfobject.pk}
        response = self.client.delete(
            delete_url, data=data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org_pk, self.lab.pk, self.user)
        )
        new_total_shelfobject = ShelfObject.objects.all().count()

        so_exists = ShelfObject.objects.filter(pk=shelfobject.pk).exists()
        self.assertFalse(so_exists)
        self.assertEqual(old_total_shelfobject - 1, new_total_shelfobject)
