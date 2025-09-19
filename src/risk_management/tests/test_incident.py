import datetime

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
import json

from risk_management.models import IncidentReport


class IncidentReportTest(TestCase):
    fixtures = ["object.json", "riskmanagement_data.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.url_attr = {"org_pk": 1, "lab_pk": 1}
        self.client.force_login(self.user)

    def test_get_incident(self):

        response = self.client.get(
            reverse("riskmanagement:incident_list", kwargs=self.url_attr)
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context["object_list"]) == 3)

    def test_get_q_incident(self):
        response = self.client.get(
            reverse("riskmanagement:incident_list", kwargs=self.url_attr) + "?q=Algo"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context["object_list"]) == 1)

    def test_add_incident(self):
        data = {
            "short_description": "Incendió",
            "causes": "Alguien fumando",
            "incident_date": datetime.date.today(),
            "infraestructure_impact": "Bodega",
            "people_impact": "Ninguno",
            "laboratories": [1],
            "environment_impact": "Contaminacion Aerea",
            "result_of_plans": "Nada",
            "mitigation_actions": "Cinternas de agua",
            "recomendations": "No fumar cerca de las instalaciones",
        }
        response = self.client.post(
            reverse("riskmanagement:incident_create", kwargs=self.url_attr), data=data
        )
        incident = IncidentReport.objects.last()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(data["causes"] == incident.causes)
        del self.url_attr["lab_pk"]
        self.assertRedirects(
            response, reverse("riskmanagement:riskzone_list", kwargs=self.url_attr)
        )

    def test_update_incident(self):
        self.url_attr["pk"] = IncidentReport.objects.last().pk

        data = {
            "short_description": "Incendió",
            "causes": "Alguien fumando",
            "incident_date": datetime.date.today(),
            "infraestructure_impact": "Bodega",
            "people_impact": "Ninguno",
            "laboratories": [1],
            "environment_impact": "Contaminacion Aerea",
            "result_of_plans": "Nada",
            "mitigation_actions": "Cinternas de agua",
            "recomendations": "No fumar cerca de las instalaciones",
        }
        count = IncidentReport.objects.count()

        response = self.client.post(
            reverse("riskmanagement:incident_update", kwargs=self.url_attr), data=data
        )

        incident = IncidentReport.objects.all()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(incident.count() == count)
        self.assertTrue(data["causes"] == incident.last().causes)
        del self.url_attr["lab_pk"]
        del self.url_attr["pk"]
        self.assertRedirects(
            response, reverse("riskmanagement:riskzone_list", kwargs=self.url_attr)
        )

    def test_detail_incident_report(self):
        incident = IncidentReport.objects.last()
        self.url_attr["pk"] = incident.pk

        response = self.client.get(
            reverse("riskmanagement:incident_detail", kwargs=self.url_attr)
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            incident.short_description == response.context["object"].short_description
        )

    def test_detail_incident_fail(self):
        self.url_attr["pk"] = 7
        response = self.client.get(
            reverse("riskmanagement:incident_detail", kwargs=self.url_attr)
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_incident_report(self):
        self.url_attr["pk"] = 4
        pre_incident = IncidentReport.objects.count()

        response = self.client.post(
            reverse("riskmanagement:incident_delete", kwargs=self.url_attr)
        )

        incidents = IncidentReport.objects.count()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(pre_incident > incidents)
        self.assertRedirects(
            response, reverse("riskmanagement:riskzone_list", kwargs={"org_pk": 1})
        )

    def test_report_incident(self):
        self.url_attr["pk"] = 4

        response = self.client.get(
            reverse("riskmanagement:incident_report", kwargs=self.url_attr)
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header("content-type"))
        self.assertEqual(response["content-type"], "application/pdf")
        self.assertTrue(response.has_header("content-disposition"))

    def test_report_incident_xlsx(self):
        self.url_attr["pk"] = 4
        response = self.client.get(
            reverse("riskmanagement:incident_report", kwargs=self.url_attr) + ""
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header("content-type"))
        self.assertEqual(response["content-type"], "application/pdf")
        self.assertTrue(response.has_header("content-disposition"))
