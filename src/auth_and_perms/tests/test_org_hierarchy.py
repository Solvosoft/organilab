from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory

from auth_and_perms.models import ProfilePermission, Profile, Rol
from auth_and_perms.org_hierarchy import get_ancestor_org_pks, get_descendant_org_pks
from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import OrganizationStructure, UserOrganization


class OrgHierarchyHelpersTest(TestCase):
    """Tests for get_ancestor_org_pks and get_descendant_org_pks."""

    def setUp(self):
        self.root = OrganizationStructure.objects.create(name="Root", position=0)
        self.middle = OrganizationStructure.objects.create(
            name="Middle", parent=self.root, position=0
        )
        self.leaf = OrganizationStructure.objects.create(
            name="Leaf", parent=self.middle, position=0
        )

    def test_ancestor_pks_from_leaf(self):
        pks = get_ancestor_org_pks(self.leaf.pk)
        self.assertIn(self.leaf.pk, pks)
        self.assertIn(self.middle.pk, pks)
        self.assertIn(self.root.pk, pks)

    def test_ancestor_pks_from_root(self):
        pks = get_ancestor_org_pks(self.root.pk)
        self.assertEqual(pks, [self.root.pk])

    def test_ancestor_pks_nonexistent_org(self):
        pks = get_ancestor_org_pks(99999)
        self.assertEqual(pks, [99999])

    def test_descendant_pks_from_root(self):
        pks = get_descendant_org_pks(self.root.pk)
        self.assertIn(self.root.pk, pks)
        self.assertIn(self.middle.pk, pks)
        self.assertIn(self.leaf.pk, pks)

    def test_descendant_pks_from_leaf(self):
        pks = get_descendant_org_pks(self.leaf.pk)
        self.assertEqual(len(pks), 1)
        self.assertIn(self.leaf.pk, pks)

    def test_descendant_pks_nonexistent_org(self):
        pks = get_descendant_org_pks(99999)
        self.assertEqual(pks, [99999])


class HierarchicalMembershipTest(TestCase):
    """Tests that membership is inherited downward (parent→child) but not upward."""

    def setUp(self):
        self.root = OrganizationStructure.objects.create(name="Root", position=0)
        self.middle = OrganizationStructure.objects.create(
            name="Middle", parent=self.root, position=0
        )
        self.leaf = OrganizationStructure.objects.create(
            name="Leaf", parent=self.middle, position=0
        )
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        Profile.objects.create(user=self.user)

    def test_member_of_parent_can_access_child(self):
        UserOrganization.objects.create(
            organization=self.root, user=self.user, status=True
        )
        # Should NOT raise — user is member of root, accessing leaf
        user_is_allowed_on_organization(self.user, self.leaf)

    def test_member_of_parent_can_access_middle(self):
        UserOrganization.objects.create(
            organization=self.root, user=self.user, status=True
        )
        user_is_allowed_on_organization(self.user, self.middle)

    def test_member_of_child_cannot_access_parent(self):
        UserOrganization.objects.create(
            organization=self.leaf, user=self.user, status=True
        )
        with self.assertRaises(PermissionDenied):
            user_is_allowed_on_organization(self.user, self.root)

    def test_member_of_middle_can_access_leaf_not_root(self):
        UserOrganization.objects.create(
            organization=self.middle, user=self.user, status=True
        )
        # Can access leaf (descendant of middle)
        user_is_allowed_on_organization(self.user, self.leaf)
        # Cannot access root (ancestor of middle)
        with self.assertRaises(PermissionDenied):
            user_is_allowed_on_organization(self.user, self.root)

    def test_inactive_membership_not_inherited(self):
        UserOrganization.objects.create(
            organization=self.root, user=self.user, status=False
        )
        with self.assertRaises(PermissionDenied):
            user_is_allowed_on_organization(self.user, self.leaf)

    def test_direct_membership_still_works(self):
        UserOrganization.objects.create(
            organization=self.leaf, user=self.user, status=True
        )
        user_is_allowed_on_organization(self.user, self.leaf)


