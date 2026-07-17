from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
import json


class MsdsTest(TestCase):
    fixtures = ["msds_data.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        permission = Permission.objects.get(codename="institution_can_access")
        self.user.user_permissions.add(permission)
        for codename in ["view_msdsobject", "add_msdsobject"]:
            perm = Permission.objects.get(codename=codename)
            self.user.user_permissions.add(perm)
        self.url_attr = {"org_pk": 1}
        self.client.force_login(self.user)

    def test_get_msds(self):
        response = self.client.get(reverse("msds:list_msds", kwargs=self.url_attr))
        self.assertEqual(response.status_code, 200)

    def test_index_msds(self):
        response = self.client.get(reverse("msds:index_msds", kwargs=self.url_attr))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name="index_msds.html")

    def test_sds_create_get(self):
        response = self.client.get(reverse("msds:sds_create", kwargs=self.url_attr))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name="msds/sds_create.html")

    def test_get_regulations(self):
        response = self.client.get(reverse("regulation_docs"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["object_list"].count() == 15)
