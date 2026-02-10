from django.contrib.auth.models import Permission, Group
from django.core.management import BaseCommand

from auth_and_perms.management.commands.urlname_permissions import URLNAME_PERMISSIONS
from djgentelella.models import PermissionsCategoryManagement


class Command(BaseCommand):
    help = "Load permission category"

    def get_permission(self, app_codename):
        perm = None
        val = app_codename.split(".")
        if len(val) == 2:
            perm = Permission.objects.filter(
                codename=val[1], content_type__app_label=val[0]
            )

        return perm

    def get_urlname_permission(self):
        admin = []
        admin_perms = []
        for key, value in URLNAME_PERMISSIONS.items():
            for item in value:
                if item["permission"] not in admin_perms:
                    admin.append(item)
                    admin_perms.append(item["permission"])
        URLNAME_PERMISSIONS["org_administrator"] = admin
        return URLNAME_PERMISSIONS

    def load_urlname_permissions(self):
        group, _ = Group.objects.get_or_create(name="RegisterOrganization")
        urlnames = self.get_urlname_permission()
        for url_name, item_list in urlnames.items():
            for obj in item_list:
                perm = self.get_permission(obj["permission"])
                if perm:
                    perm = perm.first()
                    group.permissions.add(perm)
                    permcat = PermissionsCategoryManagement.objects.filter(
                        name=obj["name"],
                        category=obj["category"],
                        permission=perm,
                        url_name=url_name,
                    )

                    if not permcat.exists():
                        new_permcat = PermissionsCategoryManagement(
                            name=obj["name"],
                            category=obj["category"],
                            permission=perm,
                            url_name=url_name,
                        )
                        new_permcat.save()
                    else:
                        print("'" + obj["name"] + "' already exists.")

                else:
                    print("'" + obj["permission"] + "' doesn't exist.")

    def handle(self, *args, **options):
        PermissionsCategoryManagement.objects.all().delete()
        self.load_urlname_permissions()
