from django.apps import AppConfig


class LaboratoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'laboratory'

    def ready(self):
        import laboratory.signals
        # TODO: migrate to djgentelella.async_notification.registry.register_context
        # from async_notifications.register import update_template_context
        # from async_notifications.register import DummyContextObject
        # update_template_context(
        #     "Shelf object in limit",
        #     'The shelf object called {{shelf_object.object.name}} reached its limit quantity',
        #     [...], message=message)

        super(LaboratoryConfig, self).ready()
