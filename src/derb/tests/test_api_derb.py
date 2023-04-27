import datetime

from django.contrib.contenttypes.models import ContentType

from laboratory.admin import create_informs
from laboratory.models import Object, Inform, Laboratory, OrganizationStructure, UserOrganization, ObjectFeatures
from laboratory.views.informs import create_informs
from risk_management.models import IncidentReport
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class DerbAPITest(TestCase):
    fixtures = ["derb.json", "laboratory_data.json"]
    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.url_attr= {'org_pk': 1}
        self.lab = Laboratory.objects.first()
        self.client.force_login(self.user)

    def create_object_features(self):
        return ObjectFeatures.objects.create(name="Test Feature", description="Test Feature Desc")

    def create_object(self):
        features = self.create_object_features()
        org = OrganizationStructure.objects.get(pk=1)
        object = Object.objects.create(code="1234", name="Test Object", organization=org)
        features.object_set.add(object)

    def create_inform(self):
        data = {
            "name": "Uso de instrumentos de laboratorio",
            "custom_form": 1
        }
        url = reverse("laboratory:add_informs", kwargs={"org_pk": 1, "lab_pk": self.lab.pk,
                                                        "content_type": "laboratory", "model": "laboratory"})
        self.client.post(url, data=data)

    def create_incident_report(self):
        data = {
            'short_description': 'Incendió',
            'causes': 'Alguien fumando',
            "incident_date": datetime.date.today(),
            'infraestructure_impact': "Bodega",
            'people_impact': "Ninguno",
            'laboratories': [1],
            'environment_impact': "Contaminacion Aerea",
            'result_of_plans': "Nada",
            'mitigation_actions': "Cinternas de agua",
            'recomendations': "No fumar cerca de las instalaciones",
        }
        self.client.post(reverse('riskmanagement:incident_create', kwargs={"org_pk": 1, "lab_pk": self.lab.pk}), data=data)
    def test_lab_api_by_user(self):
        response = self.client.get(reverse('derb:api_laboratory_by_user', kwargs=self.url_attr))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response=response, text="Vick Lab")
        self.assertContains(response=response, text="Lab Ultra")
        self.assertContains(response=response, text="DS Cosme")

    def test_lab_api_by_org(self):
        response = self.client.get(reverse('derb:api_laboratory_by_org', kwargs=self.url_attr))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response=response, text="Vick Lab")
        self.assertContains(response=response, text="Lab Ultra")
        self.assertContains(response=response, text="DS Cosme")

    def test_inform_api(self):
        self.create_inform()
        response = self.client.get(reverse('derb:api_inform', kwargs=self.url_attr))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response=response, text="Uso de instrumentos de laboratorio")

    def test_incident_report_api(self):
        self.create_incident_report()
        response = self.client.get(reverse('derb:api_incident', kwargs=self.url_attr))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response=response, text="Incendió")

    def test_users_by_org_api(self):
        response = self.client.get(reverse('derb:api_org_structure', kwargs=self.url_attr))
        self.assertEqual(response.status_code, 200)

    def test_objects_api(self):
        self.create_object()
        response = self.client.get(reverse('derb:api_objects', kwargs=self.url_attr))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response=response, text="Test Object")
