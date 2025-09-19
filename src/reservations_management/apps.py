from django.apps import AppConfig


class ReservationsManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reservations_management"

    def ready(self):
        import reservations_management.signals
