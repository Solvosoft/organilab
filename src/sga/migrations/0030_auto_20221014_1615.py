# Generated by Django 3.2 on 2022-10-14 22:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sga', '0029_securityleaf_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='securityleaf',
            name='annotation',
            field=models.TextField(blank=True, null=True, verbose_name='Annotation'),
        ),
        migrations.AddField(
            model_name='securityleaf',
            name='font',
            field=models.TextField(blank=True, null=True, verbose_name='font'),
        ),
        migrations.CreateModel(
            name='ReviewSubstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.IntegerField(blank=True, null=True, verbose_name='Note')),
                ('is_approved', models.BooleanField(default=False)),
                ('substance', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='sga.substance', verbose_name='Substance')),
            ],
            options={
                'verbose_name': 'Review Substance',
                'verbose_name_plural': 'Review Substance',
            },
        ),
    ]
