# Generated by Django 4.1.10 on 2023-10-18 15:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_and_perms', '0010_remove_unused_perms'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='language',
            field=models.CharField(choices=[('en', 'English'), ('es', 'Español')], default='es', max_length=4, verbose_name='Language'),
        ),
    ]
