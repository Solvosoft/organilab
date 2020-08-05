from django.contrib.auth.models import Permission, Group
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Set permissions groups'

    def handle(self, *args, **options):

        permissions_list = ['add_organizationusermanagement', 'change_organizationusermanagement',
                            'delete_organizationusermanagement', 'view_organizationusermanagement']

        admin_group = Group.objects.filter(name="Laboratory Administrator").first()

        if admin_group:
            for codename in permissions_list:
                permission= Permission.objects.get(codename=codename)
                admin_group.permissions.add(permission)


