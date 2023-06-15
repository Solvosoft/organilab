import json

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from sga.models import Substance, ReviewSubstance, \
    SGAComplement
from sga.models import SubstanceObservation


class SGAAcademicTest(TestCase):
    fixtures = ["substances.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.url_attr = {'org_pk': 1}
        self.client.force_login(self.user)

    def test_add_substance(self):
        data = {
            'comercial_name': "h20",
            'uipa_name': "Aqua",
            'synonymous': '[{"value":"s"},{"value":"a"}]',
            'agrochemical': True,
            'organization': 1,
            'description': "Agua hidratante",
            'brand': "Limon",
            'iarc': 2,
            'imdg': 79,
            'white_organ': [5, 9, 11],
            'bioaccumulable': False,
            'molecular_formula': "411",
            'cas_id_number': "48a-58",
            'is_precursor': False,
            'precursor_type': 87,
            'ue_code': [88, 100],
            'nfpa': [114, 120],
            'storage_class': [135, 140, 154],
            'seveso_list': True,
            'number_index': "156",
            'number_ce': "464",
            'molecular_weight': "20g",
            'concentration': "20%"
        }
        count = Substance.objects.count()
        response = self.client.post(
            reverse('sga:create_sustance', kwargs=self.url_attr), data=data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Substance.objects.count() > count)
        self.assertRedirects(response,
                             reverse('sga:step_two', kwargs={'org_pk': 1, 'pk': 1}))

    def test_update_substance(self):
        data = {
            'comercial_name': "h20",
            'uipa_name': "Aqua",
            'synonymous': '[{"value":"s"},{"value":"a"}]',
            'agrochemical': True,
            'organization': 1,
            'description': "Agua hidratante",
            'brand': "Limon",
            'iarc': 2,
            'imdg': 79,
            'white_organ': [5, 9, 11],
            'bioaccumulable': False,
            'molecular_formula': "411",
            'cas_id_number': "48a-58",
            'is_precursor': False,
            'precursor_type': 87,
            'ue_code': [88, 100],
            'nfpa': [114, 120],
            'storage_class': [135, 140, 154],
            'seveso_list': True,
            'number_index': "156",
            'number_ce': "464",
            'molecular_weight': "20g",
            'concentration': "20%"
        }
        count = Substance.objects.count()
        url = self.url_attr.copy()
        url['pk'] = 134

        response = self.client.post(reverse('sga:update_substance', kwargs=url),
                                    data=data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Substance.objects.count() == count)
        c = SGAComplement.objects.last().pk
        self.assertRedirects(response,
                             reverse('sga:step_two', kwargs={'org_pk': 1, 'pk': c}))

    def test_get_substance(self):
        url = self.url_attr.copy()
        url['pk'] = 134

        response = self.client.get(reverse('sga:update_substance', kwargs=url))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['substance'] == 134)
        self.assertTrue(response.context['complement'] == 2)
        self.assertTrue(response.context['step'] == 1)

    def test_get_substances(self):
        response = self.client.get(reverse('sga:get_substance', kwargs=self.url_attr))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context['substances']) == 1)

    def test_delete_substance(self):
        url = self.url_attr.copy()
        url['pk'] = 134

        response = self.client.delete(reverse('sga:delete_substance', kwargs=url))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Substance.objects.filter(
            organization__pk=self.url_attr['org_pk']).count() == 0)
        self.assertRedirects(response,
                             reverse('sga:get_substance', kwargs=self.url_attr))

    def test_detail_substance(self):
        url = self.url_attr.copy()
        url['pk'] = 134

        response = self.client.get(reverse('sga:detail_substance', kwargs=url))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context['observations']) == 0)
        self.assertTrue(response.context['object'] != None)

    def test_add_observation(self):
        url = self.url_attr.copy()
        url['substance'] = 134
        response = self.client.post(reverse('sga:add_observation', kwargs=url),
                                    data={'description': 'Simple'})
        obs = SubstanceObservation.objects.all().values_list('description', flat=True)
        del url['substance']
        url['pk'] = 134

        self.assertEqual(response.status_code, 302)
        self.assertIn("Simple", obs)
        self.assertTrue(self.client.session["step"] == 2)
        self.assertRedirects(response, reverse('sga:detail_substance', kwargs=url))

    def test_update_observation(self):
        s = Substance.objects.get(pk=134)
        obs = SubstanceObservation.objects.create(description='Hello', substance=s)
        url = self.url_attr.copy()
        response = self.client.post(reverse('sga:update_observation', kwargs=url),
                                    data={'description': 'Simple', 'pk': obs.pk})
        obs = SubstanceObservation.objects.last().description

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Simple" == obs)
        self.assertTrue(SubstanceObservation.objects.count() == 1)
        self.assertTrue(self.client.session["step"] == 2)
        self.assertTrue(json.loads(response.content)['status'] == True)

    def test_delete_observation(self):
        s = Substance.objects.get(pk=134)
        obs = SubstanceObservation.objects.create(description='Hello', substance=s)
        url = self.url_attr.copy()
        pre = SubstanceObservation.objects.count()

        response = self.client.post(reverse('sga:delete_observation', kwargs=url),
                                    data={'pk': obs.pk})
        obs = SubstanceObservation.objects.count()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(pre > obs)
        self.assertTrue(self.client.session["step"] == 2)
        self.assertTrue(json.loads(response.content)['status'] == True)

    def test_getlist_substance(self):
        url = self.url_attr.copy()

        response = self.client.get(reverse('sga:approved_substance', kwargs=url))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['showapprove'] == False)

    def test_approve_substance(self):
        s = Substance.objects.get(pk=134)
        review = ReviewSubstance.objects.create(substance=s, note=70)
        url = self.url_attr.copy()
        url['pk'] = review.pk

        response = self.client.post(reverse('sga:accept_substance', kwargs=url))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             reverse('sga:approved_substance', kwargs=self.url_attr))

    def test_step_one_substance(self):
        data = {
            'comercial_name': "h20",
            'uipa_name': "Aqua",
            'synonymous': '[{"value":"s"},{"value":"a"}]',
            'agrochemical': True,
            'organization': 1,
            'description': "Agua hidratante",
            'brand': "Limon",
            'iarc': 2,
            'imdg': 79,
            'white_organ': [5, 9, 11],
            'bioaccumulable': False,
            'molecular_formula': "411",
            'cas_id_number': "48a-58",
            'is_precursor': False,
            'precursor_type': 87,
            'ue_code': [88, 100],
            'nfpa': [114, 120],
            'storage_class': [135, 140, 154],
            'seveso_list': True,
            'number_index': "156",
            'number_ce': "464",
            'molecular_weight': "20g",
            'concentration': "20%"
        }
        count = Substance.objects.count()
        url = self.url_attr.copy()
        url['pk'] = 134

        response = self.client.post(reverse('sga:step_one', kwargs=url), data=data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Substance.objects.count() == count)
        c = SGAComplement.objects.last().pk
        self.assertRedirects(response,
                             reverse('sga:step_two', kwargs={'org_pk': 1, 'pk': c}))
