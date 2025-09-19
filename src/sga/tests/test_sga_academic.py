import json

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from sga.models import WarningWord, DangerIndication, PrudenceAdvice, Provider


class SGAAcademicTest(TestCase):
    fixtures = ["substances.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.url_attr = {"org_pk": 1}
        self.client.force_login(self.user)

    def test_get_warning_words(self):
        response = self.client.get(reverse("sga:warning_words", kwargs=self.url_attr))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "sga/substance/warning_words.html")

    def test_add_warning_word(self):
        response_get = self.client.get(
            reverse("sga:add_warning_word", kwargs=self.url_attr)
        )
        self.assertEqual(response_get.status_code, 200)
        self.assertEqual(
            response_get.context["url"],
            reverse("sga:add_warning_word", kwargs=self.url_attr),
        )
        self.assertEqual(
            response_get.context["view_url"],
            reverse("sga:warning_words", kwargs=self.url_attr),
        )
        data = {
            "name": "Advertencia",
            "weigth": 28,
        }

        response_pos = self.client.post(
            reverse("sga:add_warning_word", kwargs=self.url_attr),
            data=data,
            follow=True,
        )

        self.assertEqual(response_pos.status_code, 200)
        self.assertTrue("Advertencia" == WarningWord.objects.latest("pk").name)
        self.assertRedirects(
            response_pos, reverse("sga:warning_words", kwargs=self.url_attr)
        )

    def test_add_warning_word_fail(self):
        response_get = self.client.get(
            reverse("sga:add_warning_word", kwargs=self.url_attr)
        )
        self.assertEqual(response_get.status_code, 200)
        self.assertEqual(
            response_get.context["url"],
            reverse("sga:add_warning_word", kwargs=self.url_attr),
        )
        self.assertEqual(
            response_get.context["view_url"],
            reverse("sga:warning_words", kwargs=self.url_attr),
        )
        data = {
            "name": "Advertencia",
            "weigth": 28.9,
        }
        count = WarningWord.objects.all().count()
        response_pos = self.client.post(
            reverse("sga:add_warning_word", kwargs=self.url_attr),
            data=data,
            follow=True,
        )

        self.assertEqual(response_pos.status_code, 200)
        self.assertTrue(count == WarningWord.objects.all().count())

    def test_add_prudence_advice(self):
        response_get = self.client.get(
            reverse("sga:add_prudence_advice", kwargs=self.url_attr)
        )
        self.assertEqual(response_get.status_code, 200)
        self.assertEqual(
            response_get.context["url"],
            reverse("sga:add_prudence_advice", kwargs=self.url_attr),
        )
        self.assertEqual(
            response_get.context["view_url"],
            reverse("sga:prudence_advices", kwargs=self.url_attr),
        )
        data = {
            "code": "2158",
            "name": "Radioactivo",
            "prudence_advice_help": "zzz",
        }
        response_pos = self.client.post(
            reverse("sga:add_prudence_advice", kwargs=self.url_attr),
            data=data,
            follow=True,
        )
        self.assertEqual(response_pos.status_code, 200)
        self.assertTrue("2158", PrudenceAdvice.objects.latest("pk").code)
        self.assertRedirects(
            response_pos, reverse("sga:prudence_advices", kwargs=self.url_attr)
        )

    def test_get_update_warning_word(self):
        url = self.url_attr.copy()
        url["pk"] = 2
        response_get = self.client.get(reverse("sga:update_warning_word", kwargs=url))
        self.assertEqual(response_get.status_code, 200)
        self.assertEqual(
            response_get.context["url"], reverse("sga:update_warning_word", kwargs=url)
        )
        self.assertEqual(
            response_get.context["view_url"],
            reverse("sga:warning_words", kwargs=self.url_attr),
        )

    def test_post_update_warning_word(self):
        url = self.url_attr.copy()
        url["pk"] = 2
        data = {"name": "Advertencia", "weigth": 20}

        response_pos = self.client.post(
            reverse("sga:update_warning_word", kwargs=url), data=data, follow=True
        )

        self.assertEqual(response_pos.status_code, 200)
        self.assertTrue(data["name"] == WarningWord.objects.get(pk=2).name)
        self.assertRedirects(
            response_pos, reverse("sga:warning_words", kwargs=self.url_attr)
        )

    def test_post_update_warning_word_fail(self):
        """The weigth field is required"""

        url = self.url_attr.copy()
        url["pk"] = 2
        data = {
            "name": "Advertencia",
        }

        response_pos = self.client.post(
            reverse("sga:update_warning_word", kwargs=url), data=data, follow=True
        )
        self.assertTrue(data["name"] != WarningWord.objects.get(pk=2).name)

    def test_update_prudence_advice(self):
        url = self.url_attr.copy()
        url["pk"] = PrudenceAdvice.objects.last().pk
        response_get = self.client.get(
            reverse("sga:update_prudence_advice", kwargs=url)
        )
        self.assertEqual(response_get.status_code, 200)
        self.assertEqual(
            response_get.context["url"],
            reverse("sga:update_prudence_advice", kwargs=url),
        )
        self.assertEqual(
            response_get.context["view_url"],
            reverse("sga:prudence_advices", kwargs=self.url_attr),
        )

        data = {"code": "2158", "name": "Caliente"}

        response_pos = self.client.post(
            reverse("sga:add_prudence_advice", kwargs=self.url_attr),
            data=data,
            follow=True,
        )
        self.assertEqual(response_pos.status_code, 200)
        self.assertTrue("2158" == PrudenceAdvice.objects.last().code)
        self.assertRedirects(
            response_pos, reverse("sga:prudence_advices", kwargs=self.url_attr)
        )

    def test_update_prudence_advice_fail(self):
        """The name and code fields are required"""

        url = self.url_attr.copy()
        url["pk"] = PrudenceAdvice.objects.last().pk
        response_get = self.client.get(
            reverse("sga:update_prudence_advice", kwargs=url)
        )
        self.assertEqual(response_get.status_code, 200)
        self.assertEqual(
            response_get.context["url"],
            reverse("sga:update_prudence_advice", kwargs=url),
        )
        self.assertEqual(
            response_get.context["view_url"],
            reverse("sga:prudence_advices", kwargs=self.url_attr),
        )

        data = {
            "code": "2158",
        }

        response_pos = self.client.post(
            reverse("sga:add_prudence_advice", kwargs=self.url_attr),
            data=data,
            follow=True,
        )
        self.assertFormError(response_pos, "form", "name", "This field is required.")
        self.assertFormError(response_pos, "form", "name", "This field is required.")

        self.assertTrue("2158" != PrudenceAdvice.objects.last().code)

    def test_update_danger_indications(self):
        """The code field can't change because is the pk and the view convert to add"""

        url = self.url_attr.copy()
        url["pk"] = DangerIndication.objects.last().pk
        response_get = self.client.get(
            reverse("sga:update_danger_indication", kwargs=url)
        )
        self.assertEqual(response_get.status_code, 200)
        self.assertEqual(
            response_get.context["url"],
            reverse("sga:update_danger_indication", kwargs=url),
        )
        self.assertEqual(
            response_get.context["view_url"],
            reverse("sga:danger_indications", kwargs=self.url_attr),
        )
        data = {
            "code": url["pk"],
            "description": "No tocar agua",
            "warning_words": 2,
            "warning_class": [2],
            "warning_category": [64],
            "prudence_advice": [2, 3],
        }
        response_pos = self.client.post(
            reverse("sga:update_danger_indication", kwargs=url), data, follow=True
        )
        self.assertEqual(response_pos.status_code, 200)
        self.assertTrue(
            data["description"] == DangerIndication.objects.last().description
        )
        self.assertRedirects(
            response_pos, reverse("sga:danger_indications", kwargs=self.url_attr)
        )

    def test_add_provider(self):
        url = self.url_attr.copy()
        data = {
            "name": "Fanal",
            "country": "CR",
            "direction": "San jose",
            "telephone_number": "2222-2222",
            "fax": "25616",
            "email": "FCR@gmail.com",
            "emergency_phone": "2222-2222",
        }
        response_pos = self.client.post(
            reverse("sga:add_sga_provider", kwargs=url), data, follow=True
        )
        self.assertEqual(response_pos.status_code, 200)
        self.assertTrue(json.loads(response_pos.content)["result"] is True)
        self.assertTrue(Provider.objects.count() is True)
