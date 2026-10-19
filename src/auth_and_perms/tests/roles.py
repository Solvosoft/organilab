import sys
import unittest

from auth_and_perms.models import Rol
from auth_and_perms.roles import ROLES


def require_role(testcase, key):
    name = ROLES.get(key, key)
    rol = Rol.objects.filter(name=name).first()
    if rol is None:
        if isinstance(testcase, unittest.TestCase):
            where = testcase.id()
        else:
            where = getattr(testcase, "__qualname__", "datos de prueba")
        message = "Rol '%s' no existe en los datos de prueba" % name
        sys.stderr.write("\nSKIP %s: %s\n" % (where, message))
        raise unittest.SkipTest(message)
    return rol


def require_roles(testcase, *keys):
    return [require_role(testcase, key) for key in keys]
