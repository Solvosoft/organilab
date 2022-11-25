from django.contrib.auth.models import Group, Permission, User
from django.core.management import BaseCommand

from auth_and_perms.models import Rol, ProfilePermission
from laboratory.models import OrganizationUserManagement


class Command(BaseCommand):
    help = 'Load permission category'

    def clean_userpass(self):
        for user in User.objects.all():
            user.set_password('Admin12345')
            user.save()

    def handle(self, *args, **options):
        self.clean_userpass()
        return
