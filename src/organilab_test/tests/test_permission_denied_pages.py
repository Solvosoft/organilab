from itertools import combinations
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from auth_and_perms.models import Profile
from laboratory.models import Laboratory, OrganizationStructure, UserOrganization

ROUTES = (
    "academic:procedure_step",
    "laboratory:profile",
    "laboratory:profile_detail",
    "laboratory:password_change",
    "laboratory:protocol_list",
    "laboratory:protocol_create",
    "laboratory:protocol_update",
    "laboratory:protocol_delete",
    "laboratory:object_reservation",
    "laboratory:disposal_substance",
    "laboratory:objectview_create",
    "laboratory:objectview_update",
    "laboratory:objectview_delete",
    "laboratory:trash_list",
    "reservations_management:validate_reservation",
    "reservations_management:increase_stock",
    "riskmanagement:incident_list",
    "riskmanagement:incident_create",
    "riskmanagement:incident_update",
    "riskmanagement:incident_delete",
    "riskmanagement:incident_detail",
    "riskmanagement:incident_report",
)
KWARGS = ("org_pk", "lab_pk", "pk", "building_pk", "risk_pk", "modelpk")


def build_url(name, values):
    for size in range(len(KWARGS) + 1):
        for keys in combinations(KWARGS, size):
            try:
                return reverse(name, kwargs={key: values.get(key, 1) for key in keys})
            except NoReverseMatch:
                continue
    raise NoReverseMatch(name)


class PermissionDeniedPagesTest(TestCase):
    """Sin permiso, el usuario con sesión ve la página de error y el anónimo va al login."""

    fixtures = ["laboratory_data.json"]

    @classmethod
    def setUpTestData(cls):
        organization = OrganizationStructure.objects.first()
        laboratory = Laboratory.objects.first()
        cls.user = User.objects.create_user("sin_permisos", password="x")
        Profile.objects.create(user=cls.user)
        UserOrganization.objects.create(
            user=cls.user, organization=organization,
            type_in_organization=UserOrganization.LABORATORY_USER, status=True,
        )
        values = {"org_pk": organization.pk, "lab_pk": laboratory.pk}
        cls.urls = {name: build_url(name, values) for name in ROUTES}

    def test_usuario_con_sesion_sin_permiso_no_va_al_login(self):
        self.client.force_login(self.user)
        error_path = reverse("error_view")
        for name, url in self.urls.items():
            with self.subTest(ruta=name):
                response = self.client.get(url)
                location = urlparse(response.get("Location", ""))
                self.assertEqual(response.status_code, 302)
                self.assertEqual(location.path, error_path)
                self.assertEqual(location.query, "status=403")

    def test_usuario_anonimo_va_al_login(self):
        for name, url in self.urls.items():
            with self.subTest(ruta=name):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(urlparse(response["Location"]).path, settings.LOGIN_URL)
