from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Load groups by views without organization and laboratory'


    def save_permissions_group(self, permissions_list, group):

        for perm in permissions_list:
            perm = perm.split('.')
            permission = Permission.objects.filter(codename=perm[1], content_type__app_label=perm[0]).first()
            if permission:
                group.permissions.add(permission)
            else:
                print(perm)

    def create_groups(self):
        groups = [
            {
                "name": "Organizations",
                "permissions": [
                    "laboratory.view_laboratory", "derb.view_customform",
                    "laboratory.do_report", "sga.view_substance",
                    "risk_management.view_riskzone", "msds.view_msdsobject",
                    "laboratory.can_view_disposal", "laboratory.can_manage_disposal"
                ]
            },
            {
                "name": "Manage Organizations",
                "permissions": [
                    "laboratory.add_organizationstructure",
                    "laboratory.change_organizationstructure",
                    "laboratory.delete_organizationstructure",
                    "laboratory.view_organizationstructure"
                ]
            },
            {
                "name": "Work Inside Organizations",
                "permissions": [
                    "laboratory.change_organizationstructure",
                    "laboratory.view_organizationstructure"
                ]
            },
            {
                "name": "Blog",
                "permissions": ["blog.view_entry", "blog.delete_entry",
                                "blog.add_entry", "blog.change_entry",
                                "blog.add_category"]
            },
            {
                "name": "Profile",
                "permissions": ["auth.change_user"]
            }
        ]

        for g in groups:
            group = Group.objects.create(name=g["name"])
            self.save_permissions_group(g["permissions"], group)


    def handle(self, *args, **options):
        Group.objects.all().delete()
        self.create_groups()
