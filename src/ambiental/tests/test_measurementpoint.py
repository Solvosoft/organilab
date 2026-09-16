from django.urls import reverse
from djgentelella.models import Trash

from ambiental.ambiental_defaults import (
    KEY_ALERT_LEVEL,
    KEY_MEASURE_UNIT,
    KEY_NORMALIZER,
    KEY_POINT_TYPE,
    KEY_RESOURCE_TYPE,
    KEY_WASTE_TREATMENT,
    get_catalog_seed,
    seed_ambiental,
)
from ambiental.models import MeasurementPoint
from ambiental.tests.base import AmbientalTestCase
from laboratory.models import Catalog


class AmbientalCatalogSeedTest(AmbientalTestCase):
    """La migración 0002 siembra los catálogos y el comando es idempotente."""

    def test_catalogs_are_seeded(self):
        expected = {
            KEY_RESOURCE_TYPE: 8,
            KEY_MEASURE_UNIT: 6,
            KEY_POINT_TYPE: 4,
            KEY_NORMALIZER: 2,
            KEY_WASTE_TREATMENT: 5,
            KEY_ALERT_LEVEL: 3,
        }
        for key, count in expected.items():
            with self.subTest(key=key):
                self.assertEqual(Catalog.objects.filter(key=key).count(), count)

    def test_seed_is_idempotent(self):
        before = Catalog.objects.count()
        seed_ambiental(Catalog)
        self.assertEqual(Catalog.objects.count(), before)
        self.assertEqual(
            len(get_catalog_seed()), len(set(get_catalog_seed()))
        )


class MeasurementPointViewTest(AmbientalTestCase):

    def test_list_page_renders(self):
        response = self.client.get(
            reverse("ambiental:measurementpoint_list", kwargs={"org_pk": self.organization.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "table-measurementpoint")

    def test_list_page_renders_for_every_ambiental_role(self):
        for rol_name in ("Encargado de registro ambiental", "Analista ambiental"):
            with self.subTest(rol=rol_name):
                user = self.make_user(rol_name.replace(" ", "_"), self.organization, rol_name)
                self.client.force_login(user)
                response = self.client.get(
                    reverse("ambiental:measurementpoint_list", kwargs={"org_pk": self.organization.pk})
                )
                self.assertEqual(response.status_code, 200)

    def test_list_page_requires_permission(self):
        user = self.make_user("sin_permiso", self.organization, "Analista ambiental")
        rol = user.profile.profilepermission_set.first().rol.first()
        rol.permissions.clear()
        self.client.force_login(user)
        response = self.client.get(
            reverse("ambiental:measurementpoint_list", kwargs={"org_pk": self.organization.pk}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 403)


class MeasurementPointAPITest(AmbientalTestCase):

    def list_url(self, organization=None):
        return reverse(
            "ambiental:api-measurementpoint-list",
            kwargs={"org_pk": (organization or self.organization).pk},
        )

    def detail_url(self, point, organization=None):
        return reverse(
            "ambiental:api-measurementpoint-detail",
            kwargs={"org_pk": (organization or self.organization).pk, "pk": point.pk},
        )

    def payload(self, **kwargs):
        data = {
            "code": "AYA-123",
            "name": "Medidor de agua",
            "point_type": self.meter.pk,
            "resource_type": self.water.pk,
            "building": self.building.pk,
            "laboratories": [self.laboratory.pk],
            "meters_count": 1,
        }
        data.update(kwargs)
        return data

    def test_create_assigns_organization_and_logs(self):
        response = self.client.post(self.list_url(), data=self.payload(), content_type="application/json")
        self.assertEqual(response.status_code, 201, response.content)
        point = MeasurementPoint.objects.get(code="AYA-123")
        self.assertEqual(point.organization, self.organization)
        self.assertEqual(point.created_by, self.user)
        self.assertEqual(list(point.laboratories.all()), [self.laboratory])

    def test_list_only_returns_own_organization(self):
        own = self.make_point()
        self.make_point(organization=self.other_organization, building=self.other_building, code="X")
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["recordsTotal"], 1)
        self.assertEqual(data["data"][0]["id"], own.pk)
        self.assertEqual(data["data"][0]["building"]["text"], "Edificio A")

    def test_other_organization_is_forbidden(self):
        response = self.client.get(self.list_url(self.other_organization))
        self.assertIn(response.status_code, (403, 404))

    def test_building_of_other_organization_is_rejected(self):
        response = self.client.post(
            self.list_url(),
            data=self.payload(building=self.other_building.pk),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("building", response.json())

    def test_duplicated_code_is_rejected(self):
        self.make_point(code="AYA-123")
        response = self.client.post(self.list_url(), data=self.payload(), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("code", response.json())

    def test_same_code_for_other_resource_is_allowed(self):
        self.make_point(code="AYA-123")
        response = self.client.post(
            self.list_url(),
            data=self.payload(resource_type=self.electricity.pk),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)

    def test_update(self):
        point = self.make_point()
        response = self.client.put(
            self.detail_url(point),
            data=self.payload(code=point.code, name="Nuevo nombre"),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        point.refresh_from_db()
        self.assertEqual(point.name, "Nuevo nombre")

    def test_destroy_goes_to_the_organization_trash(self):
        point = self.make_point()
        response = self.client.delete(self.detail_url(point))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(MeasurementPoint.objects.filter(pk=point.pk).exists())
        self.assertTrue(MeasurementPoint.objects_with_deleted.filter(pk=point.pk).exists())
        trash = Trash.objects.get(object_id=point.pk, content_type__model="measurementpoint")
        self.assertEqual(trash.deleted_by, self.user)
        related = {(rel.content_type.model, rel.object_id) for rel in trash.gt_relations.all()}
        self.assertIn(("organizationstructure", self.organization.pk), related)
        self.assertIn(("buildings", self.building.pk), related)

    def test_deleted_code_asks_to_restore(self):
        point = self.make_point(code="AYA-123")
        point.delete(user=self.user)
        response = self.client.post(self.list_url(), data=self.payload(), content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_readonly_role_cannot_create(self):
        user = self.make_user("analista", self.organization, "Analista ambiental")
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.list_url()).status_code, 200)
        response = self.client.post(self.list_url(), data=self.payload(), content_type="application/json")
        self.assertEqual(response.status_code, 403)

    def test_select_of_buildings_is_scoped(self):
        # En la organización ajena el usuario no tiene rol: el middleware no le da el
        # permiso y el autocomplete responde 403 en vez de listar edificios ajenos.
        response = self.client.get(
            reverse("ambiental_buildings-list"), {"org_pk": self.other_organization.pk}
        )
        self.assertEqual(response.status_code, 403)
        response = self.client.get(
            reverse("ambiental_buildings-list"), {"org_pk": self.organization.pk}
        )
        self.assertEqual([row["text"] for row in response.json()["results"]], ["Edificio A"])
