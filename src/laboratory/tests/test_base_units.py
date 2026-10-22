from django.db.models.signals import pre_save
from django.test import TestCase

from laboratory.models import BaseUnitValues, Catalog, Object, ShelfObject


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
        ml = Catalog.objects.get(description='Mililitros', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=20, measurement_unit=ml, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 0.02)

    def test_cubic_meter_to_liter(self):
        m3 = Catalog.objects.get(description='Metro cúbico', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=20, measurement_unit=m3, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertAlmostEqual(inst.quantity_base_unit, 20000)

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

    def test_psi_to_pascal(self):
        psi = Catalog.objects.get(description='PSI', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=20, measurement_unit=psi, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertAlmostEqual(inst.quantity_base_unit, 137895.18, places=2)

    def test_pascal(self):
        pascal = Catalog.objects.get(description='Pascales', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=20, measurement_unit=pascal, quantity_base_unit=None)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 20)

    def test_atm_to_pascal(self):
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
        # Sin unidad base conocida se guarda la cantidad tal cual: el campo no admite nulos.
        self.assertEqual(inst.quantity_base_unit, -0.10)

    def test_converts_with_field_default(self):
        """Regresión: el default del campo es 0, no None, y aun así debe convertir."""
        ml = Catalog.objects.get(description='Mililitros', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=500, measurement_unit=ml)
        self.assertEqual(inst.quantity_base_unit, 0)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 0.5)

    def test_recalculates_on_every_save(self):
        """Un segundo guardado no debe reemplazar el valor convertido por la cantidad cruda."""
        gram = Catalog.objects.get(description='Gramos', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=500, measurement_unit=gram)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 0.5)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 0.5)
        inst.quantity = 250
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 0.25)

    def test_unit_change_recalculates(self):
        gram = Catalog.objects.get(description='Gramos', key='units')
        kg = Catalog.objects.get(description='Kilogramos', key='units')
        obj = Object.objects.get(pk=1)
        inst = ShelfObject(object=obj, quantity=2, measurement_unit=kg)
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 2)
        inst.quantity, inst.measurement_unit = 2000, gram
        pre_save.send(sender=ShelfObject, instance=inst)
        self.assertEqual(inst.quantity_base_unit, 2)


class RecalculateQuantityBaseUnitMigrationTest(TestCase):
    """La migración 0224 corrige las existencias guardadas con la cantidad cruda."""

    fixtures = ["laboratory_data.json"]

    def test_recalculates_raw_values(self):
        from importlib import import_module

        from django.apps import apps

        from laboratory.utils_base_unit import get_conversion_units

        migration = import_module("laboratory.migrations.0224_recalculate_quantity_base_unit")
        rows = list(ShelfObject.objects.all())
        self.assertTrue(rows)
        # Así quedaron en producción: quantity_base_unit = quantity sin convertir.
        for row in rows:
            ShelfObject.objects.filter(pk=row.pk).update(quantity_base_unit=row.quantity)

        migration.recalculate(apps, None)
        migration.recalculate(apps, None)  # idempotente

        for row in ShelfObject.objects.all():
            expected = get_conversion_units(row.measurement_unit, row.quantity)
            if expected is None:
                expected = row.quantity
            self.assertAlmostEqual(row.quantity_base_unit, expected)


class QuantityBaseUnitImpactCommandTest(TestCase):
    """El comando mide el cambio sin escribir en la base."""

    fixtures = ["laboratory_data.json"]

    def test_reporta_y_no_modifica(self):
        from io import StringIO

        from django.core.management import call_command

        from laboratory.tests.test_cov_core_tasks import asegurar_unidades_base

        asegurar_unidades_base()
        shelf_object = ShelfObject.objects.filter(object__type=Object.REACTIVE).first()
        ShelfObject.objects.filter(pk=shelf_object.pk).update(
            measurement_unit_id=63, quantity=500, quantity_base_unit=500
        )
        antes = list(ShelfObject.objects.order_by("pk").values_list("pk", "quantity_base_unit"))

        out = StringIO()
        call_command("report_quantity_base_unit_impact", stdout=out)
        salida = out.getvalue()

        self.assertIn("Existencias cuyo quantity_base_unit cambia", salida)
        self.assertNotIn("  ninguna", salida.split("\n\n")[0])
        self.assertIn("Toneladas por organización", salida)
        self.assertEqual(
            antes, list(ShelfObject.objects.order_by("pk").values_list("pk", "quantity_base_unit"))
        )

    def test_sin_diferencias(self):
        from io import StringIO

        from django.core.management import call_command

        for row in ShelfObject.objects.all():
            row.save()
        out = StringIO()
        call_command("report_quantity_base_unit_impact", stdout=out)
        self.assertIn("  ninguna", out.getvalue())


class FixBaseUnitsMigrationTest(TestCase):
    """La migración 0227 lleva PSI, Metro cúbico y Libra a la base de su familia."""

    fixtures = ["laboratory_data.json"]

    def setUp(self):
        from importlib import import_module

        self.migration = import_module("laboratory.migrations.0227_fix_base_unit_psi_cubic_meter_pound")
        self.libra, _ = Catalog.objects.get_or_create(key="units", description="Libra")
        BaseUnitValues.objects.update_or_create(
            measurement_unit=self.libra, defaults={"measurement_unit_base": self.libra, "si_value": 1}
        )
        for description in ("PSI", "Metro cúbico"):
            unit = Catalog.objects.get(key="units", description=description)
            BaseUnitValues.objects.filter(measurement_unit=unit).update(measurement_unit_base=unit)
        self.m3 = Catalog.objects.get(key="units", description="Metro cúbico")
        obj = Object.objects.get(pk=1)
        shelf = ShelfObject.objects.first().shelf
        self.en_libras = ShelfObject.objects.create(object=obj, shelf=shelf, quantity=10, measurement_unit=self.libra)
        self.en_m3 = ShelfObject.objects.create(object=obj, shelf=shelf, quantity=2, measurement_unit=self.m3)
        ShelfObject.objects.filter(pk__in=[self.en_libras.pk, self.en_m3.pk]).update(quantity_base_unit=0)

    def base(self, description):
        unit = Catalog.objects.get(key="units", description=description)
        values = BaseUnitValues.objects.get(measurement_unit=unit)
        return values.measurement_unit_base.description, values.si_value

    def test_corrige_las_bases_y_recalcula_las_existencias(self):
        from django.apps import apps

        self.migration.fix_base_units(apps, None)

        self.assertEqual(self.base("PSI"), ("Pascales", 0.0001450377))
        self.assertEqual(self.base("Metro cúbico"), ("Litros", 0.001))
        self.assertEqual(self.base("Libra"), ("Kilogramos", 2.20462))
        self.en_libras.refresh_from_db()
        self.en_m3.refresh_from_db()
        self.assertAlmostEqual(self.en_libras.quantity_base_unit, 4.5359, places=4)
        self.assertAlmostEqual(self.en_m3.quantity_base_unit, 2000)

    def test_revertir_deja_la_configuracion_anterior(self):
        from django.apps import apps

        self.migration.fix_base_units(apps, None)
        self.migration.restore_base_units(apps, None)

        self.assertEqual(self.base("PSI"), ("PSI", 0.0001450377))
        self.assertEqual(self.base("Metro cúbico"), ("Metro cúbico", 0.001))
        self.assertEqual(self.base("Libra"), ("Libra", 1))
        self.en_libras.refresh_from_db()
        self.assertEqual(self.en_libras.quantity_base_unit, 10)
