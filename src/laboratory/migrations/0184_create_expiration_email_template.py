from django.db import migrations


class Migration(migrations.Migration):

    def create_template(apps, schema_editor):
        EmailTemplate = apps.get_model('async_notification', 'EmailTemplate')
        message = ("<p>Hola</p>"
                   "<p>&nbsp;</p>"
                   "<p>Usted ha recibido este correo porque tiene reactivos pr&oacute;ximos a vencer en el sistema Organilab.</p>"
                   "<p>&nbsp;</p>"
                   "<p>Este mensaje es para notificarle que uno o m&aacute;s reactivos en el laboratorio <strong>{{ laboratory.name }}</strong> vencer&aacute;n ma&ntilde;ana.</p>"
                   "<h4>Reactivos pr&oacute;ximos a vencer</h4>"
                   "{% for obj in shelf_object %}"
                   "<p>"
                   "<strong>Estante:</strong> {{ obj.shelf }} "
                   "<strong>Reactivo:</strong> {{ obj.object }} "
                   "<strong>Fecha de vencimiento:</strong> {{ obj.reactive_expiration_date }} "
                   "<strong>Cantidad disponible:</strong> {{ obj.quantity }} {{ obj.measurement_unit }}"
                   "</p>"
                   "<p><a href='{{ blockurl }}{{ obj.object.pk }}/'>{{ blockurl }}{{ obj.object.pk }}/</a></p>"
                   "{% endfor %}"
                   "<p>&nbsp;</p>"
                   "<p>&nbsp;</p>"
                   "<p>Por favor tome las medidas necesarias con estos reactivos antes de su vencimiento.</p>"
                   "<p><br />Gracias,<br /><br />Organilab: Notificaci&oacute;n de reactivos por vencer</p>"
                   "<p>&nbsp;</p>"
                   "<p>&nbsp;</p>")
        EmailTemplate.objects.get_or_create(
            code='expiring-reactives',
            defaults={
                'subject': 'Reactivos pr\u00f3ximos a vencer en {{ laboratory.name }}',
                'message': message,
            }
        )

    dependencies = [
        ('async_notification', '0006_newslettertemplate_model_base_m2m'),
        ('laboratory', '0183_create_shelf_object_email_template'),
    ]

    operations = [
        migrations.RunPython(create_template, migrations.RunPython.noop),
    ]
