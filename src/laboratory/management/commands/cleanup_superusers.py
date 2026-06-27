from django.contrib.auth.models import User
from django.core.management import BaseCommand

KEEP_SUPERUSERS = ["luisza", "wendy.umana.herrera", "solvoadmin"]


class Command(BaseCommand):
    help = "Remove superuser status from all users not in the keep list"

    def handle(self, *args, **options):
        removed = User.objects.filter(is_superuser=True).exclude(username__in=KEEP_SUPERUSERS)
        count = removed.count()
        usernames = list(removed.values_list("username", flat=True))
        removed.update(is_superuser=False, is_staff=False)
        self.stdout.write(self.style.SUCCESS(
            f"Removed superuser from {count} user(s): {usernames}"
        ))