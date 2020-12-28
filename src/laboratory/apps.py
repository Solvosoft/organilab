from django.apps import AppConfig
from django.template.loader import render_to_string


class LaboratoryConfig(AppConfig):
    name = 'laboratory'

    def ready(self):
        import laboratory.signals
        from async_notifications.register import update_template_context
        from async_notifications.register import DummyContextObject

        super(LaboratoryConfig, self).ready()
        context = [
            ('shelf_object', 'Object in limit'),
            ('labroom', 'Labroom where is the object'),
            ('laboratory', 'Laboratory where is the object'),
            ('domain', 'url to block notifications')
        ]
        message = render_to_string('email/shelf_object_quantity_limit.html',
                                   context={
                                       'shelf_object': DummyContextObject('shelf_object'),
                                       'domain': DummyContextObject('domain')
                                   }
                                   )
        update_template_context(
            "Shelf object in limit",
            'The shelf object called {{shelf_object.object.name}} reached its limit quantity',
            context, message=message)
