# Traspasa las plantillas de correo del paquete externo async-notifications 0.2
# a djgentelella.async_notification, normalizando los codigos a slug (el campo
# code del modelo nuevo es SlugField). En una base con datos, el contenido
# vigente de la tabla vieja gana sobre los defaults horneados aqui.

from django.db import migrations

# {old_code: {new_code, subject, message, bcc, cc}}
TEMPLATES = {'Shelf object in limit': {'new_code': 'shelf-object-in-limit', 'subject': 'The shelf object called {{shelf_object.object.name}} reached its limit quantity', 'message': '\n<p>Hola,</p>\n<br>\n<p>Usted ha recibido este correo porque tiene un cambio en un laboratorio en el sistema Organilab.</p>\n<p>Este mensaje es para notificarle que uno o más objetos en su laboratorio están en las cuotas mínimas</p>\n\n<h4>Detalle de productos:</h4>\n\n<strong>Estante:</strong> {{ shelf_object.shelf }}\n<strong>Objeto:</strong> {{ shelf_object.object }}\n<strong>Cantidad de material:</strong> {{ shelf_object.quantity }}\n<strong>Cantidad límite de material:</strong> {{ shelf_object.limit_quantity }}\n<strong>Unidad de medida:</strong> {{ shelf_object.measurement_unit }}\n\n<br><br>\n<p>Por favor recargue este producto o contacte a la persona que lo reservó para cambiar la cantidad disponible.</p>\n<p>\nSi no desea recibir notificaciones de este objeto, por favor utilice<a href="{{ domain }}" >\n\teste enlace</a>.\n</p>\n<p>\nsi su servicio de correo electrónico bloquea los enlaces, copie y pegue esta url en una nueva pestaña\n<br> </p>\n</p>\n<br>\nGracias,\n<br> <br>\nOrganilab: Reporte de objetos', 'bcc': '', 'cc': ''}, 'Expiring reactives': {'new_code': 'expiring-reactives', 'subject': 'Expiring reactives - {{ laboratory.name }}', 'message': "<p>Hola</p><p>&nbsp;</p><p>Usted ha recibido este correo porque tiene reactivos pr&oacute;ximos a vencer en el sistema Organilab.</p><p>&nbsp;</p><p>Este mensaje es para notificarle que uno o m&aacute;s reactivos en el laboratorio <strong>{{ laboratory.name }}</strong> vencer&aacute;n ma&ntilde;ana.</p><h4>Reactivos pr&oacute;ximos a vencer</h4>{% for obj in shelf_object %}<p><strong>Estante:</strong> {{ obj.shelf }} <strong>Reactivo:</strong> {{ obj.object }} <strong>Fecha de vencimiento:</strong> {{ obj.reactive_expiration_date }} <strong>Cantidad disponible:</strong> {{ obj.quantity }} {{ obj.measurement_unit }}</p><p><a href='{{ blockurl }}{{ obj.object.pk }}/'>{{ blockurl }}{{ obj.object.pk }}/</a></p>{% endfor %}<p>&nbsp;</p><p>&nbsp;</p><p>Por favor tome las medidas necesarias con estos reactivos antes de su vencimiento.</p><p><br />Gracias,<br /><br />Organilab: Notificaci&oacute;n de reactivos por vencer</p><p>&nbsp;</p><p>&nbsp;</p>", 'bcc': '', 'cc': ''}, 'New feedback': {'new_code': 'new-feedback', 'subject': 'New Feedback to Organilab', 'message': '<h2>New Feedback Received</h2>\n<p><strong>Title:</strong> {{ feedback.title }}</p>\n{% if feedback.user %}<p><strong>User:</strong> {{ feedback.user.get_full_name }} ({{ feedback.user.email }})</p>{% endif %}\n<hr>\n<p><strong>Explanation:</strong></p>\n<div>{{ explanation|safe }}</div>\n{% if file_url %}<br><p><strong>Archivo adjunto:</strong> <a href="{{ file_url }}">{{ feedback.related_file.name }}</a></p>{% endif %}\n<br>\n<p><a href="{{ admin_url }}">Ver en el administrador</a></p>', 'bcc': '', 'cc': ''}, 'new user': {'new_code': 'new-user', 'subject': 'You are register now in Organilab', 'message': ' ', 'bcc': '', 'cc': ''}, 'Request demo': {'new_code': 'request-demo', 'subject': 'New demo request', 'message': 'User information:<br>\n                        {{data.name}}<br>\n                        {{data.business_email}}<br>\n                        {{data.company_name}}<br>\n                        {{data.country}}<br>\n                        {{data.phone_number}}\n                        ', 'bcc': '', 'cc': ''}, 'lab_or_org_request_created': {'new_code': 'lab_or_org_request_created', 'subject': '{{ subject|safe }}', 'message': '{{ body|linebreaksbr }}', 'bcc': '', 'cc': ''}, 'lab_or_org_request_status_changed': {'new_code': 'lab_or_org_request_status_changed', 'subject': '{{ subject|safe }}', 'message': '{{ body|linebreaksbr }}', 'bcc': '', 'cc': ''}}


def forwards(apps, schema_editor):
    EmailTemplate = apps.get_model('async_notification', 'EmailTemplate')
    connection = schema_editor.connection

    old_rows = {}
    if 'async_notifications_emailtemplate' in connection.introspection.table_names():
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT code, subject, message, bcc, cc '
                'FROM async_notifications_emailtemplate'
            )
            for code, subject, message, bcc, cc in cursor.fetchall():
                old_rows[code] = {
                    'subject': subject,
                    'message': message,
                    'bcc': bcc or '',
                    'cc': cc or '',
                }

    for old_code, meta in TEMPLATES.items():
        data = old_rows.get(old_code, meta)
        EmailTemplate.objects.update_or_create(
            code=meta['new_code'],
            defaults={
                'subject': data['subject'],
                'message': data['message'],
                'bcc': data['bcc'],
                'cc': data['cc'],
                'context_code': meta['new_code'],
            },
        )


def backwards(apps, schema_editor):
    EmailTemplate = apps.get_model('async_notification', 'EmailTemplate')
    codes = [meta['new_code'] for meta in TEMPLATES.values()]
    EmailTemplate.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0218_derive_laboratory_and_organization_codes'),
        ('async_notification', '0008_normalize_compliance_emails'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
