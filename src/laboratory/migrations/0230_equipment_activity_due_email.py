from django.db import migrations

CODE = "equipment-activity-due"
MESSAGE = (
    "<p>Hola,</p>"
    "<p>Organilab le recuerda una actividad del programa de equipos:</p>"
    "<p><strong>{{ message }}</strong></p>"
    "<p>Registre la actividad realizada (con su certificado o informe) en la ficha del equipo: "
    "<a href='{{ link }}'>{{ link }}</a></p>"
    "<p>Organilab: gestión de equipos</p>"
)


def forwards(apps, schema_editor):
    EmailTemplate = apps.get_model("async_notification", "EmailTemplate")
    EmailTemplate.objects.get_or_create(
        code=CODE,
        defaults={"subject": "Equipos: {{ message }}", "message": MESSAGE, "context_code": CODE},
    )


def backwards(apps, schema_editor):
    apps.get_model("async_notification", "EmailTemplate").objects.filter(code=CODE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0229_equipment_iso17025_data"),
        ("async_notification", "0008_normalize_compliance_emails"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
