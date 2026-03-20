from django.db import migrations


class Migration(migrations.Migration):

    def create_template(apps, schema_editor):
        EmailTemplate = apps.get_model('async_notification', 'EmailTemplate')
        message = ("{% load i18n %}"
                   "<p>{% trans 'Hi,' %}</p>"
                   "<br>"
                   "<p>{% trans 'You have received this email because you are in charge of a laboratory in the Organilab system.' %}</p>"
                   "<p>{% trans 'This message is to notify you that one of the shelf objects of your laboratory has reached its limit' %}</p>"
                   "<h4>{% trans 'This are the details of the product:' %}</h4>"
                   "{% for obj in shelf_object %}"
                   "<p>"
                   "<strong>{% trans 'Shelf:' %}</strong> {{ obj.shelf }} "
                   "<strong>{% trans 'Object:' %}</strong> {{ obj.object }} "
                   "<strong>{% trans 'Material quantity:' %}</strong> {{ obj.quantity }} "
                   "<strong>{% trans 'Limit material quantity:' %}</strong> {{ obj.limit_quantity }} "
                   "<strong>{% trans 'Measurement unit:' %}</strong> {{ obj.measurement_unit }}"
                   "</p>"
                   "{% endfor %}"
                   "<br>"
                   "<p>{% trans 'Please refill this product or contact the people that reserved it to balance the current quantity.' %}</p>"
                   "<p>{% trans \"If you don't want to recieve notifications of this object, please use\" %}"
                   "<a href='{{ blockurl }}'>{% trans ' this link' %}</a>.</p>"
                   "<p>{% blocktrans %}if your email service block links then copy and paste this url in a new tab{% endblocktrans %}"
                   "<br> {{ blockurl }}</p>"
                   "<br>"
                   "{% trans 'Thanks,' %}"
                   "<br><br>"
                   "{% trans 'Organilab system' %}")
        EmailTemplate.objects.get_or_create(
            code='shelf-object-in-limit',
            defaults={
                'subject': 'The shelf object called {{shelf_object.object.name}} reached its limit quantity',
                'message': message,
            }
        )

    dependencies = [
        ('async_notification', '0006_newslettertemplate_model_base_m2m'),
        ('laboratory', '0182_alter_informscheduler_active'),
    ]

    operations = [
        migrations.RunPython(create_template, migrations.RunPython.noop),
    ]
