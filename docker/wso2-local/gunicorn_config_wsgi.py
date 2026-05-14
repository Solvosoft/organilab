import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "organilab.settings")

bind = "unix:/run/supervisor/gunicorn_wsgi.sock"
wsgi_app = "organilab.wsgi:application"
workers = int(os.getenv("GUNICORN_WORKER", 2))
user = "organilab"
group = "organilab"
forwarded_allow_ips = ""  # do not trust X-Forwarded-Proto from nginx (local dev uses http)