import json

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from auth_and_perms.management.commands.update_roles import update_ambiental_roles
from auth_and_perms.models import Profile, ProfilePermission, Rol
from laboratory.models import OrganizationStructure, UserOrganization
from presentation.models import SystemParameter
from presentation.parameters import (
    ORIGIN_DEFAULT,
    ORIGIN_INHERITED,
    ORIGIN_OWN,
    cast_value,
    get_parameter,
    resolve_parameter,
)


def make_role_user(username, organization, rol_name):
    user = User.objects.create_user(username=username, password="pass")
    profile = Profile.objects.create(user=user)
    UserOrganization.objects.create(user=user, organization=organization, type_in_organization=1, status=True)
    permission = ProfilePermission.objects.create(
        profile=profile, organization=organization,
        content_type=ContentType.objects.get_for_model(OrganizationStructure), object_id=organization.pk,
    )
    permission.rol.add(Rol.objects.get(name=rol_name))
    return user


class PlatformTestCase(TestCase):
    """Organización raíz con una hija; los roles salen de `update_roles`."""

    @classmethod
    def setUpTestData(cls):
        Rol.objects.get_or_create(name="Administrativo superior")
        update_ambiental_roles()
        cls.root = OrganizationStructure.objects.create(name="Universidad")
        cls.child = OrganizationStructure.objects.create(name="Escuela", parent=cls.root)
        cls.user = make_role_user("superior", cls.child, "Administrativo superior")

    def setUp(self):
        self.client.force_login(self.user)


class ParameterResolutionTest(PlatformTestCase):

    def test_default_then_inherited_then_own(self):
        key = "ambiental.alert_window_months"
        self.assertEqual(resolve_parameter(self.child, key)["origin"], ORIGIN_DEFAULT)
        self.assertEqual(get_parameter(self.child, key), 12)

        SystemParameter.objects.create(organization=self.root, key=key, raw_value="6")
        resolved = resolve_parameter(self.child, key)
        self.assertEqual((resolved["value"], resolved["origin"], resolved["source"]), (6, ORIGIN_INHERITED, self.root))

        SystemParameter.objects.create(organization=self.child, key=key, raw_value="3")
        self.assertEqual(resolve_parameter(self.child, key)["origin"], ORIGIN_OWN)
        self.assertEqual(get_parameter(self.child.pk, key), 3)
        self.assertEqual(get_parameter(self.root, key), 6)

    def test_cast(self):
        self.assertIs(cast_value("bool", "Sí"), True)
        self.assertIs(cast_value("bool", "false"), False)
        with self.assertRaises(ValueError):
            cast_value("int", "doce")


class ParameterAPITest(PlatformTestCase):

    def url(self, name, **kwargs):
        return reverse("platform:api-systemparameter-" + name, kwargs={"org_pk": self.child.pk, **kwargs})

    def test_list_shows_value_and_origin(self):
        response = self.client.get(self.url("list"))
        self.assertEqual(response.status_code, 200, response.content)
        rows = {row["key"]: row for row in response.json()["data"]}
        self.assertEqual(rows["ambiental.alert_window_months"]["value"], "12")
        self.assertEqual(rows["ambiental.alert_window_months"]["origin"], ORIGIN_DEFAULT)

    def test_update_and_restore(self):
        key = "ambiental.require_document"
        response = self.client.put(self.url("detail", pk=key), data=json.dumps({"value": "sí"}), content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["value"], "true")
        self.assertTrue(get_parameter(self.child, key))

        response = self.client.post(self.url("restore", pk=key), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SystemParameter.objects.filter(key=key).exists())

    def test_invalid_value_is_rejected(self):
        response = self.client.put(
            self.url("detail", pk="ambiental.alert_window_months"),
            data=json.dumps({"value": "doce"}), content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_unknown_key_is_404(self):
        response = self.client.put(self.url("detail", pk="no.existe"), data=json.dumps({"value": "1"}), content_type="application/json")
        self.assertEqual(response.status_code, 404)

    def test_role_without_permission_is_denied(self):
        user = make_role_user("analista", self.child, "Analista ambiental")
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url("list")).status_code, 403)

    def test_page_renders_for_platform_admins(self):
        for username, rol_name in (("superior2", "Administrativo superior"), ("amb", "Administrador ambiental")):
            user = make_role_user(username, self.child, rol_name)
            self.client.force_login(user)
            with self.subTest(rol=rol_name):
                response = self.client.get(reverse("platform:systemparameter_list", kwargs={"org_pk": self.child.pk}))
                self.assertEqual(response.status_code, 200)
