from django.db import migrations


def create_email_templates(apps, schema_editor):
    EmailTemplate = apps.get_model("async_notifications", "EmailTemplate")
    EmailTemplate.objects.get_or_create(
        code="lab_or_org_request_created",
        defaults={
            "subject": "{{ subject|safe }}",
            "message": "{{ body|linebreaksbr }}",
        },
    )
    EmailTemplate.objects.get_or_create(
        code="lab_or_org_request_status_changed",
        defaults={
            "subject": "{{ subject|safe }}",
            "message": "{{ body|linebreaksbr }}",
        },
    )


def delete_email_templates(apps, schema_editor):
    EmailTemplate = apps.get_model("async_notifications", "EmailTemplate")
    EmailTemplate.objects.filter(
        code__in=["lab_or_org_request_created", "lab_or_org_request_status_changed"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0202_remove_labororgrequest_enable_child_organizations_and_more"),
        ("async_notifications", "0008_remove_newslettertemplate_file_path"),
    ]

    operations = [
        migrations.RunPython(create_email_templates, delete_email_templates),
    ]