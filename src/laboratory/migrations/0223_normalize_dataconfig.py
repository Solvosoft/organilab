from django.db import migrations

from laboratory import dataconfig


def normalize(apps, schema_editor):
    """Reescribe todos los ``Furniture.dataconfig`` en el formato canónico.

    La base de datos contiene tres formatos históricos (JSON de listas, celdas
    CSV ``"1,2"`` y el ``repr`` de Python con comillas simples).  El parser es
    tolerante con todos ellos, así que esta migración no es bloqueante: lo que
    quede sin convertir se sigue leyendo igual.  Idempotente.
    """
    Furniture = apps.get_model("laboratory", "Furniture")
    for pk, text in Furniture.objects.values_list("pk", "dataconfig").iterator():
        normalized = dataconfig.normalize(text)
        if normalized != text:
            Furniture.objects.filter(pk=pk).update(dataconfig=normalized)


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0222_protocol_is_deleted"),
    ]

    operations = [
        migrations.RunPython(normalize, migrations.RunPython.noop, elidable=True),
    ]
