from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from academic.models import Procedure
from laboratory.models import OrganizationStructure, Laboratory
import json
from rest_framework.test import APIClient

class ProceduresAPITest(TestCase):
    fixtures = ["object.json","procedure.json"]

    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()
        self.user = User.objects.get(pk=1)
        self.url_attr= {'org_pk': 1}

    def test_get_procedures(self):
        self.client.force_login(self.user)
        url = reverse("academic:api-procedure-list",kwargs=self.url_attr)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,text="recordsTotal")
        self.assertTrue(json.loads(response.content)["recordsTotal"]==0)

    def test_get_procedures_no_login(self):
        self.client.logout()
        url = reverse("academic:api-procedure-list",kwargs=self.url_attr)
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_get_procedures_no_organization(self):
        self.client.force_login(self.user)
        url = reverse("academic:api-procedure-list",kwargs={'org_pk':10000})
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, 403)


