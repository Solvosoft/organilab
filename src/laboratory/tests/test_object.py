from django.contrib.auth import get_user_model
from django.db.models import Q
from django.urls import reverse
from django.test import Client

from laboratory.models import ObjectFeatures, Object, Provider
from laboratory.tests.utils import BaseLaboratorySetUpTest
from laboratory.utils import get_pk_org_ancestors_decendants
import json


class ObjectViewTest(BaseLaboratorySetUpTest):

    def test_get_substance_list(self):
        url = reverse("laboratory:sustance_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_substance(self):
        url = reverse("laboratory:sustance_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 2})
        response = self.client.post(url)
        success_url = reverse("laboratory:sustance_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, success_url)

    def test_sustance_add(self):
        url = reverse("laboratory:sustance_add", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_sustance_manage(self):
        url = reverse("laboratory:sustance_manage", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_sustance_list_json(self):
        url = reverse("laboratory:sustance_list_json", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_objectview_list(self):
        url = reverse("laboratory:objectview_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        data = {
            "type_id": '0'
        }
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tanque 1000 mL")

    def test_objectview_update(self):
        object = Object.objects.get(name="RA 100 gr")
        url = reverse("laboratory:objectview_update", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": object.pk})
        data = {
            "name": "RA Paquete 100 gr",
            "features": [1],
            "code": "RA43",
            "synonym": "RA",
            "is_public": True,
            "model": "RA2022",
            "serie": "Reactive 008",
            "plaque": "RA4300",
            "type": "0"
        }
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_objectview_delete(self):
        object = Object.objects.last()
        url = reverse("laboratory:objectview_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": object.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(object.pk, Object.objects.values_list('pk'))
        success_url = reverse("laboratory:objectview_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response, success_url)

    def test_objectview_create(self):
        total_obj = Object.objects.all().count()
        url = reverse("laboratory:objectview_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        data = {
            "name": "Ácido Clorhídrico",
            "features": [1],
            "code": "AC",
            "synonym": "Ácido",
            "is_public": True,
            "model": "AC2022",
            "serie": "Ácido 222",
            "plaque": "AC4300",
            "type": "1",
            "is_container": True,
            "capacity":200,
            "capacity_measurement_unit":64,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Object.objects.last().materialcapacity.capacity==200)
        self.assertEqual(total_obj+1, Object.objects.all().count())
        success_url = reverse("laboratory:objectview_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})+"?type_id=1"
        self.assertRedirects(response, success_url)

    def test_objects_list_report(self):
        data = {
            "type_id": "1"
        }
        url = reverse("laboratory:reports_objects_list", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)

    def test_precursor_report(self):
        data = {
            "consecutive": 1,
            "month": 2,
            "year": 2018
        }
        url = reverse("laboratory:precursor_report", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)

class SustanceCharacteristicsViewTest(BaseLaboratorySetUpTest):

    def test_organizationreactivepresence(self):
        url = reverse("laboratory:organizationreactivepresence", kwargs={"org_pk": self.org.pk, })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_download_h_code_reports(self):
        url = reverse("laboratory:download_h_code_reports", kwargs={"org_pk": self.org.pk, })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_h_code_reports(self):
        url = reverse("laboratory:h_code_reports", kwargs={"org_pk": self.org.pk, })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

class ObjectFeaturesViewTest(BaseLaboratorySetUpTest):

    def test_update_objectfeature(self):
        objfeature = ObjectFeatures.objects.first()
        url = reverse("laboratory:object_feature_update", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": objfeature.pk})

        response_get = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Es un reactivo en la industria química")

        data = {
            "name": "Reactivo 1",
            "description": "Es un reactivo en la industria química empacado en saco de 50kg o bolsas de 2kg."
        }
        response_post = self.client.post(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        success_url = reverse("laboratory:object_feature_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response_post.status_code, 302)
        self.assertRedirects(response_post, success_url)
        self.assertIn("Reactivo 1", list(ObjectFeatures.objects.values_list("name", flat=True)))

    def test_create_objectfeature(self):
        data = {
            "name": "Guantes",
            "description": "Brinda protección en manos y brazos a la hora de manipular cualquier material que lo requiera.",
        }
        url = reverse("laboratory:object_feature_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.post(url, data=data)
        success_url = reverse("laboratory:object_feature_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, success_url)
        self.assertIn("Guantes", list(ObjectFeatures.objects.values_list("name", flat=True)))

    def test_delete_objectfeature(self):
        objfeature = ObjectFeatures.objects.first()
        url = reverse("laboratory:object_feature_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": objfeature.pk})
        response = self.client.post(url)
        success_url = reverse("laboratory:object_feature_create", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, success_url)


class EquipmentViewTest(BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        self.kwargs = {"org_pk": self.org.pk, "lab_pk": self.lab.pk}

        self.kwargs_update = self.kwargs.copy()
        self.kwargs_destroy1 = self.kwargs.copy()
        self.kwargs_destroy2 = self.kwargs.copy()
        self.kwargs_destroy3 = self.kwargs.copy()

        self.kwargs_update.update({"pk": 8})
        self.kwargs_destroy1.update({"pk": 9})
        self.kwargs_destroy2.update({"pk": 10})
        self.kwargs_destroy3.update({"pk": 11})

        detail_url = "laboratory:api-equipment-detail"

        self.url_equipment_view = reverse("laboratory:equipment_list", kwargs=self.kwargs)
        self.url_equipment_list = reverse("laboratory:api-equipment-list", kwargs=self.kwargs)

        self.url_equipment_update = reverse(detail_url, kwargs=self.kwargs_update)
        self.url_equipment_destroy1 = reverse(detail_url, kwargs=self.kwargs_destroy1)
        self.url_equipment_destroy2 = reverse(detail_url, kwargs=self.kwargs_destroy2)
        self.url_equipment_destroy3 = reverse(detail_url, kwargs=self.kwargs_destroy3)

        self.user_without_perms = get_user_model().objects.filter(username="tuwp").first()
        self.client2 = Client()
        self.client2.force_login(self.user_without_perms)

        data_base = {
            "type": "2",
            "is_public": True,
            "features": [1],
            "providers": [1],
            "use_manual": None,
            "calibration_required": False,
            "operation_voltage": "",
            "operation_amperage": "",
            "generate_pathological_waste": False,
            "clean_period_according_to_provider": 3,
            "instrumental_family": None,
            "equipment_type": 2,
            "created_by": self.user.pk,
            "organization": self.org.pk,
            "laboratory": self.lab.pk,
        }

        self.create_data = data_base.copy()
        self.create_data.update({
            "code": "25rfe6",
            "name": "Mechero",
            "synonym": "Encendedor",
            "description": "Entrada de calor controlada a base de gas.",
            "model": "MK23213",
            "serie": "3232432",
            "plaque": "P32r32",
            "use_specials_conditions": "El uso adecuado de este equipo requiere que "
                                       "las las condiciones donde vaya a ser "
                                       "utilizado sean óptimas."
        })

        self.update_data1 = data_base.copy()
        self.update_data1.update({
            "code": "BZ",
            "name": "Balanza",
            "synonym": "Pesa",
            "description": "Instrumento para el cálculo de la masa de un objeto.",
            "model": "F79L543",
            "serie": "kd23213",
            "plaque": "BFDS3E",
            "use_specials_conditions": "Evitar golpes al equipo y exposión prolongada a "
                                       "condiciones calurosas y húmedas."
        })

        self.update_data2 = data_base.copy()
        self.update_data2.update({
            "code": "HN",
            "name": "Horno",
            "synonym": "Fuego,Horneado",
            "description": "Aparato que permite calentar materiales a temperaturas elevadas, normalmente superiores a 300°C.",
            "model": "PDLSF",
            "serie": "FS553",
            "plaque": "34FERDSA",
            "organization": 3
        })

        self.queryset = Object.objects.filter(type=Object.EQUIPMENT)

        filters = (Q(organization__in=get_pk_org_ancestors_decendants(self.user,
                                                                      self.org.pk),
                     is_public=True)
                   | Q(organization__pk=self.org.pk, is_public=False))

        self.queryset = self.queryset.filter(filters).distinct()

    def test_access_to_equipment_view_user_with_perms(self):
        # User 1 with perms - Check response status code equal to 200.
        response = self.client.get(self.url_equipment_view)
        self.assertEqual(response.status_code, 200)

    def test_access_to_equipment_view_user_without_perms(self):
        # User 3 without perms - Check response status code equal to 302. --> Permission required(view_object)
        response = self.client2.get(self.url_equipment_view)
        self.assertEqual(response.status_code, 302)

    def test_view_equipment_list_user_with_perms(self):
        # User 1 with perms - Check response status code equal to 200.
        response = self.client.get(self.url_equipment_list, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)['data'])

    def test_view_equipment_list_user_without_perms(self):
        # User 3 without perms - Check response status code equal to 403. --> Permission required(view_object)
        response = self.client2.get(self.url_equipment_list, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_create_equipment_user_with_perms(self):
        # User 1 with perms - Check response status code equal to 201. --> Complete and valid data
        response = self.client.post(self.url_equipment_list, data=self.create_data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(self.queryset.filter(name=self.create_data["name"]).exists())

    def test_create_equipment_without_features_user_with_perms(self):
        # User 1 with perms - Check response status code equal to 400. --> Incomplete data
        data = self.create_data.copy()
        del data['features']
        response = self.client.post(self.url_equipment_list, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_create_equipment_with_different_type_user_with_perms(self):
        # User 1 with perms - Check response status code equal to 400. --> Invalid data
        data = self.create_data.copy()
        data['type'] = Object.MATERIAL
        response = self.client.post(self.url_equipment_list, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_create_equipment_with_different_org_user_with_perms(self):
        # User 1 with perms - Check response status code equal to 400. --> Invalid data
        data = self.create_data.copy()
        data['organization'] = 2
        response = self.client.post(self.url_equipment_list, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_create_equipment_user_without_perms(self):
        # User 3 without perms - Check response status code equal to 403. --> Permissions required(view_object, add_object)
        response = self.client2.post(self.url_equipment_list, data=self.create_data, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_update_equipment_user_with_perms(self):
        # User 1 with perms - Check response status code equal to 200.
        response = self.client.put(self.url_equipment_update, data=self.update_data1, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_update_equipment_without_features_user_with_perms(self):
        # User 1 with perms - Check response status code equal to 400. --> Invalid data
        data = self.update_data1
        data["features"] = []
        response = self.client.put(self.url_equipment_update, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_update_equipment_with_different_type_user_with_perms(self):
        # User 1 with perms - Check response status code equal to 400. --> Invalid data
        data = self.update_data1.copy()
        data["type"] = Object.REACTIVE
        response = self.client.put(self.url_equipment_update, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_update_equipment_with_different_org_user_with_perms(self):
        # User 1 with perms - Check response status code equal to 400. --> Invalid data
        data = self.update_data1.copy()
        data["organization"] = 2
        response = self.client.put(self.url_equipment_update, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_update_equipment_with_different_object_org_user_with_perms(self):
        # User 1 with perms - Check response status code equal to 400. --> Different organization equipment object
        response = self.client.put(self.url_equipment_update, data=self.update_data2, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_update_equipment_user_without_perms(self):
        # User 3 without perms - Check response status code equal to 403. --> Permissions required(view_object, change_object)
        response = self.client2.put(self.url_equipment_update, data=self.update_data1, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_delete_equipment_user_with_perms(self):
        # User 1 with perms - Check response status code equal to 204.
        response = self.client.delete(self.url_equipment_destroy1, content_type='application/json')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(self.queryset.filter(pk=self.kwargs_destroy1["pk"]).exists())

    def test_delete_equipment_with_different_object_org_user_with_perms(self):
        # User 1 with perms - Check response status code equal to 204. --> Different organization equipment object
        response = self.client.delete(self.url_equipment_destroy3, content_type='application/json')
        self.assertEqual(response.status_code, 404)
        self.assertTrue(self.queryset.filter(pk=self.kwargs_destroy1["pk"]).exists())

    def test_delete_equipment_user_without_perms(self):
        # User 3 without perms - Check response status code equal to 403. --> Permissions required(view_object, delete_object)
        response = self.client2.delete(self.url_equipment_destroy2, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.queryset.filter(pk=self.kwargs_destroy2["pk"]).exists())
