from django.contrib.auth.models import User
from django.urls import reverse

from laboratory.models import OrganizationStructure
from laboratory.tests.utils import BaseLaboratorySetUpTest

class OrganizationViewTest(BaseLaboratorySetUpTest):

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

class ProfileViewTest(BaseLaboratorySetUpTest):

    def test_update_password(self):
        url = reverse("laboratory:password_change", kwargs={"pk": self.user.pk})

        data = {
            "password": "edu4060cal",
            "password_confirm": "edu4060cal"
        }
        response_post = self.client.post(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        success_url = reverse("laboratory:profile", kwargs={"pk": self.user.pk, })
        self.assertRedirects(response_post, success_url)

    def test_update_profile(self):
        url = reverse("laboratory:profile", kwargs={"pk": self.user.pk, })

        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        self.assertEqual(response_get.context['user'].email, "orgadmin@gmail.com")

        data = {
            "username": "admin",
            "last_name": "Organilab",
            "first_name": "Admin",
            "email": "orgadmin@gmail.com"
        }
        response_post = self.client.post(url, data=data)
        self.assertEqual(response_post.status_code, 200)
        self.assertEqual(self.user.first_name, "Admin")