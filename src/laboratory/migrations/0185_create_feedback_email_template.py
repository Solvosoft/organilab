from django.db import migrations


class Migration(migrations.Migration):

    def create_template(apps, schema_editor):
        EmailTemplate = apps.get_model('async_notification', 'EmailTemplate')
        message = ("<p>Hola,</p>"
                   "<p>&nbsp;</p>"
                   "<p>Se ha recibido un nuevo feedback en el sistema Organilab.</p>"
                   )
        EmailTemplate.objects.get_or_create(
            code='new-feedback',
            defaults={
                'subject': 'New Feedback to Organilab: {{ feedback.title }}',
                'message': message,
            }
        )

    dependencies = [
        ('async_notification', '0006_newslettertemplate_model_base_m2m'),
        ('laboratory', '0184_create_expiration_email_template'),
    ]

    operations = [
        migrations.RunPython(create_template, migrations.RunPython.noop),
    ]
