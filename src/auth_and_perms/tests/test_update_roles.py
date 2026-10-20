from io import StringIO

from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.test import TestCase

from auth_and_perms.management.commands.update_roles import sync_roles
from auth_and_perms.models import Rol
from auth_and_perms.roles import ROLE_DEFINITIONS, ROLES, ROOT_ORGANIZATION
from laboratory.models import OrganizationStructure


def permission_names(rol):
    return {"%s.%s" % p for p in rol.permissions.values_list("content_type__app_label", "codename")}


def existing(perms):
    available = {"%s.%s" % p for p in Permission.objects.values_list("content_type__app_label", "codename")}
    return set(perms) & available


class UpdateRolesTest(TestCase):

    def setUp(self):
        Rol.objects.filter(name__in=[ROLES["sga"], ROLES["analista_ambiental"], ROLES["organization_management"]]).delete()
        self.root, _ = OrganizationStructure.objects.get_or_create(name=ROOT_ORGANIZATION, parent=None)

    def run_command(self, *args):
        out = StringIO()
        call_command("update_roles", *args, stdout=out)
        return out.getvalue()

    def test_deja_los_permisos_exactos_del_archivo(self):
        rol = Rol.objects.create(name=ROLES["sga"], description="vieja")
        sobrante = Permission.objects.get(content_type__app_label="laboratory", codename="delete_laboratory")
        rol.permissions.add(sobrante)

        sync_roles(["sga"])

        rol.refresh_from_db()
        definition = ROLE_DEFINITIONS["sga"]
        self.assertEqual(permission_names(rol), existing(definition["permissions"]))
        self.assertNotIn("laboratory.delete_laboratory", permission_names(rol))
        self.assertEqual(rol.description, definition["description"])

    def test_crea_el_rol_faltante_asociado_a_la_raiz(self):
        sync_roles(["analista_ambiental"])

        rol = Rol.objects.get(name=ROLES["analista_ambiental"])
        self.assertIn(rol, self.root.rol.all())
        self.assertEqual(permission_names(rol), existing(ROLE_DEFINITIONS["analista_ambiental"]["permissions"]))

    def test_no_crea_el_rol_que_es_por_organizacion(self):
        sync_roles(["organization_management"])
        self.assertFalse(Rol.objects.filter(name=ROLES["organization_management"]).exists())

    def test_segunda_corrida_no_cambia_nada(self):
        self.run_command()
        changes = sync_roles()
        self.assertFalse([c["rol"].name for c in changes if c["created"] or c["added"] or c["removed"] or c["description"]])

    def test_dry_run_no_guarda(self):
        output = self.run_command("--dry-run")
        self.assertIn("%s [nuevo]" % ROLES["analista_ambiental"], output)
        self.assertFalse(Rol.objects.filter(name=ROLES["analista_ambiental"]).exists())
