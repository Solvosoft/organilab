# Generated by Django 4.0.8 on 2023-01-29 22:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('laboratory', '0071_sustancecharacteristics_img_representation'),
    ]

    operations = [
        migrations.AddField(
            model_name='shelf',
            name='color',
            field=models.CharField(default='#73879C', max_length=10),
        ),
    ]
