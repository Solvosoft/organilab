from django.db.models.signals import pre_save
from django.test import TestCase

from laboratory.models import ShelfObject, Catalog


class BaseUnitTest(TestCase):

    def test_millimeter_to_meter(self):
        mm = Catalog.objects.get(description='Milímetros', key='units')
        inst = ShelfObject(quantity=20, measurement_unit=mm)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 0.02)

    def test_centimeter_to_meter(self):
        cm = Catalog.objects.get(description='Centímetros', key='units')
        inst = ShelfObject(quantity=20, measurement_unit=cm)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 0.2)

    def test_meter(self):
        m = Catalog.objects.get(description='Metros', key='units')
        inst = ShelfObject(quantity=20, measurement_unit=m)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 20)

    def test_milliliter_to_liter(self):
        ml = Catalog.objects.get(description='Milímetros', key='units')
        inst = ShelfObject(quantity=20, measurement_unit=ml)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 0.02)

    def test_cubic_meter_to_liter(self):
        m3 = Catalog.objects.get(description='Metro cúbico', key='units')
        inst = ShelfObject(quantity=20, measurement_unit=m3)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 20000)

    def test_liter(self):
        liter = Catalog.objects.get(description='Litros', key='units')
        inst = ShelfObject(quantity=20, measurement_unit=liter)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 20)

    def test_units(self):
        units = Catalog.objects.get(description='Unidades', key='units')
        inst = ShelfObject(quantity=20, measurement_unit=units)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 20)

    def test_gram_to_kilogram(self):
        gram = Catalog.objects.get(description='Gramos', key='units')
        inst = ShelfObject(quantity=20, measurement_unit=gram)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 0.02)

    def test_milligram_to_kilogram(self):
        mg = Catalog.objects.get(description='Miligramos', key='units')
        inst = ShelfObject(quantity=20, measurement_unit=mg)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 0.00002)

    def test_units(self):
        units = Catalog.objects.get(description='Kilogramos', key='units')
        inst = ShelfObject(quantity=20, measurement_unit=units)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 20)

    def test_atm_to_pascal(self):
        atm = Catalog.objects.get(description='Atmósfera', key='units')
        inst = ShelfObject(quantity=20, measurement_unit=atm)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 2026500.547661773)

    def test_psi_to_pascal(self):
        psi = Catalog.objects.get(description='PSI', key='units')
        inst = ShelfObject(quantity=20, measurement_unit=psi)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 137895.1817355074)

    def test_pascals(self):
        pascal = Catalog.objects.get(description='Pascales', key='units')
        inst = ShelfObject(quantity=20, measurement_unit=pascal)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 20)

    def test_low_quantity(self):
        liter = Catalog.objects.get(description='Miligramos', key='units')
        inst = ShelfObject(quantity=0.1, measurement_unit=liter)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 1.0000000000000001e-07)
