from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from auth_and_perms.models import Rol
from sga.models import SDSTraceability


class SDSTraceabilityAppMoveTest(TestCase):
    """El modelo se movió de `laboratory` a `sga` conservando la tabla.

    El riesgo del traslado era perder en silencio las asignaciones de permisos:
    si Django creara permisos nuevos bajo `sga`, los antiguos de `laboratory`
    quedarían huérfanos y cada rol que los tuviera se quedaría sin acceso. La
    migración reetiqueta el ContentType para que las filas de auth_permission
    conserven su id y, con ellas, sus asignaciones.
    """

    def test_model_lives_in_the_sga_app(self):
        self.assertEqual(SDSTraceability._meta.app_label, "sga")

    def test_physical_table_is_preserved(self):
        self.assertEqual(SDSTraceability._meta.db_table, "laboratory_sdstraceability")

    def test_content_type_is_unique_and_belongs_to_sga(self):
        content_types = ContentType.objects.filter(model="sdstraceability")
        self.assertEqual(content_types.count(), 1)
        self.assertEqual(content_types.first().app_label, "sga")

    def test_permissions_are_namespaced_under_sga(self):
        codenames = set(
            Permission.objects.filter(
                content_type__model="sdstraceability"
            ).values_list("codename", flat=True)
        )
        self.assertEqual(
            codenames,
            {
                "add_sdstraceability",
                "change_sdstraceability",
                "delete_sdstraceability",
                "view_sdstraceability",
            },
        )
        self.assertFalse(
            Permission.objects.filter(
                content_type__model="sdstraceability",
                content_type__app_label="laboratory",
            ).exists()
        )

    def test_role_and_group_assignments_survive(self):
        """Un rol y un grupo con el permiso lo conservan tras el traslado."""
        permission = Permission.objects.get(
            codename="change_sdstraceability", content_type__model="sdstraceability"
        )
        rol = Rol.objects.create(name="Verificador de fichas")
        rol.permissions.add(permission)
        group = Group.objects.create(name="verificadores")
        group.permissions.add(permission)

        self.assertTrue(rol.permissions.filter(pk=permission.pk).exists())
        self.assertTrue(group.permissions.filter(pk=permission.pk).exists())
        # El nombre con el que el código comprueba el permiso.
        self.assertEqual(
            "%s.%s" % (permission.content_type.app_label, permission.codename),
            "sga.change_sdstraceability",
        )
