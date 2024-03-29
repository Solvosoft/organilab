# Generated by Django 2.2.20 on 2021-05-24 15:22

from django.db import migrations


class Migration(migrations.Migration):

    def update_template(apps, schema_editor):
        model = apps.get_model('async_notifications', 'TemplateContext')
        template = model.objects.filter(code='Shelf object in limit').first()
        if template is not None:
            template.context_dic = {
                "Lista de objectos que se encuentra en el limite del laboratorio {{laboratory.name}}": [
                    ["shelf_object", "Object in limit"], ["laboratory", "Laboratory where is the object"]]}
            template.save()
    dependencies = [
        ('async_notifications', '0004_auto_20200228_1653'),
        ('laboratory', '0039_precursorreport_consecutive'),
    ]

    operations = [
        migrations.RunPython(update_template),
    ]

