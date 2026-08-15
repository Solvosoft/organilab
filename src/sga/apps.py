from django.apps import AppConfig


class SgaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sga'

    def ready(self):
        # El motor de etiquetas resuelve las frases H/P contra la base de datos
        # antes de caer a su catálogo local. Se registra la función, que es
        # perezosa: no hay consultas hasta que se genera una etiqueta.
        from sga.label_engine.phrases_catalog import set_phrase_resolver
        from sga.label_phrases import resolve

        set_phrase_resolver(resolve)
