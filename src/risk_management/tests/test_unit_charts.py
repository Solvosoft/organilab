from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from laboratory.models import Catalog, Laboratory, Object, OrganizationStructure, ShelfObject
from risk_management.models import RiskZone, ZoneType
from sga.models import SubstanceCharacteristics

# Sin esta cabecera HandleErrorMiddleware convierte 403/404 en una redirección.
AJAX = {"X-Requested-With": "XMLHttpRequest"}


class UnitGroupedChartTest(TestCase):
    """Los gráficos por categoría suman por unidad base, sin unidades fijas en código."""

    fixtures = ["laboratory_data.json"]

    def setUp(self):
        self.lab = Laboratory.objects.get(pk=1)
        self.org = self.lab.organization
        self.organ = Catalog.objects.create(key="white_organ", description="Hígado")
        obj = Object.objects.get(pk=1)
        substance = SubstanceCharacteristics.objects.get(pk=1)
        substance.object_related = obj
        substance.save()
        substance.white_organ.add(self.organ)

        self.gram = Catalog.objects.get(description="Gramos", key="units")
        self.ml = Catalog.objects.get(description="Mililitros", key="units")
        self.kg = Catalog.objects.get(description="Kilogramos", key="units")
        ShelfObject.objects.filter(object=obj).exclude(in_where_laboratory=self.lab).delete()
        first, second = ShelfObject.objects.filter(object=obj, in_where_laboratory=self.lab).order_by("pk")[:2]
        for shelfobject, quantity, unit in ((first, 500, self.gram), (second, 2000, self.ml)):
            shelfobject.quantity = quantity
            shelfobject.measurement_unit = unit
            shelfobject.save()
        ShelfObject.objects.filter(object=obj, in_where_laboratory=self.lab).exclude(pk__in=[first.pk, second.pk]).delete()

        # Un usuario con perfil: ImpostorMiddleware responde 404 si no lo tiene.
        self.user = User.objects.get(username="admin")
        User.objects.filter(pk=self.user.pk).update(is_superuser=True)
        self.client.force_login(self.user)
        self.url = reverse("whiteorganchart-detail", kwargs={"pk": self.org.pk})

    def get_chart(self, **params):
        response = self.client.get(self.url, data=params, headers=AJAX)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def series(self, chart):
        return {dataset["label"]: dataset["data"] for dataset in chart["data"]["datasets"]}

    def test_one_series_per_base_unit(self):
        chart = self.get_chart()
        self.assertEqual(chart["data"]["labels"], ["Hígado"])
        self.assertEqual(self.series(chart), {"Kilogramos": [0.5], "Litros": [2.0]})

    def test_unit_filter_keeps_one_series(self):
        chart = self.get_chart(unit=self.kg.pk)
        self.assertEqual(self.series(chart), {"Kilogramos": [0.5]})

    def test_invalid_unit_falls_back_to_all_units(self):
        chart = self.get_chart(unit="abc")
        self.assertEqual(set(self.series(chart)), {"Kilogramos", "Litros"})

    def test_risk_zone_of_other_organization_is_ignored(self):
        other_org = OrganizationStructure.objects.exclude(pk=self.org.pk).first()
        zone = RiskZone.objects.create(name="Ajena", organization=other_org, num_workers=1, zone_type=ZoneType.objects.create(name="Tipo"))
        chart = self.get_chart(risk_zone=zone.pk)
        self.assertEqual(set(self.series(chart)), {"Kilogramos", "Litros"})

    def test_requires_permission(self):
        User.objects.filter(pk=self.user.pk).update(is_superuser=False)
        self.client.force_login(User.objects.exclude(profile__isnull=True).exclude(pk=self.user.pk).first())
        self.assertEqual(self.client.get(self.url, headers=AJAX).status_code, 403)
