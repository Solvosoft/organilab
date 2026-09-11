"""
Tests for OrganizationLabRelationDeleteViewSet.
Tests the CRUDAL functionality for listing and deleting OrganizationStructureRelations
where content_type is Laboratory.
"""
import json

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.urls import reverse

from auth_and_perms.models import ProfilePermission, Rol
from laboratory.models import (
    Laboratory,
    OrganizationStructure,
    OrganizationStructureRelations,
)
from laboratory.tests.utils import BaseSetUpAjaxRequest


class OrganizationLabRelationDeleteViewSetTest(BaseSetUpAjaxRequest):
    """Tests for the OrganizationLabRelationDeleteViewSet."""

    def setUp(self):
        super().setUp()

        # Get content types
        self.lab_ct = ContentType.objects.get(app_label="laboratory", model="laboratory")
        self.org_ct = ContentType.objects.get(
            app_label="laboratory", model="organizationstructure"
        )

        # Create relation between org1 and lab3 (lab3 belongs to org1)
        self.relation1, _ = OrganizationStructureRelations.objects.get_or_create(
            organization=self.org1,
            content_type=self.lab_ct,
            object_id=self.lab3_org1.pk,
        )

        # Create a ProfilePermission for user3 on lab3 in org1
        self.pp_user3_lab3 = ProfilePermission.objects.create(
            profile=self.profile3_org1,
            content_type=self.lab_ct,
            object_id=self.lab3_org1.pk,
            organization=self.org1,
        )
        self.pp_user3_lab3.rol.add(self.role_manage_lab)

        # Add permissions to user1
        perm_view = Permission.objects.get(
            codename="view_organizationstructurerelations"
        )
        perm_delete = Permission.objects.get(
            codename="delete_organizationstructurerelations"
        )
        self.user1_org1.user_permissions.add(perm_view, perm_delete)

        # URLs
        self.list_url = reverse(
            "auth_and_perms:api-org-lab-relation-list",
            kwargs={"org_pk": self.org1.pk},
        )
        self.detail_url = reverse(
            "auth_and_perms:api-org-lab-relation-detail",
            kwargs={"org_pk": self.org1.pk, "pk": self.relation1.pk},
        )

    def test_list_lab_relations_returns_only_laboratory_content_type(self):
        """
        Test that listing returns only OrganizationStructureRelations
        where content_type is Laboratory, not other content types.
        """
        # Create a relation with a different content type (org)
        OrganizationStructureRelations.objects.create(
            organization=self.org1,
            content_type=self.org_ct,
            object_id=self.org2.pk,
        )

        response = self.client1_org1.get(self.list_url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        # Should only return lab relations, not org relations
        for item in data.get("data", data.get("results", [])):
            # Verify each item is a lab relation
            relation = OrganizationStructureRelations.objects.get(pk=item["id"])
            self.assertEqual(relation.content_type, self.lab_ct)

    def test_list_lab_relations_filters_by_organization(self):
        """
        Test that listing only returns relations for the specified organization.
        """
        # Create a relation for org2
        relation_org2 = OrganizationStructureRelations.objects.create(
            organization=self.org2,
            content_type=self.lab_ct,
            object_id=self.lab2_org2.pk,
        )

        response = self.client1_org1.get(self.list_url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        relation_ids = [item["id"] for item in data.get("data", data.get("results", []))]

        # Should contain org1 relation but not org2 relation
        self.assertIn(self.relation1.pk, relation_ids)
        self.assertNotIn(relation_org2.pk, relation_ids)

    def test_delete_lab_relation_success(self):
        """
        Test that a user with permissions can delete a lab relation.
        """
        # Verify relation exists
        self.assertTrue(
            OrganizationStructureRelations.objects.filter(pk=self.relation1.pk).exists()
        )

        response = self.client1_org1.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)

        # Verify relation was deleted
        self.assertFalse(
            OrganizationStructureRelations.objects.filter(pk=self.relation1.pk).exists()
        )

    def test_delete_lab_relation_removes_profile_permissions(self):
        """
        Test that deleting a lab relation also removes ProfilePermissions
        for users on that laboratory in that organization.
        """
        # Verify ProfilePermission exists before delete
        self.assertTrue(
            ProfilePermission.objects.filter(
                pk=self.pp_user3_lab3.pk,
            ).exists()
        )

        response = self.client1_org1.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)

        # Verify ProfilePermission was also deleted
        self.assertFalse(
            ProfilePermission.objects.filter(
                profile=self.profile3_org1,
                content_type=self.lab_ct,
                object_id=self.lab3_org1.pk,
                organization=self.org1,
            ).exists()
        )

    def test_delete_lab_relation_without_permission_fails(self):
        """
        Test that a user without delete permission cannot delete a lab relation.
        """
        # Create a client without delete permission
        client_no_perm = Client()
        client_no_perm.force_login(self.user3_org1)

        # Add only view permission to user3
        perm_view = Permission.objects.get(
            codename="view_organizationstructurerelations"
        )
        self.user3_org1.user_permissions.add(perm_view)

        response = client_no_perm.delete(self.detail_url)
        self.assertEqual(response.status_code, 403)

        # Verify relation still exists
        self.assertTrue(
            OrganizationStructureRelations.objects.filter(pk=self.relation1.pk).exists()
        )
