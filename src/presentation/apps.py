from django.apps import AppConfig


class PresentationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'presentation'

    def ready(self):
        import presentation.signals
        super(PresentationConfig, self).ready()
