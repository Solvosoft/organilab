"""Validación de los formularios de `auth_and_perms`."""

from django.contrib.auth.models import Group

from auth_and_perms.forms import (
    OrganizationActions,
    OrganizationActionsWithoutInactive,
    OrganizationForViewsetForm,
    ProfileGroupForm,
)
from auth_and_perms.tests.escenario import EscenarioOrganizaciones


class FormulariosDeOrganizacionTest(EscenarioOrganizaciones):
    def setUp(self):
        self.org_b.active = False
        self.org_b.save()

    def test_organizacion_inactiva_no_sirve_para_los_viewsets(self):
        form = OrganizationForViewsetForm(data={"organization": self.org_b.pk})
        self.assertFalse(form.is_valid())
        self.assertIn("organization", form.errors)
        self.assertTrue(OrganizationForViewsetForm(data={"organization": self.org_a.pk}).is_valid())

    def test_no_se_inactiva_ni_renombra_una_organizacion_inactiva(self):
        for accion in ("1", "3"):
            with self.subTest(accion=accion):
                form = OrganizationActions(
                    data={"actions": accion, "action_organization": self.org_b.pk, "name": "Nuevo nombre"}
                )
                self.assertFalse(form.is_valid())
                self.assertIn("action_organization", form.errors)

    def test_una_organizacion_inactiva_si_se_puede_activar_o_clonar(self):
        for accion in ("2", "4"):
            with self.subTest(accion=accion):
                form = OrganizationActions(
                    data={"actions": accion, "action_organization": self.org_b.pk, "name": "x"}
                )
                self.assertTrue(form.is_valid(), form.errors)

    def test_variante_sin_inactivar_solo_ofrece_clonar_y_renombrar(self):
        form = OrganizationActionsWithoutInactive(
            data={"actions": "1", "action_organization": self.org_a.pk, "name": "x"}
        )
        self.assertEqual([c for c, _ in form.fields["actions"].choices], [2, 3])
        self.assertFalse(form.is_valid())
        self.assertIn("actions", form.errors)

    def test_grupos_de_perfil_en_organizacion_inactiva(self):
        user = self.crear_usuario("con-grupos", self.org_a)
        grupo = Group.objects.create(name="Grupo de prueba")
        datos = {"profile": user.pk, "groups": [grupo.pk]}
        form = ProfileGroupForm(data={**datos, "organization": self.org_b.pk})
        self.assertFalse(form.is_valid())
        self.assertIn("organization", form.errors)
        form = ProfileGroupForm(data={**datos, "organization": self.org_a.pk})
        self.assertTrue(form.is_valid(), form.errors)

    def test_grupos_de_perfil_en_organizacion_inexistente(self):
        user = self.crear_usuario("con-grupos", self.org_a)
        form = ProfileGroupForm(data={"profile": user.pk, "groups": [], "organization": 999999})
        self.assertFalse(form.is_valid())
        self.assertIn("organization", form.errors)
