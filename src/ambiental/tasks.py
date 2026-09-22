import importlib

from django.conf import settings

from presentation.alerts import run_alert_rules

app = importlib.import_module(settings.CELERY_MODULE).app


@app.task
def check_consumption_anomalies():
    """Evalúa las reglas de alerta de consumo de todas las organizaciones."""
    return run_alert_rules("ambiental.consumption")
