"""Permisos por organización de ``api/utils.py``.

``PermissionBase`` se prueba compuesto **delante** del permiso de djgentelella: es
la composición que hace efectiva la verificación de organización. Las clases
``AllPermissionOrganization*`` lo heredan detrás de ``AllPermission``, de modo que
su ``has_permission`` nunca corre (ver el informe de cobertura).
"""

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from djgentelella.permission_management import AllPermission
from rest_framework.request import Request

from api.utils import (
    AllPermissionOrganization,
    AllPermissionOrganizationByAction,
    PermissionBase,
)
from laboratory.models import OrganizationStructure, UserOrganization


class PermisoConOrganizacion(PermissionBase, AllPermission):
    def __init__(self, perms, lookup_keyword="org_pk", as_param_method=None):
        self.lookup_keyword = lookup_keyword
        self.as_param_method = as_param_method
        super().__init__(perms)


class VistaFalsa:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class PermissionBaseTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = OrganizationStructure.objects.create(name="Propia")
        cls.other = OrganizationStructure.objects.create(name="Ajena")
        cls.user = User.objects.create_superuser("permisos_api", password="x")
        UserOrganization.objects.create(
            user=cls.user, organization=cls.organization, type_in_organization=1, status=True
        )

    def peticion(self, metodo="get", data=None, **headers):
        factory = RequestFactory()
        if metodo == "get":
            django_request = factory.get("/", data or {}, headers=headers)
        else:
            django_request = factory.post(
                "/", data or {}, content_type="application/json", headers=headers
            )
        django_request.user = self.user
        request = Request(django_request)
        # Sin authenticators DRF resolvería AnonymousUser; el setter fija ambos.
        request.user = self.user
        request._full_data = data or {}
        return request

    def test_sin_organizacion_niega(self):
        permiso = PermisoConOrganizacion([])
        self.assertFalse(permiso.has_permission(self.peticion(), VistaFalsa()))

    def test_organizacion_en_kwargs_de_la_vista(self):
        permiso = PermisoConOrganizacion(["laboratory.view_laboratory"])
        self.assertTrue(
            permiso.has_permission(self.peticion(), VistaFalsa(org_pk=self.organization.pk))
        )

    def test_organizacion_ajena_niega(self):
        permiso = PermisoConOrganizacion(["laboratory.view_laboratory"])
        self.assertFalse(
            permiso.has_permission(self.peticion(), VistaFalsa(org_pk=self.other.pk))
        )

    def test_organizacion_inexistente_niega(self):
        permiso = PermisoConOrganizacion(["laboratory.view_laboratory"])
        self.assertFalse(permiso.has_permission(self.peticion(), VistaFalsa(org_pk=999999)))

    def test_organizacion_en_el_cuerpo_y_en_cabeceras(self):
        permiso = PermisoConOrganizacion(["laboratory.view_laboratory"], lookup_keyword="org")
        en_cuerpo = self.peticion("post", {"org": self.organization.pk})
        self.assertTrue(permiso.has_permission(en_cuerpo, VistaFalsa()))
        en_cabecera = self.peticion(org=str(self.other.pk))
        self.assertFalse(permiso.has_permission(en_cabecera, VistaFalsa()))

    def test_organizacion_como_parametro_get(self):
        permiso = PermisoConOrganizacion(
            ["laboratory.view_laboratory"], lookup_keyword="organization", as_param_method="GET"
        )
        request = self.peticion(data={"organization": self.organization.pk})
        self.assertTrue(permiso.has_permission(request, VistaFalsa()))

    def test_las_instancias_se_devuelven_a_si_mismas_al_llamarlas(self):
        permiso = AllPermissionOrganization(["x.y"], lookup_keyword="organization")
        por_accion = AllPermissionOrganizationByAction(lookup_keyword="organization")
        self.assertIs(permiso(), permiso)
        self.assertIs(por_accion(), por_accion)
        self.assertEqual(por_accion.lookup_keyword, "organization")
