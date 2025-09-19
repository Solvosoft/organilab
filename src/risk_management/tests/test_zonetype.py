from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
import json

from risk_management.models import *


class RiskZoneTest(TestCase):
    fixtures = ["object.json", "riskmanagement_data.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.url_attr = {"org_pk": 1}
        self.client.force_login(self.user)

    def test_get_risk_zone(self):

        response = self.client.get(
            reverse("riskmanagement:riskzone_list", kwargs=self.url_attr)
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context["object_list"]) == 2)

    def test_add_risk_zone(self):
        data = {
            "name": "First Risk Zone",
            "laboratories": [1],
            "num_workers": 7,
            "zone_type": 2,
        }

        response = self.client.post(
            reverse("riskmanagement:riskzone_create", kwargs=self.url_attr), data=data
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(data["name"], RiskZone.objects.values_list("name", flat=True))
        self.assertRedirects(
            response, reverse("riskmanagement:riskzone_list", kwargs={"org_pk": 1})
        )

    def test_update_risk_zone(self):
        self.url_attr["pk"] = 6
        data = {
            "name": "First Risk",
            "laboratories": [1],
            "num_workers": 7,
            "zone_type": 2,
        }
        count = RiskZone.objects.count()
        response = self.client.post(
            reverse("riskmanagement:riskzone_update", kwargs=self.url_attr), data=data
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(data["name"], RiskZone.objects.values_list("name", flat=True))
        self.assertTrue(RiskZone.objects.count() == count)
        self.assertRedirects(
            response, reverse("riskmanagement:riskzone_list", kwargs={"org_pk": 1})
        )

    def test_delete_risk_zone(self):
        self.url_attr["pk"] = 6

        count = RiskZone.objects.count()
        response = self.client.post(
            reverse("riskmanagement:riskzone_delete", kwargs=self.url_attr)
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(RiskZone.objects.count() < count)
        self.assertRedirects(
            response, reverse("riskmanagement:riskzone_list", kwargs={"org_pk": 1})
        )

    def test_detail_risk_zone(self):
        self.url_attr["pk"] = 6

        risk = RiskZone.objects.get(pk=6)
        response = self.client.get(
            reverse("riskmanagement:riskzone_detail", kwargs=self.url_attr)
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(risk.name == response.context["object"].name)

    def test_detail_risk_zone_fail(self):
        self.url_attr["pk"] = 7

        response = self.client.get(
            reverse("riskmanagement:riskzone_detail", kwargs=self.url_attr)
        )

        self.assertEqual(response.status_code, 404)

    def test_add_zone_type(self):
        data = {"name": "First Risk Zone", "priority_validator": [2]}
        response = self.client.post(
            reverse("riskmanagement:zone_type_add", kwargs=self.url_attr), data=data
        )
        zone = ZoneType.objects.last()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)["ok"] is True)
        self.assertTrue(json.loads(response.content)["id"] == zone.pk)
