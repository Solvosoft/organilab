"""Ramas del módulo ambiental que no alcanza el uso normal de la API."""

from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

from ambiental.api.building_access import MANAGE_PERM, BuildingAccessViewSet
from ambiental.gtselects import AmbientalOrganizationSelect
from ambiental.tests.test_building_access import BuildingAccessTestCase
from risk_management.models import Buildings


class AlcancePorDefectoDelAutocompleteTest(BuildingAccessTestCase):
    def test_la_base_acota_por_organizacion(self):
        """Todas las subclases lo redefinen; el de la base es la red de seguridad para
        un autocomplete nuevo que olvide hacerlo."""
        view = AmbientalOrganizationSelect()
        visibles = view.scope_queryset(Buildings.objects.all(), self.organization)
        self.assertIn(self.building, visibles)
        self.assertNotIn(self.other_building, visibles)


class ComprobarEdificioTest(BuildingAccessTestCase):
    def test_sin_permiso_de_gestion_en_el_edificio_se_niega(self):
        """La API ya acota el queryset y las opciones del serializer a los edificios
        gestionables; `check_building` es la última comprobación antes de escribir."""
        sin_roles = self.building_user("sin-roles", {})
        view = BuildingAccessViewSet()
        view.request = RequestFactory().get("/")
        view.request.user = sin_roles
        view.kwargs = {"org_pk": self.organization.pk}
        view.format_kwarg = None
        with self.assertRaises(PermissionDenied):
            view.check_building(MANAGE_PERM, self.building)
