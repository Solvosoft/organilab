from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def set_existing_approved(apps, schema_editor):
    OrganizationStructure = apps.get_model('laboratory', 'OrganizationStructure')
    Laboratory = apps.get_model('laboratory', 'Laboratory')
    OrganizationStructure.objects.update(approval_status=1)
    Laboratory.objects.update(approval_status=1)


def create_pending_approval_email_template(apps, schema_editor):
    EmailTemplate = apps.get_model('async_notifications', 'EmailTemplate')
    if not EmailTemplate.objects.filter(code='Pending approval').exists():
        EmailTemplate.objects.create(
            code='Pending approval',
            subject='Pending approval - {{ obj.name }}',
            message=(
                "<p>{% load i18n %}</p>"
                "<p>{% trans 'Hi,' %}</p>"
                "<p>{% blocktrans with name=obj.name %}A new item <strong>{{ name }}</strong> "
                "has been created and is pending your approval.{% endblocktrans %}</p>"
                "<p><a href='{{ url }}'>{% trans 'Go to approval page' %}</a></p>"
                "<p>{% trans 'Thanks,' %}<br/>{% trans 'Organilab system' %}</p>"
            ),
        )


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0199_shelfobject_shelfobject_code'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationstructure',
            name='approval_status',
            field=models.SmallIntegerField(
                choices=[(0, 'Pending approval'), (1, 'Approved')],
                default=0,
                verbose_name='Approval status',
            ),
        ),
        migrations.AddField(
            model_name='organizationstructure',
            name='approved_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='approved_organizations',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Approved by',
            ),
        ),
        migrations.AddField(
            model_name='organizationstructure',
            name='approved_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Approved at'),
        ),
        migrations.AddField(
            model_name='laboratory',
            name='approval_status',
            field=models.SmallIntegerField(
                choices=[(0, 'Pending approval'), (1, 'Approved')],
                default=0,
                verbose_name='Approval status',
            ),
        ),
        migrations.AddField(
            model_name='laboratory',
            name='approved_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='approved_laboratories',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Approved by',
            ),
        ),
        migrations.AddField(
            model_name='laboratory',
            name='approved_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Approved at'),
        ),
        migrations.RunPython(set_existing_approved, migrations.RunPython.noop),
        migrations.RunPython(
            create_pending_approval_email_template,
            migrations.RunPython.noop,
        ),
    ]