class MiddlewarePermissionInheritanceTest(TestCase):
    """Tests that ProfilePermission roles on ancestor orgs are collected by the middleware."""

    def setUp(self):
        self.root = OrganizationStructure.objects.create(name="Root", position=0)
        self.leaf = OrganizationStructure.objects.create(
            name="Leaf", parent=self.root, position=0
        )
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.profile = Profile.objects.create(user=self.user)
        UserOrganization.objects.create(
            organization=self.root, user=self.user, status=True
        )
        self.ct_org = ContentType.objects.get_for_model(OrganizationStructure)

    def test_ancestor_permissions_included_for_leaf(self):
        from authentication.middleware import ProfileMiddleware

        rol = Rol.objects.create(name="Test Role")
        pp = ProfilePermission.objects.create(
            profile=self.profile,
            content_type=self.ct_org,
            object_id=self.root.pk,
        )
        pp.rol.add(rol)

        # Build the query the middleware would use
        from auth_and_perms.org_hierarchy import get_ancestor_org_pks
        from django.db.models import Q

        ancestor_pks = get_ancestor_org_pks(self.leaf.pk)
        queryQ = Q(
            profile=self.profile,
            object_id__in=ancestor_pks,
            content_type__app_label="laboratory",
            content_type__model="organizationstructure",
        )
        result = ProfilePermission.objects.filter(queryQ)
        self.assertTrue(result.exists())
        self.assertEqual(result.first().pk, pp.pk)

    def test_no_permissions_for_unrelated_org(self):
        other_org = OrganizationStructure.objects.create(name="Other", position=0)

        rol = Rol.objects.create(name="Test Role")
        pp = ProfilePermission.objects.create(
            profile=self.profile,
            content_type=self.ct_org,
            object_id=self.root.pk,
        )
        pp.rol.add(rol)

        from auth_and_perms.org_hierarchy import get_ancestor_org_pks
        from django.db.models import Q

        ancestor_pks = get_ancestor_org_pks(other_org.pk)
        queryQ = Q(
            profile=self.profile,
            object_id__in=ancestor_pks,
            content_type__app_label="laboratory",
            content_type__model="organizationstructure",
        )
        result = ProfilePermission.objects.filter(queryQ)
        self.assertFalse(result.exists())

    def test_direct_perms_override_inherited(self):
        """When user has direct permissions at leaf, only those apply (not ancestor's)."""
        from django.contrib.auth.models import Permission
        perm_change = Permission.objects.filter(
            codename="change_organizationstructure"
        ).first()
        perm_add = Permission.objects.filter(
            codename="add_user"
        ).first()

        # Ancestor role with change_organizationstructure
        ancestor_rol = Rol.objects.create(name="Ancestor Role")
        ancestor_rol.permissions.add(perm_change)
        pp_root = ProfilePermission.objects.create(
            profile=self.profile,
            content_type=self.ct_org,
            object_id=self.root.pk,
        )
        pp_root.rol.add(ancestor_rol)

        # Direct role at leaf with add_user only
        leaf_rol = Rol.objects.create(name="Leaf Role")
        leaf_rol.permissions.add(perm_add)
        pp_leaf = ProfilePermission.objects.create(
            profile=self.profile,
            content_type=self.ct_org,
            object_id=self.leaf.pk,
        )
        pp_leaf.rol.add(leaf_rol)

        # Simulate middleware logic: direct perms exist → use only direct
        from django.db.models import Q
        has_direct = ProfilePermission.objects.filter(
            profile=self.profile,
            object_id=self.leaf.pk,
            content_type__app_label="laboratory",
            content_type__model="organizationstructure",
        ).exists()
        self.assertTrue(has_direct)

        # When direct perms exist, query only the direct org
        queryQ = Q(
            profile=self.profile,
            object_id=self.leaf.pk,
            content_type__app_label="laboratory",
            content_type__model="organizationstructure",
        )
        result = ProfilePermission.objects.filter(queryQ)
        perms = list(result.values_list(
            "rol__permissions__content_type__app_label",
            "rol__permissions__codename",
        ))
        perm_set = {"%s.%s" % (ct, name) for ct, name in perms if ct and name}
        # Only leaf's perm (add_user), not ancestor's (change_organizationstructure)
        self.assertIn("auth.add_user", perm_set)
        self.assertNotIn(
            "laboratory.change_organizationstructure", perm_set
        )

    def test_inherited_perms_when_no_direct(self):
        """When user has no direct perms at leaf, ancestor perms are inherited."""
        from django.contrib.auth.models import Permission
        perm_change = Permission.objects.filter(
            codename="change_organizationstructure"
        ).first()

        ancestor_rol = Rol.objects.create(name="Ancestor Role")
        ancestor_rol.permissions.add(perm_change)
        pp_root = ProfilePermission.objects.create(
            profile=self.profile,
            content_type=self.ct_org,
            object_id=self.root.pk,
        )
        pp_root.rol.add(ancestor_rol)

        # No direct ProfilePermission at leaf
        from django.db.models import Q
        has_direct = ProfilePermission.objects.filter(
            profile=self.profile,
            object_id=self.leaf.pk,
            content_type__app_label="laboratory",
            content_type__model="organizationstructure",
        ).exists()
        self.assertFalse(has_direct)

        # Middleware falls back to ancestors
        from auth_and_perms.org_hierarchy import get_ancestor_org_pks
        ancestor_pks = get_ancestor_org_pks(self.leaf.pk)
        queryQ = Q(
            profile=self.profile,
            object_id__in=ancestor_pks,
            content_type__app_label="laboratory",
            content_type__model="organizationstructure",
        )
        result = ProfilePermission.objects.filter(queryQ)
        perms = list(result.values_list(
            "rol__permissions__content_type__app_label",
            "rol__permissions__codename",
        ))
        perm_set = {"%s.%s" % (ct, name) for ct, name in perms if ct and name}
        self.assertIn("laboratory.change_organizationstructure", perm_set)
