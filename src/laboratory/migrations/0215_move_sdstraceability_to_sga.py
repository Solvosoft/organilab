from django.db import migrations


def repoint_content_type(apps, schema_editor):
    """Reetiqueta el ContentType en vez de dejar que Django cree permisos nuevos.

    Al mover un modelo de app, `post_migrate` crearía cuatro permisos nuevos bajo
    `sga` y los antiguos de `laboratory` quedarían huérfanos: todas las
    asignaciones a roles y grupos apuntarían a permisos muertos y se perderían en
    silencio. Cambiando el `app_label` del ContentType existente, las filas de
    `auth_permission` conservan su id y, con ellas, cada asignación.
    """
    db_alias = schema_editor.connection.alias
    ContentType = apps.get_model("contenttypes", "ContentType")

    updated = (
        ContentType.objects.using(db_alias)
        .filter(app_label="laboratory", model="sdstraceability")
        .update(app_label="sga")
    )
    if updated:
        print("\nRepointed SDSTraceability content type to the sga app")


def restore_content_type(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    ContentType = apps.get_model("contenttypes", "ContentType")
    ContentType.objects.using(db_alias).filter(
        app_label="sga", model="sdstraceability"
    ).update(app_label="laboratory")


class Migration(migrations.Migration):
    """Saca SDSTraceability del estado de `laboratory`.

    La tabla física no se toca: el modelo pasa a `sga` conservando
    `db_table = "laboratory_sdstraceability"`, así que esto es solo estado.
    """

    dependencies = [
        ("laboratory", "0214_grant_sga_characteristics_permissions"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(repoint_content_type, reverse_code=restore_content_type),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name="SDSTraceability"),
            ],
            database_operations=[],
        ),
    ]
