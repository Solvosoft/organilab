from django.apps import AppConfig


class AuthAndPermsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth_and_perms'

    def ready(self):
        import auth_and_perms.signals
        from django.contrib import admin
        from django.contrib.admin.models import LogEntry
        from auth_and_perms.admin import ExtendedLogEntryAdmin

        # djgentelella's admin.py (autodiscovered after auth_and_perms's, per
        # app order in INSTALLED_APPS) registers LogEntry first. Overriding
        # it here (in ready(), not at admin.py import time) guarantees that
        # registration has already happened.
        admin.site.unregister(LogEntry)
        admin.site.register(LogEntry, ExtendedLogEntryAdmin)
