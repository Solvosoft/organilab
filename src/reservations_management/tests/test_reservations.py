from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
import json

from reservations_management.models import Reservations


class ReservationsTest(TestCase):
    fixtures = ["object.json", "reservations.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.url_attr= {'org_pk':1}
        self.client.force_login(self.user)

    def test_get_update_reservation(self):
        self.url_attr['pk'] = 1
        reservation= Reservations.objects.get(pk=1)
        response = self.client.get(reverse('reservations_management:manage_reservation', kwargs=self.url_attr))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['object']==reservation)
        self.assertTemplateUsed(response, template_name='reservations_management/manage_reservation.html')

    def test_post_update_reservation(self):
        self.url_attr['pk'] = 1
        data = {
            "status":3,
            "comments":"Errors"

        }
        response = self.client.post(reverse('reservations_management:manage_reservation', kwargs=self.url_attr), data=data)
        reservation= Reservations.objects.get(pk=1)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(data['comments']==reservation.comments)
        self.assertRedirects(response, reverse("reservations_management:reservations_list",kwargs={'status': 3, 'org_pk':1}))

    def test_getlist_reservation(self):
        self.url_attr['status'] = 1
        response = self.client.get(reverse('reservations_management:reservations_list', kwargs=self.url_attr))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['reservations'].count()==1)

    def test_get_info_reservation(self):
        response = self.client.get(reverse('reservations_management:get_product_name_and_quantity', kwargs=self.url_attr)+'?id=1')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)['product_name']=='Embudo espiga corta 10 cm')

    def test_validate_reservation(self):
        data = {
            'id': 1
        }
        response = self.client.get(reverse('reservations_management:validate_reservation', kwargs=self.url_attr), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)['is_valid']==False)

    def test_increasee_stock(self):
        response = self.client.get(reverse('reservations_management:increase_stock', kwargs=self.url_attr)+'?id=1&amount_to_return=98.5')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)['was_increase']==True)



