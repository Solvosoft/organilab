from django.db import migrations

CODE = "equipment-control-alert"
MESSAGE = (
    "<p>Hola,</p>"
    "<p>Un registro de control de equipos quedó fuera de sus límites o de su criterio de aceptación:</p>"
    "<p><strong>{{ message }}</strong></p>"
    "<p>Revise la carta de control y registre la desviación y la acción tomada: "
    "<a href='{{ link }}'>{{ link }}</a></p>"
    "<p>Organilab: gestión de equipos</p>"
)


def forwards(apps, schema_editor):
    apps.get_model("async_notification", "EmailTemplate").objects.get_or_create(
        code=CODE, defaults={"subject": "Control de equipos: {{ message }}", "message": MESSAGE, "context_code": CODE}
    )


def backwards(apps, schema_editor):
    apps.get_model("async_notification", "EmailTemplate").objects.filter(code=CODE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0232_equipment_control_charts"),
        ("async_notification", "0008_normalize_compliance_emails"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
