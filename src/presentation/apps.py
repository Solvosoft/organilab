from django.apps import AppConfig


class PresentationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'presentation'

    def ready(self):
        import presentation.signals
        import presentation.alerts  # noqa: F401  registra los canales de alerta de organilab
        super(PresentationConfig, self).ready()
