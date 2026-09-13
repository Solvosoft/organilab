from .settings import *
from logging import Filter

INSTALLED_APPS.append("organilab_test")

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]


class NotInTestingFilter(Filter):
    def filter(self, record):
        from django.conf import settings

        return not settings.TESTING_MODE


LANGUAGE_CODE = "en"


LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        },
    },
    "filters": {"testing": {"()": NotInTestingFilter}},
    "handlers": {
        "console": {
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "class": "logging.StreamHandler",
            "stream": os.devnull,
            "formatter": "verbose",
            "filters": ["testing"],
        },
    },
    "loggers": {
        "fontTools.subset": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": True,
        },
        "": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": True,
        },
    },
}

# `organilab/celery.py` llama a config_from_object sin `namespace="CELERY"`, así
# que Celery no reconoce los nombres tipo CELERY_TASK_*: hay que usar los
# heredados que sí mapea (CELERY_ALWAYS_EAGER -> task_always_eager). Con los
# nombres equivocados las tareas intentaban conectarse al broker en los tests.
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_STORE_EAGER_RESULT = True

TESTING_MODE = True
GENERATE_SCREENSHOTS = os.getenv("GENERATE_SCREENSHOTS", "True") == "True"

# Directory for temporary selenium screenshots (PNGs used to build GIFs).
# Override with SELENIUM_SCREENSHOTS_DIR env var to keep them in a known location for debugging.
# Default: system temp directory (e.g. /tmp/organilab_selenium_screenshots/)
import tempfile  # noqa: E402

SELENIUM_SCREENSHOTS_DIR = os.getenv(
    "SELENIUM_SCREENSHOTS_DIR",
    os.path.join(tempfile.gettempdir(), "organilab_selenium_screenshots"),
)
