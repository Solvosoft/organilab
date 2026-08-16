# -*- coding: utf-8 -*-
"""Pruebas del backfill de ProfilePermission.organization (migración 0033)."""
import importlib

from django.apps import apps as global_apps
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from auth_and_perms.models import Profile, ProfilePermission, Rol
from laboratory.models import Laboratory, OrganizationStructure

migration = importlib.import_module(
    "auth_and_perms.migrations.0033_backfill_profilepermission_organization"
)


class BackfillOrganizationTest(TestCase):
    """La organización se deduce del objeto sobre el que recae el permiso."""

    def setUp(self):
        self.org = OrganizationStructure.objects.create(name="Organización raíz")
        self.lab = Laboratory.objects.create(
            name="Laboratorio de prueba", organization=self.org
        )
        user = User.objects.create_user(username="backfill", password="x")
        self.profile = Profile.objects.create(user=user, id_card="1")
        self.rol = Rol.objects.create(name="Rol de prueba")
        self.org_ct = ContentType.objects.get_for_model(OrganizationStructure)
        self.lab_ct = ContentType.objects.get_for_model(Laboratory)

    def _permission(self, content_type, object_id, organization=None):
        permission = ProfilePermission.objects.create(
            profile=self.profile,
            content_type=content_type,
            object_id=object_id,
            organization=organization,
        )
        permission.rol.add(self.rol)
        return permission

    def _run(self):
        migration.backfill_organization(global_apps, None)

    def test_permission_over_organization_uses_that_organization(self):
        permission = self._permission(self.org_ct, self.org.pk)
        self._run()
        permission.refresh_from_db()
        self.assertEqual(permission.organization_id, self.org.pk)

    def test_permission_over_laboratory_uses_its_organization(self):
        permission = self._permission(self.lab_ct, self.lab.pk)
        self._run()
        permission.refresh_from_db()
        self.assertEqual(permission.organization_id, self.org.pk)

    def test_orphan_permission_is_left_untouched(self):
        # El objeto referenciado no existe: es un permiso huérfano y lo limpia
        # el comando clean_orphaned_profilepermissions, no esta migración.
        permission = self._permission(self.lab_ct, 999999)
        self._run()
        permission.refresh_from_db()
        self.assertIsNone(permission.organization_id)

    def test_does_not_overwrite_an_existing_organization(self):
        other = OrganizationStructure.objects.create(name="Otra organización")
        permission = self._permission(self.lab_ct, self.lab.pk, organization=other)
        self._run()
        permission.refresh_from_db()
        self.assertEqual(permission.organization_id, other.pk)

    def test_permission_over_other_model_is_skipped(self):
        profile_ct = ContentType.objects.get_for_model(Profile)
        permission = self._permission(profile_ct, self.profile.pk)
        self._run()
        permission.refresh_from_db()
        self.assertIsNone(permission.organization_id)

    def test_is_idempotent(self):
        permission = self._permission(self.lab_ct, self.lab.pk)
        self._run()
        permission.refresh_from_db()
        first = permission.organization_id
        self._run()
        permission.refresh_from_db()
        self.assertEqual(permission.organization_id, first)


class GetLabIdsAfterBackfillTest(TestCase):
    """El backfill devuelve a get_lab_ids los laboratorios del perfil.

    Es la razón de ser de la migración: sin `organization`, get_lab_ids filtra
    fuera el permiso y el usuario ve los listados vacíos.
    """

    def setUp(self):
        self.org = OrganizationStructure.objects.create(name="Organización")
        self.lab = Laboratory.objects.create(name="Laboratorio", organization=self.org)
        user = User.objects.create_user(username="lab-user", password="x")
        self.profile = Profile.objects.create(user=user, id_card="2")
        rol = Rol.objects.create(name="Rol con acceso")
        permission = ProfilePermission.objects.create(
            profile=self.profile,
            content_type=ContentType.objects.get_for_model(Laboratory),
            object_id=self.lab.pk,
            organization=None,
        )
        permission.rol.add(rol)

    def test_lab_is_invisible_before_and_visible_after(self):
        from laboratory.models import OrganizationStructureRelations
        from laboratory.utils import get_lab_ids

        OrganizationStructureRelations.objects.create(
            organization=self.org,
            content_type=ContentType.objects.get_for_model(Laboratory),
            object_id=self.lab.pk,
        )

        self.assertEqual(list(get_lab_ids(self.org, self.profile)), [])
        migration.backfill_organization(global_apps, None)
        self.assertEqual(list(get_lab_ids(self.org, self.profile)), [self.lab.pk])
