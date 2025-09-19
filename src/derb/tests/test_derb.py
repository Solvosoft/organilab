import datetime

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
import json

from derb.models import *


class DerbTest(TestCase):
    fixtures = ["derb.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.url_attr = {"org_pk": 1}
        self.client.force_login(self.user)

    def test_formlist(self):
        response = self.client.get(reverse("derb:form_list", kwargs=self.url_attr))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["forms"].count() == 2)

    def test_delete_form(self):
        self.url_attr["pk"] = 1
        pre = CustomForm.objects.count()
        response = self.client.post(reverse("derb:delete_form", kwargs=self.url_attr))
        pos = CustomForm.objects.count()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(pre > pos)
        del self.url_attr["pk"]
        self.assertRedirects(response, reverse("derb:form_list", kwargs=self.url_attr))

    def test_create_form(self):
        pre = CustomForm.objects.count()
        data = {
            "organization": 1,
            "creation_date": "2023-01-26T15:44:10.602Z",
            "last_update": "2023-01-26T15:44:10.739Z",
            "created_by": self.user,
            "name": "ZZZ",
            "status": "admin",
            "schema": {"name": "Prueba Congreso", "status": "admin", "components": []},
        }
        response = self.client.post(
            reverse("derb:create_form", kwargs=self.url_attr), data=data
        )
        pos = CustomForm.objects.count()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(pre < pos)
        self.assertTrue(data["name"] == CustomForm.objects.last().name)
        self.assertTrue(
            json.loads(response.content)["url"]
            == reverse("derb:edit_view", args=[1, CustomForm.objects.last().pk])
        )
