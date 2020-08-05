from django.contrib.auth.models import Permission
from django.core.management import BaseCommand
from django.apps.registry import apps
from django.contrib.contenttypes.management import create_contenttypes
from django.contrib.auth.management import create_permissions

class Command(BaseCommand):
    help = 'Set permissions'

    def handle(self, *args, **options):

        Permission.objects.all().delete()

        apps_list = ['academic', 'authentication', 'laboratory', 'msds', 'risk_management', 'sga']

        for app in apps_list:

            app_config = apps.get_app_config(app)
            create_contenttypes(app_config)
            create_permissions(app_config)
