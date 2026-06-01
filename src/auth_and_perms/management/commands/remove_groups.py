from django.contrib.auth.models import User, Group
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Load permission category"

    def init_groups(self):
        self.groups = Group.objects.filter(
            name__in=["Student", "Professor", "Manage Roles Permissions"]
        )

        self.ultra_group = Group.objects.get(name="RegisterOrganization")

    def remove_groups(self):
        for group in self.groups:
            for user in User.objects.filter(groups=group):
                user.groups.remove(group)
                user.save()
        self.groups.delete()

    def remove_ultra_group(self):
        for user in User.objects.filter(groups=self.ultra_group).exclude(
            is_superuser=True
        ):
            user.groups.remove(self.ultra_group)
            user.save()

    def handle(self, *args, **options):
        self.init_groups()
        self.remove_groups()
        self.remove_ultra_group()
