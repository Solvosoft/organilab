from django.core.files.base import ContentFile
from django.test import TestCase
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
import json

from msds.models import *
import io


class MsdsTest(TestCase):
    fixtures = ["msds_data.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.url_attr = {"org_pk": 1}
        self.client.force_login(self.user)

    def test_get_msds(self):

        response = self.client.get(reverse("msds:list_msds", kwargs=self.url_attr))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)["recordsTotal"] > 2000)
        self.assertTrue(json.loads(response.content)["recordsFiltered"] == 4)

    def test_add_msds(self):
        f = ContentFile(b"Hello world!", name="hello-world.pdf")

        data = {
            "provider": "Fanal",
            "file": f,
            "product": "Gel",
        }
        pre_count = MSDSObject.objects.count()

        response = self.client.post(
            reverse("msds:msds_msdsobject_create", kwargs=self.url_attr), data=data
        )
        pos_count = MSDSObject.objects.count()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(pos_count > pre_count)
        self.assertIn(data["product"], MSDSObject.objects.last().product)
        self.assertRedirects(response, reverse("msds:index_msds", kwargs={"org_pk": 1}))

    def test_update_msds(self):
        self.url_attr["pk"] = 449

        f = ContentFile(b"Hello world!", name="hello-world.pdf")

        data = {
            "provider": "Fanal",
            "file": f,
            "product": "Gel",
            "provider": "AVENTIS CROPSCIENCE ESPAÑA, S.A.",
        }
        pre_count = MSDSObject.objects.count()

        response = self.client.post(
            reverse("msds:msds_msdsobject_update", kwargs=self.url_attr), data=data
        )
        pos_count = MSDSObject.objects.count()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(pos_count == pre_count)
        self.assertIn(data["product"], MSDSObject.objects.get(pk=449).product)
        self.assertRedirects(response, reverse("msds:index_msds", kwargs={"org_pk": 1}))

    def test_delete_msds(self):
        self.url_attr["pk"] = 449

        pre_count = MSDSObject.objects.count()

        response = self.client.post(
            reverse("msds:msds_msdsobject_delete", kwargs=self.url_attr)
        )
        pos_count = MSDSObject.objects.count()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(pos_count < pre_count)
        self.assertIsNone(MSDSObject.objects.filter(pk=449).first())
        self.assertRedirects(response, reverse("msds:index_msds", kwargs={"org_pk": 1}))

    def test_detail_msds(self):
        self.url_attr["pk"] = 449

        response = self.client.get(
            reverse("msds:msds_msdsobject_detail", kwargs=self.url_attr)
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["object"])
        self.assertTrue(response.context["object"].product == "FURADAN 5G")

    def test_index_msds(self):

        response = self.client.get(reverse("msds:index_msds", kwargs=self.url_attr))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name="index_msds.html")

    def test_get_regulations(self):

        response = self.client.get(reverse("regulation_docs"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["object_list"].count() == 15)

    """
    In development don't have the regulation files in media only try test in production
    def test_download_regulations(self):

        response = self.client.get(reverse('download_all_regulations'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header('content-type'))
        self.assertEqual(response['content-type'], 'application/force-download')
        self.assertTrue(response.has_header('content-disposition'))
        self.assertContains(response['content-disposition'],'attachment; filename="regulations.zip"')"""
