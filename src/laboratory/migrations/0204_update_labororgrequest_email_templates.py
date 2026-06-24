from django.db import migrations


def update_email_templates(apps, schema_editor):
    EmailTemplate = apps.get_model("async_notifications", "EmailTemplate")
    EmailTemplate.objects.filter(code="lab_or_org_request_created").update(
        subject="{{ subject|safe }}",
        message="{{ body|linebreaksbr }}",
    )
    EmailTemplate.objects.filter(code="lab_or_org_request_status_changed").update(
        subject="{{ subject|safe }}",
        message="{{ body|linebreaksbr }}",
    )


def revert_email_templates(apps, schema_editor):
    EmailTemplate = apps.get_model("async_notifications", "EmailTemplate")
    EmailTemplate.objects.filter(
        code__in=["lab_or_org_request_created", "lab_or_org_request_status_changed"]
    ).update(subject="{{ subject }}", message="{{ body }}")


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0203_add_labororgrequest_email_templates"),
    ]

    operations = [
        migrations.RunPython(update_email_templates, revert_email_templates),
    ]