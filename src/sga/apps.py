from django.apps import AppConfig


class SgaConfig(AppConfig):
    name = 'sga'

    def ready(self):
        import sga.signals
        super(SgaConfig, self).ready()
