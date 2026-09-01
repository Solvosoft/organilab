# -*- coding: utf-8 -*-
"""Unidades no convertibles: deben rechazarse, no reventar la vista.

`get_related_units` y `get_conversion_from_two_units` devuelven None cuando la
unidad no tiene unidad base, es decir, cuando no es convertible. Sus llamadores
daban por hecho un valor utilizable y producían un 500:

- `increase_unit not in None`  -> TypeError: argument of type 'NoneType'...
- `None * units_per_box`       -> TypeError: unsupported operand type(s) for *
"""
from django.test import TestCase

from laboratory.models import Catalog
from laboratory.utils_base_unit import (
    get_conversion_from_two_units,
    get_related_units,
)


class IncompatibleUnitsTest(TestCase):
    fixtures = ["base_units.json"]

    def setUp(self):
        self.meters = Catalog.objects.get(description="Metros", key="units")
        # Unidad recién creada: no tiene BaseUnitValues, así que no es
        # convertible con ninguna otra.
        self.orphan_unit = Catalog.objects.create(
            key="units", description="Unidad sin base"
        )

    def test_related_units_returns_none_for_unit_without_base(self):
        queryset = Catalog.objects.filter(key="units")
        self.assertIsNone(get_related_units(self.orphan_unit, queryset))

    def test_related_units_returns_queryset_for_known_unit(self):
        queryset = Catalog.objects.filter(key="units")
        related = get_related_units(self.meters, queryset)
        self.assertIsNotNone(related)
        self.assertIn(self.meters, related)

    def test_conversion_returns_none_between_incompatible_units(self):
        self.assertIsNone(
            get_conversion_from_two_units(self.orphan_unit, self.meters, 10)
        )

    def test_conversion_works_between_compatible_units(self):
        centimeters = Catalog.objects.get(description="Centímetros", key="units")
        self.assertIsNotNone(
            get_conversion_from_two_units(centimeters, self.meters, 10)
        )
