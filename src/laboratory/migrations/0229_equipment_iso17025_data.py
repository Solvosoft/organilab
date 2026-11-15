from django.db import migrations

CATALOGS = {
    "equipment_magnitude": [
        "Masa", "Volumen", "Temperatura", "pH", "Tiempo", "Longitud", "Presión",
        "Humedad", "Conductividad", "Absorbancia", "Velocidad de rotación",
    ],
    # Actividades del formato PT-05 R-10.
    "maintenance_activity": [
        "Inspección visual", "Limpieza", "Cambio de batería", "Pintura", "Engrasado",
    ],
    "equipment_document_type": [
        "Manual de fabricante", "Instructivo interno de uso", "Procedimiento asociado",
        "Certificado", "Informe de mantenimiento o reparación", "Documento técnico",
    ],
}


def seed_catalogs(apps, schema_editor):
    Catalog = apps.get_model("laboratory", "Catalog")
    for key, descriptions in CATALOGS.items():
        for description in descriptions:
            Catalog.objects.get_or_create(key=key, description=description)


def copy_identification(apps, schema_editor):
    """Modelo, serie y placa vivían en el catálogo (``Object``); ahora son de cada unidad."""
    Characteristics = apps.get_model("laboratory", "ShelfObjectEquipmentCharacteristics")
    for ch in Characteristics.objects.select_related("shelfobject__object").iterator():
        obj = ch.shelfobject.object
        changed = []
        for target, source in (("model", "model"), ("serial_number", "serie"), ("asset_number", "plaque")):
            value = (getattr(obj, source, "") or "").strip()
            if value and not getattr(ch, target):
                setattr(ch, target, value[:100])
                changed.append(target)
        if changed:
            ch.save(update_fields=changed)


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0228_equipment_iso17025"),
    ]

    operations = [
        migrations.RunPython(seed_catalogs, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(copy_identification, reverse_code=migrations.RunPython.noop),
    ]
