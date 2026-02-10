from django.apps import AppConfig
from django.core.management import call_command
from django.db.models.signals import post_migrate
from django.apps import apps as global_apps
from django.db import DEFAULT_DB_ALIAS


def load_initialdata(
    app_config,
    verbosity=2,
    interactive=True,
    using=DEFAULT_DB_ALIAS,
    apps=global_apps,
    **kwargs
):
    if app_config.__class__.__name__ == "LaboratoryConfig":
        print("Load initial data")
        call_command("loaddata", "initial_data.json")


class OrganilabTestConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "organilab_test"

    def ready(self):
        post_migrate.connect(load_initialdata)
