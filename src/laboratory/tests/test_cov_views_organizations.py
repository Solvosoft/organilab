"""Acciones sobre organizaciones: desactivar, activar, clonar, renombrar y mover.

Cubre `OrganizationActionsFormview` (los tres formularios según el prefijo) y la
transferencia de laboratorios al nuevo root en `OrganizationUpdateView`.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from auth_and_perms.models import Profile
from laboratory.models import (
    Laboratory,
    OrganizationStructure,
    OrganizationStructureRelations,
    UserOrganization,
)
from laboratory.tests.utils import BaseLaboratorySetUpTest


def assert_error_page(test, response, status):
    """`HandleErrorMiddleware` convierte 403/404 en redirección a la página de error."""
    test.assertEqual(response.status_code, 302)
    test.assertIn("status=%d" % status, response["Location"])


class OrganizationActionsViewTest(BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        perm = Permission.objects.get(
            content_type__app_label="laboratory",
            codename="change_organizationstructure",
        )
        self.user.user_permissions.add(perm)
        self.url = reverse("laboratory:organization_actions")
        self.success_url = reverse("auth_and_perms:organizationManager")
        self.child = OrganizationStructure.objects.create(
            name="Hija de Investigadores", parent=self.org, position=1, level=2
        )
        self.child.users.add(self.user)

    def test_desactivar_organizacion_con_padre(self):
        posicion_esperada = self.org.min_child_position - 1
        response = self.client.post(
            self.url,
            {"actions": "1", "action_organization": self.child.pk, "name": "x"},
        )
        self.assertRedirects(response, self.success_url, fetch_redirect_response=False)
        self.child.refresh_from_db()
        self.assertFalse(self.child.active)
        self.assertEqual(self.child.position, posicion_esperada)

    def test_renombrar_organizacion(self):
        response = self.client.post(
            self.url,
            {
                "actions": "3",
                "action_organization": self.child.pk,
                "name": "Nombre nuevo",
            },
        )
        self.assertRedirects(response, self.success_url, fetch_redirect_response=False)
        self.child.refresh_from_db()
        self.assertEqual(self.child.name, "Nombre nuevo")

    def test_renombrar_con_prefijo_sin_desactivar(self):
        response = self.client.post(
            self.url,
            {
                "prefix": "wi",
                "wi-actions": "3",
                "wi-action_organization": self.child.pk,
                "wi-name": "Renombrada wi",
            },
        )
        self.assertRedirects(response, self.success_url, fetch_redirect_response=False)
        self.child.refresh_from_db()
        self.assertEqual(self.child.name, "Renombrada wi")

    def test_activar_organizacion_con_padre(self):
        self.child.active = False
        self.child.save()
        response = self.client.post(
            self.url,
            {
                "prefix": "clone",
                "clone-actions": "4",
                "clone-action_organization": self.child.pk,
            },
        )
        self.assertRedirects(response, self.success_url, fetch_redirect_response=False)
        self.child.refresh_from_db()
        self.assertTrue(self.child.active)

    def test_clonar_organizacion_copia_relaciones_roles_y_usuarios(self):
        lab_ct = ContentType.objects.get_for_model(Laboratory)
        OrganizationStructureRelations.objects.create(
            organization=self.child, content_type=lab_ct, object_id=self.lab.pk
        )
        UserOrganization.objects.create(
            organization=self.child,
            user=self.user,
            type_in_organization=UserOrganization.LABORATORY_MANAGER,
        )
        roles_root = self.org.rol.count()
        response = self.client.post(
            self.url,
            {
                "prefix": "clone",
                "clone-actions": "2",
                "clone-action_organization": self.child.pk,
            },
        )
        self.assertRedirects(response, self.success_url, fetch_redirect_response=False)
        clone = OrganizationStructure.objects.get(name="Hija de Investigadores-clone")
        self.assertEqual(clone.parent, self.org)
        self.assertTrue(clone.users.filter(pk=self.user.pk).exists())
        self.assertTrue(
            OrganizationStructureRelations.objects.filter(
                organization=clone, content_type=lab_ct, object_id=self.lab.pk
            ).exists()
        )
        self.assertEqual(clone.rol.count(), roles_root)
        self.assertTrue(
            UserOrganization.objects.filter(
                organization=clone,
                user=self.user,
                type_in_organization=UserOrganization.LABORATORY_MANAGER,
            ).exists()
        )

    def test_formulario_invalido_redirige_sin_cambios(self):
        response = self.client.post(self.url, {"actions": "99"})
        self.assertRedirects(response, self.success_url, fetch_redirect_response=False)
        self.child.refresh_from_db()
        self.assertTrue(self.child.active)

    def test_organizacion_ajena_devuelve_403(self):
        ajena = OrganizationStructure.objects.get(name="Organization Testing")
        response = self.client.post(
            self.url,
            {"actions": "3", "action_organization": ajena.pk, "name": "Robada"},
        )
        assert_error_page(self, response, 403)
        ajena.refresh_from_db()
        self.assertEqual(ajena.name, "Organization Testing")


class OrganizationUpdateTransferTest(BaseLaboratorySetUpTest):

    def test_mover_root_con_laboratorio_crea_relacion_en_nuevo_root(self):
        root = OrganizationStructure.objects.create(
            name="Root a mover", position=9, level=1
        )
        root.users.add(self.user)
        lab = Laboratory.objects.create(name="Lab del root", organization=root)
        url = reverse("laboratory:update_organization", kwargs={"pk": root.pk})
        response = self.client.post(url, {"parent": self.org.pk})
        self.assertRedirects(
            response,
            reverse("auth_and_perms:organizationManager"),
            fetch_redirect_response=False,
        )
        root.refresh_from_db()
        self.assertEqual(root.parent, self.org)
        self.assertTrue(
            OrganizationStructureRelations.objects.filter(
                organization=self.org,
                content_type=ContentType.objects.get_for_model(Laboratory),
                object_id=lab.pk,
            ).exists()
        )


class OrganizationActionsSinPermisoTest(BaseLaboratorySetUpTest):

    def test_usuario_sin_permiso_recibe_403(self):
        user = get_user_model().objects.get(username="tuwp")
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.client.force_login(user)
        response = self.client.post(
            reverse("laboratory:organization_actions"),
            {"actions": "3", "action_organization": self.org.pk, "name": "x"},
        )
        assert_error_page(self, response, 403)
