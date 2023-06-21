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
        m = Catalog.objects.get(description='Litros', key='units')
        inst = ShelfObject(quantity=20, measurement_unit=m)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 20)

