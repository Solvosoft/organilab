from django.db import migrations

MESSAGE = (
    "<p>Hola,</p>"
    "<p>Organilab detectó una alerta ambiental:</p>"
    "<p><strong>{{ message }}</strong></p>"
    "<p>Edificio: {{ point.building }}<br>Punto de medición: {{ point.code }} - {{ point.name }}</p>"
    "<p>Revise la alerta y márquela como revisada con una nota que la explique: "
    "<a href='{{ link }}'>{{ link }}</a></p>"
    "<p>Organilab: gestión ambiental</p>"
)


def forwards(apps, schema_editor):
    EmailTemplate = apps.get_model("async_notification", "EmailTemplate")
    EmailTemplate.objects.get_or_create(
        code="ambiental-consumption-alert",
        defaults={
            "subject": "Alerta ambiental: {{ message }}",
            "message": MESSAGE,
            "context_code": "ambiental-consumption-alert",
        },
    )


def backwards(apps, schema_editor):
    apps.get_model("async_notification", "EmailTemplate").objects.filter(
        code="ambiental-consumption-alert"
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("ambiental", "0006_consumptionalert"),
        ("async_notification", "0008_normalize_compliance_emails"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
