from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, Client
from django.urls import reverse

from auth_and_perms.models import Profile, ProfilePermission, Rol
from laboratory.models import (
    Laboratory,
    OrganizationStructure,
    OrganizationStructureRelations,
    UserOrganization,
)
from laboratory.utils import resolve_org_for_lab, get_all_user_laboratories


class ResolveOrgForLabTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        Profile.objects.get_or_create(user=self.user)

        self.org_root = OrganizationStructure.objects.create(
            name="Root Org", level=0
        )
        self.org_child = OrganizationStructure.objects.create(
            name="Child Org", level=1, parent=self.org_root
        )
        self.org_grandchild = OrganizationStructure.objects.create(
            name="Grandchild Org", level=2, parent=self.org_child
        )

        self.lab = Laboratory.objects.create(
            name="Test Lab", organization=self.org_child
        )

        self.org_ct = ContentType.objects.get(
            app_label="laboratory", model="organizationstructure"
        )
        self.lab_ct = ContentType.objects.get(
            app_label="laboratory", model="laboratory"
        )

    def _add_org_permission(self, user, org):
        pp, _ = ProfilePermission.objects.get_or_create(
            profile=user.profile,
            content_type=self.org_ct,
            object_id=org.pk,
        )
        return pp

    def _add_lab_permission(self, user, lab):
        pp, _ = ProfilePermission.objects.get_or_create(
            profile=user.profile,
            content_type=self.lab_ct,
            object_id=lab.pk,
        )
        return pp

    def test_user_with_permission_on_lab_org_resolves_to_that_org(self):
        self._add_org_permission(self.user, self.org_child)
        result = resolve_org_for_lab(self.user, self.lab)
        self.assertEqual(result, self.org_child.pk)

    def test_user_with_permission_on_parent_resolves_to_parent(self):
        self._add_org_permission(self.user, self.org_root)
        result = resolve_org_for_lab(self.user, self.lab)
        self.assertEqual(result, self.org_root.pk)

    def test_no_permission_falls_back_to_lab_organization(self):
        result = resolve_org_for_lab(self.user, self.lab)
        self.assertEqual(result, self.lab.organization_id)

    def test_user_with_deepest_org_permission_wins(self):
        self._add_org_permission(self.user, self.org_root)
        self._add_org_permission(self.user, self.org_child)
        result = resolve_org_for_lab(self.user, self.lab)
        self.assertEqual(result, self.org_child.pk)

    def test_lab_shared_via_relations_resolves_correctly(self):
        OrganizationStructureRelations.objects.create(
            organization=self.org_grandchild,
            content_type=self.lab_ct,
            object_id=self.lab.pk,
        )
        self._add_org_permission(self.user, self.org_grandchild)
        result = resolve_org_for_lab(self.user, self.lab)
        self.assertEqual(result, self.org_grandchild.pk)


class GetAllUserLaboratoriesTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        Profile.objects.get_or_create(user=self.user)

        self.org = OrganizationStructure.objects.create(name="Org", level=0)
        self.lab1 = Laboratory.objects.create(name="Lab A", organization=self.org)
        self.lab2 = Laboratory.objects.create(name="Lab B", organization=self.org)
        self.lab3 = Laboratory.objects.create(name="Lab C", organization=self.org)

        self.lab_ct = ContentType.objects.get(
            app_label="laboratory", model="laboratory"
        )
        self.org_ct = ContentType.objects.get(
            app_label="laboratory", model="organizationstructure"
        )

    def test_returns_only_labs_with_permission(self):
        ProfilePermission.objects.create(
            profile=self.user.profile,
            content_type=self.lab_ct,
            object_id=self.lab1.pk,
        )
        ProfilePermission.objects.create(
            profile=self.user.profile,
            content_type=self.lab_ct,
            object_id=self.lab2.pk,
        )

        result = get_all_user_laboratories(self.user)
        lab_pks = {item["lab"].pk for item in result}
        self.assertEqual(lab_pks, {self.lab1.pk, self.lab2.pk})
        self.assertNotIn(self.lab3.pk, lab_pks)

    def test_returns_empty_for_user_without_permissions(self):
        result = get_all_user_laboratories(self.user)
        self.assertEqual(result, [])

    def test_each_result_has_org_pk(self):
        ProfilePermission.objects.create(
            profile=self.user.profile,
            content_type=self.lab_ct,
            object_id=self.lab1.pk,
        )
        result = get_all_user_laboratories(self.user)
        self.assertEqual(len(result), 1)
        self.assertIn("org_pk", result[0])
        self.assertEqual(result[0]["org_pk"], self.org.pk)


class AllLaboratoriesListViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        Profile.objects.get_or_create(user=self.user)

        self.org = OrganizationStructure.objects.create(name="Org", level=0)
        self.lab = Laboratory.objects.create(name="My Lab", organization=self.org)

        lab_ct = ContentType.objects.get(
            app_label="laboratory", model="laboratory"
        )
        ProfilePermission.objects.create(
            profile=self.user.profile,
            content_type=lab_ct,
            object_id=self.lab.pk,
        )

        self.client = Client()
        self.url = reverse("laboratory:all_labs")

    def test_unauthenticated_redirects_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login", response.url)

    def test_authenticated_user_sees_labs(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Lab")
        self.assertTemplateUsed(response, "laboratory/all_laboratories_list.html")

    def test_search_filter_works(self):
        lab2 = Laboratory.objects.create(name="Other Lab", organization=self.org)
        lab_ct = ContentType.objects.get(
            app_label="laboratory", model="laboratory"
        )
        ProfilePermission.objects.create(
            profile=self.user.profile,
            content_type=lab_ct,
            object_id=lab2.pk,
        )

        self.client.force_login(self.user)
        response = self.client.get(self.url, {"search_fil": "Other"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Other Lab")
        self.assertNotContains(response, "My Lab")


class IndexRedirectTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        Profile.objects.get_or_create(user=self.user)
        self.client = Client()

    def test_authenticated_user_redirects_to_all_labs(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("index"))
        self.assertRedirects(
            response,
            reverse("laboratory:all_labs"),
            fetch_redirect_response=False,
        )

    def test_unauthenticated_user_sees_index(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
