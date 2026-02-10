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
        self.url_attr = {"org_pk": 1, "risk":5}
        self.client.force_login(self.user)

    def test_get_incident(self):

        response = self.client.get(
            reverse("riskmanagement:api-incident-list", kwargs=self.url_attr)
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content).get("recordsTotal") == 3)

    def test_get_q_incident(self):
        response = self.client.get(
            reverse("riskmanagement:api-incident-list", kwargs=self.url_attr) + "?q=Algo"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content).get("recordsTotal") == 3)

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
            reverse("riskmanagement:api-incident-list", kwargs=self.url_attr),
            data=data, content_type="application/json"
        )
        incident = IncidentReport.objects.last()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(data["causes"] == incident.causes)

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

        response = self.client.put(
            reverse("riskmanagement:api-incident-detail", kwargs=self.url_attr), data=data,
            content_type="application/json"
        )

        incident = IncidentReport.objects.all()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(incident.count() == count)
        self.assertTrue(data["causes"] == incident.last().causes)

    def test_detail_incident_fail(self):
        self.url_attr["pk"] = 7
        response = self.client.get(
            reverse("riskmanagement:api-incident-detail", kwargs=self.url_attr)
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_incident_report(self):
        self.url_attr["pk"] = 4
        pre_incident = IncidentReport.objects.count()
        response = self.client.delete(
            reverse("riskmanagement:api-incident-detail", kwargs=self.url_attr)
        )

        incidents = IncidentReport.objects.count()
        self.assertEqual(response.status_code, 204)
        self.assertTrue(pre_incident > incidents)


    def test_report_incident(self):
        self.url_attr["pk"] = 4
        del self.url_attr["risk"]
        self.url_attr.update({"risk_pk": 5})

        response = self.client.get(
            reverse("riskmanagement:incident_report", kwargs=self.url_attr)
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header("content-type"))
        self.assertEqual(response["content-type"], "application/pdf")
        self.assertTrue(response.has_header("content-disposition"))

    def test_report_incident_xlsx(self):
        self.url_attr["pk"] = 4
        del self.url_attr["risk"]
        self.url_attr.update({"risk_pk": 5})
        response = self.client.get(
            reverse("riskmanagement:incident_report", kwargs=self.url_attr) + ""
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header("content-type"))
        self.assertEqual(response["content-type"], "application/pdf")
        self.assertTrue(response.has_header("content-disposition"))
