from django.db import migrations


def create_email_templates(apps, schema_editor):
    EmailTemplate = apps.get_model('async_notifications', 'EmailTemplate')

    EmailTemplate.objects.filter(code='Auto approved creation').delete()
    EmailTemplate.objects.create(
        code='Auto approved creation',
        subject='{% load i18n %}{% blocktrans with name=obj.name %}Creation report: {{ name }}{% endblocktrans %}',
        message=(
            "<p>{% load i18n %}</p>"
            "<p>{% trans 'Hi,' %}</p>"
            "<p>{% blocktrans with name=obj.name creator=creator %}"
            "<strong>{{ creator }}</strong> has created <strong>{{ name }}</strong> "
            "and it has been automatically approved."
            "{% endblocktrans %}</p>"
            "<p><a href='{{ url }}'>{% trans 'Go to organization management' %}</a></p>"
            "<p>{% trans 'Thanks,' %}<br/>{% trans 'Organilab' %}</p>"
        ),
    )

    pending = EmailTemplate.objects.filter(code='Pending approval').first()
    if pending and '{{ creator }}' not in pending.message:
        pending.message = (
            "<p>{% load i18n %}</p>"
            "<p>{% trans 'Hi,' %}</p>"
            "<p>{% blocktrans with name=obj.name creator=creator %}"
            "<strong>{{ creator }}</strong> has created <strong>{{ name }}</strong> "
            "and it is pending your approval."
            "{% endblocktrans %}</p>"
            "<p><a href='{{ url }}'>{% trans 'Go to approval page' %}</a></p>"
            "<p>{% trans 'Thanks,' %}<br/>{% trans 'Organilab system' %}</p>"
        )
        pending.save()


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0201_alter_approval_fields'),
        ('async_notifications', '__first__'),
    ]

    operations = [
        migrations.RunPython(create_email_templates, reverse_code=migrations.RunPython.noop),
    ]
