import datetime

from django.core.files.base import ContentFile
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from presentation.models import *


class FeedbackTest(TestCase):
    fixtures = ["feedback.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.client.force_login(self.user)

    def test_feedback(self):
        response = self.client.get(reverse('feedback'))
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response, template_name='feedback/feedbackentry_form.html')
    def test_add_feedback(self):
        f = ContentFile(b'Hello world!', name='hello-world.pdf')

        data ={
            'title': 'Falla reserva',
            'explanation': "No se efectuo la reserva el día indicado",
            'related_file': f
        }
        pre = FeedbackEntry.objects.count()
        response = self.client.post(reverse('feedback'), data=data, follow=True)
        pos = FeedbackEntry.objects.count()
        self.assertEqual(response.status_code,200)
        self.assertTrue(pos>pre)
        self.assertRedirects(response, reverse('auth_and_perms:select_organization_by_user'))

    def test_add_feedback_lab_org(self):
        f = ContentFile(b'Hello world!', name='hello-world.pdf')

        data ={
            'title': 'Falla reserva',
            'explanation': "No se efectuo la reserva el día indicado",
            'related_file': f,
            'org_pk':1,
            'lab_pk':1
        }
        pre = FeedbackEntry.objects.count()
        response = self.client.post(reverse('feedback'), data=data, follow=True)
        pos = FeedbackEntry.objects.count()
        self.assertEqual(response.status_code,200)
        self.assertTrue(pos>pre)
        self.assertRedirects(response, reverse('laboratory:labindex', kwargs={'lab_pk': 1, 'org_pk': 1}))

    def test_add_feedback_lab_org_fail(self):
        f = ContentFile(b'Hello world!', name='hello-world.pdf')

        data ={
            'title': 'Falla reserva',
            'explanation': "No se efectuo la reserva el día indicado",
            'related_file': f,
            'org_pk':1,
            'lab_pk':1
        }
        pre = FeedbackEntry.objects.count()
        response = self.client.post(reverse('feedback'), data=data, follow=True)
        pos = FeedbackEntry.objects.count()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(pos>pre)
        self.assertRedirects(response, reverse('laboratory:labindex', kwargs={'lab_pk': 1, 'org_pk': 1}))

    def test_index_auth(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code,302)
        self.assertRedirects(response, reverse('auth_and_perms:select_organization_by_user'))
        self.assertTemplateNotUsed(response, 'index.html')

    def test_index_no_auth(self):
        self.client.logout()
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response, 'index.html')


