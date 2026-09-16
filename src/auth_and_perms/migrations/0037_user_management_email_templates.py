from django.db import migrations

CODES = ("user-merged", "user-deleted", "user-deletion-warning")


def create_email_templates(apps, schema_editor):
    EmailTemplate = apps.get_model("async_notification", "EmailTemplate")
    for code in CODES:
        EmailTemplate.objects.get_or_create(
            code=code,
            defaults={
                "subject": "{{ subject|safe }}",
                "message": "{{ body|linebreaksbr }}",
                "context_code": code,
            },
        )


def delete_email_templates(apps, schema_editor):
    EmailTemplate = apps.get_model("async_notification", "EmailTemplate")
    EmailTemplate.objects.filter(code__in=CODES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("auth_and_perms", "0036_userdeletionrequest_can_manage_users"),
        ("async_notification", "0008_normalize_compliance_emails"),
    ]

    operations = [
        migrations.RunPython(create_email_templates, delete_email_templates),
    ]
