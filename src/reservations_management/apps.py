from django.apps import AppConfig


class ReservationsManagementConfig(AppConfig):
    name = 'reservations_management'

    def ready(self):
            import reservations_management.signals
