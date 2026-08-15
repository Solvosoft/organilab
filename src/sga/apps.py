from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save


class SgaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sga'

    def ready(self):
        # El motor de etiquetas resuelve las frases H/P contra la base de datos
        # antes de caer a su catálogo local. Se registra la función, que es
        # perezosa: no hay consultas hasta que se genera una etiqueta.
        from sga.label_engine.phrases_catalog import set_phrase_resolver
        from sga.label_phrases import invalidate, resolve

        set_phrase_resolver(resolve)

        # El mapa de frases vive en memoria del proceso: se descarta al editar
        # el catálogo GHS para que la siguiente etiqueta use el texto nuevo.
        def _drop_phrase_cache(sender, **kwargs):
            invalidate()

        for model in ("DangerIndication", "PrudenceAdvice"):
            post_save.connect(
                _drop_phrase_cache,
                sender=self.get_model(model),
                dispatch_uid=f"sga_label_phrases_{model}_save",
                weak=False,
            )
            post_delete.connect(
                _drop_phrase_cache,
                sender=self.get_model(model),
                dispatch_uid=f"sga_label_phrases_{model}_delete",
                weak=False,
            )
