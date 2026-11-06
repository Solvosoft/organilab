"""Escenario multi-inquilino armado en código para las pruebas de `auth_and_perms`.

Dos organizaciones raíz que no se conocen (A, con una hija, y B), un laboratorio en cada
una y una fábrica de usuarios cuyos permisos salen de un `Rol` asignado por
`ProfilePermission`, igual que en producción: `ProfileMiddleware` arma los permisos
efectivos desde los roles, no desde `user.user_permissions`.
"""

from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from auth_and_perms.models import Profile, ProfilePermission, Rol
from laboratory.models import Laboratory, OrganizationStructure, UserOrganization


def permisos(*codenames):
    """`"app.codename"` → instancias de `Permission`."""
    resultado = []
    for perm in codenames:
        app_label, codename = perm.split(".")
        resultado.append(
            Permission.objects.get(content_type__app_label=app_label, codename=codename)
        )
    return resultado


class EscenarioOrganizaciones(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ct_org = ContentType.objects.get_for_model(OrganizationStructure)
        cls.ct_lab = ContentType.objects.get_for_model(Laboratory)
        cls.ct_profile = ContentType.objects.get_for_model(Profile)

        cls.org_a = OrganizationStructure.objects.create(name="Organización A")
        cls.org_a_hija = OrganizationStructure.objects.create(
            name="Organización A hija", parent=cls.org_a, level=1
        )
        cls.org_b = OrganizationStructure.objects.create(name="Organización B")

        cls.lab_a = Laboratory.objects.create(name="Laboratorio A", organization=cls.org_a)
        cls.lab_a_hija = Laboratory.objects.create(
            name="Laboratorio A hija", organization=cls.org_a_hija
        )
        cls.lab_b = Laboratory.objects.create(name="Laboratorio B", organization=cls.org_b)

    @classmethod
    def crear_usuario(
        cls,
        username,
        org=None,
        perms=(),
        ambito="organizacion",
        type_in_organization=UserOrganization.ADMINISTRATOR,
        rol_name=None,
        **user_kwargs,
    ):
        """Usuario con perfil, miembro de `org` y con un rol que trae `perms`.

        `ambito="organizacion"` asigna el rol sobre la organización (cuenta cuando la URL
        trae `org_pk`); `ambito="perfil"` lo asigna sobre el propio perfil, que es la rama
        que `ProfileMiddleware` aplica en cualquier URL, también en las que no llevan
        organización.
        """
        user = User.objects.create_user(
            username, email=f"{username}@ejemplo.cr", password="clave-segura-123", **user_kwargs
        )
        profile = Profile.objects.create(user=user)
        if org is not None:
            UserOrganization.objects.create(
                user=user, organization=org, type_in_organization=type_in_organization
            )
        if perms:
            rol = Rol.objects.create(name=rol_name or f"Rol de {username}")
            rol.permissions.add(*permisos(*perms))
            if org is not None:
                org.root.rol.add(rol)
            if ambito == "perfil":
                pp = ProfilePermission.objects.create(
                    profile=profile, content_type=cls.ct_profile, object_id=profile.pk
                )
            else:
                pp = ProfilePermission.objects.create(
                    profile=profile,
                    content_type=cls.ct_org,
                    object_id=org.pk,
                    organization=org,
                )
            pp.rol.add(rol)
        return user

    def assertNegado(self, response, status_code=403):
        """403/404 directo (JSON/XHR) o la redirección de `HandleErrorMiddleware`."""
        if response.status_code == 302:
            self.assertIn(reverse("error_view"), response.url)
            self.assertIn("status=%d" % status_code, response.url)
        else:
            self.assertEqual(response.status_code, status_code)
