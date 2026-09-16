from unittest import mock

from django.contrib.auth.models import Permission, User
from django.test import TestCase, override_settings
from django.urls import reverse

from auth_and_perms.models import Profile, ProfilePermission, Rol
from laboratory.models import OrganizationStructure

SENTINEL = "centinela-test"
# Sin esta cabecera HandleErrorMiddleware convierte 403/404 en una redirección.
AJAX = {"X-Requested-With": "XMLHttpRequest"}


@override_settings(DELETED_USER_SENTINEL_USERNAME=SENTINEL)
class PlatformUsersAPITest(TestCase):
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        User.objects.create_user(SENTINEL, password="x")
        self.manager = self.create_user("gestor-plataforma")
        self.manager.user_permissions.add(Permission.objects.get(codename="can_manage_users"))
        self.victim = self.create_user("victima")
        self.other = self.create_user("otro")
        self.client.force_login(self.manager)
        self.list_url = reverse("auth_and_perms:api-platformusers-list")

    def create_user(self, username):
        user = User.objects.create_user(username, "%s@example.com" % username, "x")
        Profile.objects.get_or_create(user=user)
        return user

    def detail_url(self, user):
        return reverse("auth_and_perms:api-platformusers-detail", args=[user.pk])

    def merge_url(self, user):
        return reverse("auth_and_perms:api-platformusers-merge", args=[user.pk])

    def test_list_hides_sentinel_and_own_actions(self):
        response = self.client.get(self.list_url, headers=AJAX)
        self.assertEqual(response.status_code, 200)
        rows = {row["username"]: row for row in response.json()["data"]}
        self.assertNotIn(SENTINEL, rows)
        self.assertEqual(rows["gestor-plataforma"]["actions"], {"destroy": False, "merge": False})
        self.assertEqual(rows["victima"]["actions"], {"destroy": True, "merge": True})

    @mock.patch("auth_and_perms.user_merge.notify_user_deleted")
    def test_destroy_deletes_user(self, notify):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(self.detail_url(self.victim), headers=AJAX)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(pk=self.victim.pk).exists())
        notify.assert_called_once()

    def test_cannot_delete_own_user(self):
        response = self.client.delete(self.detail_url(self.manager), headers=AJAX)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(User.objects.filter(pk=self.manager.pk).exists())

    @mock.patch("auth_and_perms.user_merge.notify_user_merged")
    def test_merge(self, notify):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.merge_url(self.other), {"source": self.victim.pk}, headers=AJAX)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(pk=self.victim.pk).exists())
        notify.assert_called_once()

    def test_organization_role_does_not_grant_access(self):
        """Los roles de organización llevan auth.change_user; eso no alcanza."""
        org_admin = self.create_user("admin-org")
        org = OrganizationStructure.objects.first()
        permission = ProfilePermission.objects.create(profile=org_admin.profile, organization=org, content_type_id=1, object_id=org.pk)
        rol = Rol.objects.create(name="rol-con-change-user")
        rol.permissions.add(Permission.objects.get(codename="change_user"), Permission.objects.get(codename="delete_user"))
        permission.rol.add(rol)
        self.client.force_login(org_admin)
        self.assertEqual(self.client.get(self.list_url, headers=AJAX).status_code, 403)
        self.assertEqual(self.client.delete(self.detail_url(self.victim), headers=AJAX).status_code, 403)
        self.assertEqual(self.client.post(self.merge_url(self.other), {"source": self.victim.pk}, headers=AJAX).status_code, 403)
        self.assertEqual(self.client.get(reverse("auth_and_perms:platform_users"), headers=AJAX).status_code, 403)
        self.assertEqual(self.client.get(reverse("platformusers-list"), headers=AJAX).status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.victim.pk).exists())

    def test_page_and_select_for_manager(self):
        self.assertEqual(self.client.get(reverse("auth_and_perms:platform_users")).status_code, 200)
        response = self.client.get(reverse("platformusers-list"), {"term": "victima"}, headers=AJAX)
        self.assertEqual(response.status_code, 200)
        self.assertIn("victima", response.content.decode())
