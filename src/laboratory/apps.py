from django.apps import AppConfig


class LaboratoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'laboratory'

    def ready(self):
        import laboratory.signals
        from djgentelella.async_notification.registry import register_context

        super(LaboratoryConfig, self).ready()
        register_context(
            code='shelf-object-in-limit',
            subject='The shelf object called {{shelf_object.object.name}} '
                    'reached its limit quantity',
            models={
                'shelf_object': 'laboratory.ShelfObject',
                'labroom': 'laboratory.LaboratoryRoom',
                'laboratory': 'laboratory.Laboratory',
            },
            extra_variables={
                'domain': 'Site domain, used to build links',
                'blockurl': 'URL to block these notifications',
            },
        )
        register_context(
            code='expiring-reactives',
            subject='Expiring reactives - {{ laboratory.name }}',
            models={
                'laboratory': 'laboratory.Laboratory',
            },
            extra_variables={
                'shelf_objects': 'List of expiring shelf objects',
                'domain': 'Site domain, used to build links',
            },
        )
        register_context(
            code='lab_or_org_request_created',
            subject='{{ subject|safe }}',
            models={},
            extra_variables={
                'subject': 'Rendered subject of the request',
                'body': 'Rendered body of the request',
            },
        )
        register_context(
            code='lab_or_org_request_status_changed',
            subject='{{ subject|safe }}',
            models={},
            extra_variables={
                'subject': 'Rendered subject of the request',
                'body': 'Rendered body of the request',
            },
        )
