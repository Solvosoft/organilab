from django.apps import AppConfig


class LaboratoryConfig(AppConfig):
    name = 'laboratory'

    def ready(self):
        import laboratory.signals
