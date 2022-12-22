from django.apps import AppConfig


class PresentationConfig(AppConfig):
    name = 'presentation'

    def ready(self):
        import presentation.signals
        super(PresentationConfig, self).ready()
