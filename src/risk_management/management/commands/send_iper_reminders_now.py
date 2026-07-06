from django.core.management.base import BaseCommand

from risk_management.tasks import send_iper_update_reminders


class Command(BaseCommand):
    help = "Run send_iper_update_reminders synchronously, for local testing."

    def handle(self, *args, **options):
        send_iper_update_reminders()
        self.stdout.write(self.style.SUCCESS("send_iper_update_reminders executed"))