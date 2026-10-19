import unittest
from unittest import mock

from django.test import TestCase

from auth_and_perms.models import Rol
from auth_and_perms.roles import ROLES
from auth_and_perms.tests.roles import require_role, require_roles


class RequireRoleTest(TestCase):
    def test_devuelve_el_rol_por_id_o_por_nombre(self):
        rol = Rol.objects.create(name=ROLES["regente"])
        self.assertEqual(require_role(self, "regente"), rol)
        self.assertEqual(require_role(self, ROLES["regente"]), rol)

    def test_rol_faltante_salta_el_test_y_lo_avisa(self):
        Rol.objects.filter(name=ROLES["auditor_iper"]).delete()
        with mock.patch("sys.stderr") as stderr:
            with self.assertRaises(unittest.SkipTest) as error:
                require_role(self, "auditor_iper")
        self.assertIn("Auditor IPER", str(error.exception))
        self.assertIn(self.id(), stderr.write.call_args.args[0])

    def test_rol_faltante_desde_la_preparacion_de_la_clase(self):
        Rol.objects.filter(name=ROLES["auditor_iper"]).delete()
        with mock.patch("sys.stderr") as stderr:
            with self.assertRaises(unittest.SkipTest):
                require_role(RequireRoleTest, "auditor_iper")
        self.assertIn("RequireRoleTest", stderr.write.call_args.args[0])

    def test_varios_roles(self):
        roles = [Rol.objects.create(name=ROLES[key]) for key in ("sga", "regente")]
        self.assertEqual(require_roles(self, "sga", "regente"), roles)
