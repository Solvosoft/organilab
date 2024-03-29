# Generated by Django 4.1.9 on 2023-06-21 18:25
from decimal import Decimal

from django.db import migrations


def load_base_unit_data(apps, schema_editor):
    Catalog = apps.get_model('laboratory', 'Catalog')
    BaseUnitValues = apps.get_model('laboratory', 'BaseUnitValues')
    list_base_unit = [
        (Catalog.objects.get(description='Metros', key='units'), 1),
        (Catalog.objects.get(description='Milímetros', key='units'), 1000),
        (Catalog.objects.get(description='Centímetros', key='units'), 100),
        (Catalog.objects.get(description='Litros', key='units'), 1),
        (Catalog.objects.get(description='Mililitros', key='units'), 1000),
        (Catalog.objects.get(description='Unidades', key='units'), 1),
        (Catalog.objects.get(description='Gramos', key='units'), 1000),
        (Catalog.objects.get(description='Kilogramos', key='units'), 1),
        (Catalog.objects.get(description='Miligramos', key='units'), 1000000),
        (Catalog.objects.get(description='Metro cúbico', key='units'), 0.001),
        (Catalog.objects.get(description='Atmósfera', key='units'), 0.00000986923),
        (Catalog.objects.get(description='Pascales', key='units'), 1),
        (Catalog.objects.get(description='PSI', key='units'), 0.0001450377),
    ]
    base_unit_obj = []
    for key, value in list_base_unit:
        base_unit_obj.append(BaseUnitValues(measurement_unit=key, si_value=value))
    BaseUnitValues.objects.bulk_create(base_unit_obj, ignore_conflicts=True)


def change_shelf_object(apps, schema_editor):
    ShelfObject = apps.get_model('laboratory', 'ShelfObject')
    mydata = ShelfObject.objects.all()
    BaseUnitValues = apps.get_model('laboratory', 'BaseUnitValues')
    for element in mydata:
        if element.quantity:
            base_unit = BaseUnitValues.objects.get(
                measurement_unit=element.measurement_unit)
            quantity = Decimal(str(element.quantity))
            base_unit_value = Decimal(str(base_unit.si_value))
            result = float(quantity / base_unit_value)
            element.quantity_base_unit = result
            element.save()


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0121_alter_shelfobject_quantity_base_unit'),
    ]

    operations = [
        migrations.RunPython(load_base_unit_data,
                             reverse_code=migrations.RunPython.noop),
        migrations.RunPython(change_shelf_object,
                             reverse_code=migrations.RunPython.noop),
    ]
