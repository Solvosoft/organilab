import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "organilab.asettings")

bind = os.getenv("UVICORN_BIND", "unix:/run/supervisor/gunicorn_asgi.sock")
wsgi_app = "organilab.asgi:application"
workers = int(os.getenv("UVICORN_WORKER", 2))
worker_class = "djgentelella.firmador_digital.config.asgi_worker.DjgentelellaUvicornWorker"
reload = os.getenv("UVICORN_RELOAD", "False").lower() == 'true'

user = "organilab"
group = "organilab"
