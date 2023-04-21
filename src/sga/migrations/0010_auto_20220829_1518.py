# Generated by Django 3.2 on 2022-08-29 21:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
def delete_templates(apps, schema_editor):
    TemplateSGA = apps.get_model('sga', 'TemplateSGA')
    PersonalTemplateSGA = apps.get_model('sga', 'PersonalTemplateSGA')

    TemplateSGA.objects.all().delete()
    PersonalTemplateSGA.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sga', '0009_personaltemplatesga'),
    ]

    operations = [
        migrations.RunPython(delete_templates),
        migrations.RemoveField(
            model_name='personaltemplatesga',
            name='recipient_size',
        ),
        migrations.AddField(
            model_name='personaltemplatesga',
            name='preview',
            field=models.TextField(help_text='B64 preview image', null=True),
        ),
        migrations.AddField(
            model_name='personaltemplatesga',
            name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='sga.templatesga', verbose_name='Template SGA'),
        ),
        migrations.AddField(
            model_name='templatesga',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]