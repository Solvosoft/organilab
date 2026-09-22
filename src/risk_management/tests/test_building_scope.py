from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from auth_and_perms.models import Profile
from laboratory.models import OrganizationStructure, UserOrganization
from risk_management.models import Buildings


class BuildingOrganizationScopeTest(TestCase):
    """Un edificio solo se alcanza desde su propia organización.

    Se usa un superusuario a propósito: lo que se prueba no es el permiso de modelo sino
    que el pk de otra organización no se cuele por la URL.
    """

    @classmethod
    def setUpTestData(cls):
        cls.organization = OrganizationStructure.objects.create(name="Propia")
        cls.other = OrganizationStructure.objects.create(name="Ajena")
        cls.user = User.objects.create_superuser("super_edificios", "s@example.com", "pass")
        Profile.objects.create(user=cls.user)
        UserOrganization.objects.create(user=cls.user, organization=cls.organization, type_in_organization=1, status=True)
        cls.own = Buildings.objects.create(name="Propio", phone="", organization=cls.organization)
        cls.foreign = Buildings.objects.create(name="Ajeno", phone="", organization=cls.other)

    def setUp(self):
        self.client.force_login(self.user)

    def get(self, name, **kwargs):
        return self.client.get(
            reverse("riskmanagement:" + name, kwargs=kwargs), HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

    def test_update_of_foreign_building_is_404(self):
        self.assertEqual(self.get("buildings_update", org_pk=self.organization.pk, pk=self.own.pk).status_code, 200)
        self.assertEqual(self.get("buildings_update", org_pk=self.organization.pk, pk=self.foreign.pk).status_code, 404)

    def test_api_of_foreign_organization_is_denied(self):
        own = self.client.get(reverse("riskmanagement:api-building-list", kwargs={"org_pk": self.organization.pk}))
        self.assertEqual(own.status_code, 200)
        self.assertEqual(own.json()["recordsTotal"], 1)
        foreign = self.client.get(reverse("riskmanagement:api-building-list", kwargs={"org_pk": self.other.pk}))
        self.assertEqual(foreign.status_code, 403)

    def test_incident_with_foreign_building_is_404(self):
        response = self.get("incident_create", org_pk=self.organization.pk, building_pk=self.foreign.pk)
        self.assertEqual(response.status_code, 404)

    def test_building_select_of_foreign_organization_is_denied(self):
        response = self.client.get(reverse("risk_building-list"), {"org_pk": self.other.pk})
        self.assertEqual(response.status_code, 403)
