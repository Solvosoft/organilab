import json

from django.test import TestCase, Client
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from laboratory.models import OrganizationStructure
from django.urls import reverse

from sga.models import WarningWord, DangerIndication, PrudenceAdvice


class WarningWordAPITests(TestCase):
    fixtures = ["sga_components_data.json"]

    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()
        self.first_user = User.objects.get(pk=1)
        self.second_user = User.objects.get(pk=2)
        self.organization = OrganizationStructure.objects.get(pk=1)

    def test_warning_word_api_forbidden_for_non_organization_member_users(self):
        self.client.force_login(self.second_user)
        url = reverse("laboratory:api-warning-word-list",
                      kwargs={"org_pk": self.organization.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_warnings_table_api_forbidden_for_non_organization_member_users(self):
        self.client.force_login(self.second_user)
        url = reverse("laboratory:api-warnings-table-list",
                      kwargs={"org_pk": self.organization.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_warning_word_query_if_not_logged_in(self):
        response = self.api_client.get(reverse('laboratory:api-warnings-table-list',
                                               kwargs={"org_pk": self.organization.pk})
                                       + "?format=datatables")
        result = response.json()
        expected = NotFound.default_detail
        self.assertFalse('recordsTotal' in result)
        self.assertEqual(result['detail'], expected)

    def test_warning_words_api_list(self):
        self.client.force_login(self.first_user)
        search_script = '?offset=0&limit=10&draw=7&ordering=created_by' \
                        '&my_procedure=1&_=1685373101914'
        url = reverse('laboratory:api-warning-word-list',
                      kwargs={"org_pk": self.organization.pk}) + search_script
        response = self.client.get(url)
        expected = WarningWord.objects.count()
        result = response.json()
        self.assertEqual(result['count'], expected)

    def test_add_warning_word(self):
        data = {
            "name": "New warning word",
            "weigth": 9,
        }
        self.client.force_login(self.first_user)
        url = reverse('laboratory:api-warning-word-list',
                      kwargs={"org_pk": self.organization.pk})
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json.loads(response.content)['detail'],
                         'Item created successfully.')

    def test_get_warning_word(self):
        warning_word = WarningWord.objects.get(pk=15)
        self.client.force_login(self.first_user)
        url = reverse("laboratory:api-warning-word-detail",
                      kwargs={"org_pk": self.organization.pk,
                              "pk": warning_word.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(warning_word.pk, json.loads(response.content)['pk'])

    def test_update_warning_word(self):
        self.client.force_login(self.first_user)
        data = {
            "name": "Changed",
            "weigth": 0
        }
        warning_word = WarningWord.objects.get(pk=18)
        url = reverse('laboratory:api-warning-word-detail',
                      kwargs={"org_pk": self.organization.pk,
                              "pk": warning_word.pk})
        response = self.client.put(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Refresh comment values
        warning_word = WarningWord.objects.get(pk=18)
        self.assertEqual(warning_word.name, 'Changed')

    def test_delete_warning_word(self):
        self.client.force_login(self.first_user)
        total_count = WarningWord.objects.count()
        warning_word = WarningWord.objects.get(pk=17)
        url = reverse("laboratory:api-warning-word-detail",
                      kwargs={"org_pk": self.organization.pk,
                              "pk": warning_word.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(total_count-1, WarningWord.objects.count())

    def test_warning_word_general_filter_input_returns_filtered_records(self):
        self.client.force_login(self.first_user)
        search_script = '?offset=0&limit=10&draw=4&search=Carefully&' \
                        'ordering=name&_=1687883849018'
        url = reverse('laboratory:api-warnings-table-list',
                      kwargs={"org_pk": self.organization.pk}) + search_script
        response = self.client.get(url)
        result = response.json()
        self.assertNotEquals(result['recordsFiltered'], result['recordsTotal'])


class DangerIndicationAPITests(TestCase):
    fixtures = ["sga_components.json"]

    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()
        self.first_user = User.objects.get(pk=1)
        self.second_user = User.objects.get(pk=2)
        self.organization = OrganizationStructure.objects.get(pk=1)

    def test_danger_indication_api_forbidden_for_non_organization_member_users(self):
        self.client.force_login(self.second_user)
        url = reverse("laboratory:api-danger-indication-list",
                      kwargs={"org_pk": self.organization.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dangers_table_api_forbidden_for_non_organization_member_users(self):
        self.client.force_login(self.second_user)
        url = reverse("laboratory:api-dangers-table-list",
                      kwargs={"org_pk": self.organization.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_danger_indication_query_if_not_logged_in(self):
        response = self.api_client.get(reverse('laboratory:api-dangers-table-list',
                                               kwargs={"org_pk": self.organization.pk})
                                       + "?format=datatables")
        result = response.json()
        expected = NotFound.default_detail
        self.assertFalse('recordsTotal' in result)
        self.assertEqual(result['detail'], expected)

    def test_danger_indications_api_list(self):
        self.client.force_login(self.first_user)
        search_script = '?offset=0&limit=10&draw=7&ordering=created_by' \
                        '&my_procedure=1&_=1685373101914'
        url = reverse('laboratory:api-danger-indication-list',
                      kwargs={"org_pk": self.organization.pk}) + search_script
        response = self.client.get(url)
        expected = DangerIndication.objects.count()
        result = response.json()
        self.assertEqual(result['count'], expected)

    def test_add_danger_indication(self):
        data = {
            "code": "H999",
            "description": "Description for a new danger indication",
            "warning_words": 16,
            "warning_class": [
                2
            ],
            "warning_category": [
                2
            ],
            "prudence_advice": [
                1
            ]
        }
        self.client.force_login(self.first_user)
        url = reverse('laboratory:api-danger-indication-list',
                      kwargs={"org_pk": self.organization.pk})
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json.loads(response.content)['detail'],
                         'Item created successfully.')

    def test_get_danger_indication(self):
        danger_indication = DangerIndication.objects.get(pk='H131')
        self.client.force_login(self.first_user)
        url = reverse("laboratory:api-danger-indication-detail",
                      kwargs={"org_pk": self.organization.pk,
                              "pk": danger_indication.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(danger_indication.pk, json.loads(response.content)['pk'])

    def test_delete_danger_indication(self):
        self.client.force_login(self.first_user)
        total_count = DangerIndication.objects.count()
        danger_indication = DangerIndication.objects.get(pk='H131')
        url = reverse("laboratory:api-danger-indication-detail",
                      kwargs={"org_pk": self.organization.pk,
                              "pk": danger_indication.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(total_count-1, DangerIndication.objects.count())

    def test_danger_indication_general_filter_input_returns_filtered_records(self):
        self.client.force_login(self.first_user)
        search_script = '?offset=0&limit=10&draw=4&search=Description&' \
                        'ordering=name&_=1687883849018'
        url = reverse('laboratory:api-dangers-table-list',
                      kwargs={"org_pk": self.organization.pk}) + search_script
        response = self.client.get(url)
        result = response.json()
        self.assertNotEquals(result['recordsFiltered'], result['recordsTotal'])


class PrudenceAdviceAPITests(TestCase):
    fixtures = ["sga_components.json"]

    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()
        self.first_user = User.objects.get(pk=1)
        self.second_user = User.objects.get(pk=2)
        self.organization = OrganizationStructure.objects.get(pk=1)

    def test_prudence_advice_api_forbidden_for_non_organization_member_users(self):
        self.client.force_login(self.second_user)
        url = reverse("laboratory:api-prudence-advice-list",
                      kwargs={"org_pk": self.organization.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_advices_table_api_forbidden_for_non_organization_member_users(self):
        self.client.force_login(self.second_user)
        url = reverse("laboratory:api-advices-table-list",
                      kwargs={"org_pk": self.organization.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_prudence_advice_query_if_not_logged_in(self):
        response = self.api_client.get(reverse('laboratory:api-advices-table-list',
                                               kwargs={"org_pk": self.organization.pk})
                                       + "?format=datatables")
        result = response.json()
        expected = NotFound.default_detail
        self.assertFalse('recordsTotal' in result)
        self.assertEqual(result['detail'], expected)

    def test_prudence_advices_api_list(self):
        self.client.force_login(self.first_user)
        search_script = '?offset=0&limit=10&draw=7&ordering=created_by' \
                        '&my_procedure=1&_=1685373101914'
        url = reverse('laboratory:api-prudence-advice-list',
                      kwargs={"org_pk": self.organization.pk}) + search_script
        response = self.client.get(url)
        expected = PrudenceAdvice.objects.count()
        result = response.json()
        self.assertEqual(result['count'], expected)

    def test_add_prudence_advice(self):
        data = {
            "code": "P777",
            "name": "New advice",
            "prudence_advice_help": "Help message for new advice"
        }
        self.client.force_login(self.first_user)
        url = reverse('laboratory:api-prudence-advice-list',
                      kwargs={"org_pk": self.organization.pk})
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(json.loads(response.content)['detail'],
                         'Item created successfully.')

    def test_get_prudence_advice(self):
        prudence_advice = PrudenceAdvice.objects.get(pk=1)
        self.client.force_login(self.first_user)
        url = reverse("laboratory:api-prudence-advice-detail",
                      kwargs={"org_pk": self.organization.pk,
                              "pk": prudence_advice.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(prudence_advice.pk, json.loads(response.content)['id'])

    def test_update_prudence_advice(self):
        self.client.force_login(self.first_user)
        data = {
            "code": "P616",
            "name": "Changed",
            "prudence_advice_help": "Also changed"
        }
        prudence_advice = PrudenceAdvice.objects.get(pk=1)
        url = reverse('laboratory:api-prudence-advice-detail',
                      kwargs={"org_pk": self.organization.pk,
                              "pk": prudence_advice.pk})
        response = self.client.put(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Refresh comment values
        prudence_advice = PrudenceAdvice.objects.get(pk=1)
        self.assertEqual(prudence_advice.name, 'Changed')

    def test_delete_prudence_advice(self):
        self.client.force_login(self.first_user)
        total_count = PrudenceAdvice.objects.count()
        prudence_advice = PrudenceAdvice.objects.get(pk=15)
        url = reverse("laboratory:api-prudence-advice-detail",
                      kwargs={"org_pk": self.organization.pk,
                              "pk": prudence_advice.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(total_count-1, PrudenceAdvice.objects.count())

    def test_prudence_advice_general_filter_input_returns_filtered_records(self):
        self.client.force_login(self.first_user)
        search_script = '?offset=0&limit=10&draw=4&search=First&' \
                        'ordering=name&_=1687883849018'
        url = reverse('laboratory:api-warnings-table-list',
                      kwargs={"org_pk": self.organization.pk}) + search_script
        response = self.client.get(url)
        result = response.json()
        self.assertNotEquals(result['recordsFiltered'], result['recordsTotal'])
