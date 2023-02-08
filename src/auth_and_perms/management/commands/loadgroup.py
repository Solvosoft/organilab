from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand
from auth_and_perms.management.commands.urlname_permissions import URLNAME_PERMISSIONS

class Command(BaseCommand):
    help = 'Load permission category'

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name='RegisterOrganization')
        group.permissions.clear()

        PERMISSIONS = set()
        for item in URLNAME_PERMISSIONS:
            for perm in URLNAME_PERMISSIONS[item]:
                PERMISSIONS.add(perm['permission'])
        for perm in PERMISSIONS:
            perm = perm.split('.')
            permission = Permission.objects.filter(codename=perm[1], content_type__app_label=perm[0]).first()
            if permission:
                group.permissions.add(permission)
            else:
                print(perm)