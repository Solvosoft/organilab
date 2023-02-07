from django.urls import reverse

from laboratory.models import OrganizationStructure
from laboratory.tests.utils import BaseSetUpTest

class OrganizationViewTest(BaseSetUpTest):

    def test_update_organization(self):
        url = reverse("laboratory:update_organization", kwargs={"pk": 3, })

        data = {
            "name": "Org BM",
            "parent": 1,
        }
        response_post = self.client.post(url, data=data)
        success_url = reverse("auth_and_perms:organizationManager")
        self.assertRedirects(response_post, success_url)

    def test_create_organization(self):
        data = {
            "name": "SKO Company",
            "parent": 1,
        }
        url = reverse("laboratory:create_organization")
        response = self.client.post(url, data=data)
        success_url = reverse("auth_and_perms:organizationManager")
        self.assertRedirects(response, success_url)
        self.assertIn("SKO Company", list(OrganizationStructure.objects.values_list("name", flat=True)))

    def test_delete_organization(self):
        url = reverse("laboratory:delete_organization", kwargs={"pk": 2, })
        response = self.client.post(url)
        success_url = reverse("auth_and_perms:organizationManager")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, success_url)

    def test_get_reports_list(self):
        url = reverse("laboratory:reports", kwargs={"org_pk": self.org.pk, })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
#
    def test_get_logentry_list(self):
        url = reverse("laboratory:logentry_list", kwargs={"org_pk": self.org.pk, })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
#
    def test_organization_building_report(self):
        url = reverse("laboratory:reports_organization_building", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
#
    def test_organization_report(self):
        url = reverse("laboratory:reports_organization", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

class ProfileViewTest(BaseSetUpTest):

    def test_update_password(self):
        url = reverse("laboratory:password_change", kwargs={"pk": 1})

        data = {
            "password": "edu4060cal",
            "password_confirm": "edu4060cal"
        }
        response_post = self.client.post(url, data=data)
        success_url = reverse("laboratory:profile", kwargs={"pk": 1, })
        self.assertRedirects(response_post, success_url)

    def test_update_profile(self):
        url = reverse("laboratory:profile", kwargs={"pk": 1, })

        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Zárate Montero")

        data = {
            "username": "german",
            "last_name": "Rojas Montero",
            "first_name": "Eduardo",
            "email": "gedzar@gmail.com"
        }
        response_post = self.client.post(url, data=data)
        success_url = reverse("laboratory:profile", kwargs={"pk": 1, })
        self.assertRedirects(response_post, success_url)
        self.assertEqual(self.user.last_name, "Rojas Montero")