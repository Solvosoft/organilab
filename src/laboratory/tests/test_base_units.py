import importlib

from django.apps import apps
from django.db.models.signals import pre_save
from django.test import TestCase

from laboratory.models import ShelfObject, Catalog, Object
from laboratory.utils_base_unit import get_conversion_units


class BaseUnitTest(TestCase):
    fixtures = ["base_units.json"]

    def test_millimeter_to_meter(self):
        mm = Catalog.objects.get(description='Milímetros', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(quantity=20, measurement_unit=mm, object=obj, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 0.02)

    def test_centimeter_to_meter(self):
        cm = Catalog.objects.get(description='Centímetros', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=20, measurement_unit=cm, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 0.2)

    def test_meter(self):
        m = Catalog.objects.get(description='Metros', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=20, measurement_unit=m, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 20)

    def test_milliliter_to_liter(self):
        ml = Catalog.objects.get(description='Milímetros', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=20, measurement_unit=ml, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 0.02)

    def test_cubic_meter_to_liter(self):
        m3 = Catalog.objects.get(description='Metro cúbico', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=20, measurement_unit=m3, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 20)

    def test_liter(self):
        liter = Catalog.objects.get(description='Litros', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=20, measurement_unit=liter, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 20)

    def test_units(self):
        units = Catalog.objects.get(description='Unidades', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=20, measurement_unit=units, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 20)

    def test_gram_to_kilogram(self):
        gram = Catalog.objects.get(description='Gramos', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=20, measurement_unit=gram, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 0.02)

    def test_milligram_to_kilogram(self):
        mg = Catalog.objects.get(description='Miligramos', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=20, measurement_unit=mg, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 0.00002)

    def test_units(self):
        units = Catalog.objects.get(description='Unidades', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=20, measurement_unit=units, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 20)

    def test_psi_to_pascal(self):
        psi = Catalog.objects.get(description='PSI', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=20, measurement_unit=psi, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 20)

    def test_atm_to_pascal(self):
        pascal = Catalog.objects.get(description='Pascales', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=20, measurement_unit=pascal, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 20)

    def test_pascals(self):
        atm = Catalog.objects.get(description='Atmósfera', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=20, measurement_unit=atm, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 2026500.547661773)

    def test_low_quantity(self):
        ml = Catalog.objects.get(description='Miligramos', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=0.10, measurement_unit=ml, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 1.0000000000000001e-07)

    def test_negative_quantity(self):
        ml = Catalog.objects.get(description='Miligramos', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=-0.10, measurement_unit=ml, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, -1.0000000000000001e-07)

    def test_unsupported_catalog(self):
        new_catalog = Catalog.objects.create(key='units', description='New Catalog')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=-0.10, measurement_unit=new_catalog, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        # Sin factor de conversión, la cantidad se guarda tal cual.
        self.assertEqual(inst.quantity_base_unit, -0.10)

    def test_converts_with_default_value(self):
        # El campo vale 0 por defecto: antes se copiaba la cantidad sin convertir.
        gram = Catalog.objects.get(description='Gramos', key='units')
        inst = ShelfObject(object=Object.objects.get(pk=1), quantity=20, measurement_unit=gram)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 0.02)

    def test_reconverts_when_quantity_changes(self):
        gram = Catalog.objects.get(description='Gramos', key='units')
        inst = ShelfObject(object=Object.objects.get(pk=1), quantity=20, measurement_unit=gram)
        pre_save.send(sender=ShelfObject, instance=inst)
        inst.quantity = 500
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 0.5)


class RecomputeQuantityBaseUnitMigrationTest(TestCase):
    fixtures = ["laboratory_data.json"]

    def test_backfill_converts_stored_values(self):
        recompute = importlib.import_module("laboratory.migrations.0224_recompute_quantity_base_unit").recompute
        for shelfobject in ShelfObject.objects.all():
            ShelfObject.objects.filter(pk=shelfobject.pk).update(quantity_base_unit=shelfobject.quantity)
        recompute(apps, None)
        for shelfobject in ShelfObject.objects.all():
            expected = get_conversion_units(shelfobject.measurement_unit, shelfobject.quantity)
            if expected is None:
                expected = shelfobject.quantity
            self.assertAlmostEqual(shelfobject.quantity_base_unit, expected, msg=shelfobject.pk)
