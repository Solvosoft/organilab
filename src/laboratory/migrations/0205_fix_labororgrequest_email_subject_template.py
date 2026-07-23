from django.db import migrations


def fix_subject_templates(apps, schema_editor):
    EmailTemplate = apps.get_model("async_notifications", "EmailTemplate")
    EmailTemplate.objects.filter(
        code__in=["lab_or_org_request_created", "lab_or_org_request_status_changed"]
    ).update(subject="{{ subject|safe }}")


def revert_subject_templates(apps, schema_editor):
    EmailTemplate = apps.get_model("async_notifications", "EmailTemplate")
    EmailTemplate.objects.filter(
        code__in=["lab_or_org_request_created", "lab_or_org_request_status_changed"]
    ).update(subject="{{ subject }}")


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0204_update_labororgrequest_email_templates"),
    ]

    operations = [
        migrations.RunPython(fix_subject_templates, revert_subject_templates),
    ]