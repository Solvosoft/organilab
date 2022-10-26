from django.apps import AppConfig


class AuthAndPermsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth_and_perms'

    def ready(self):
        import auth_and_perms.signals
