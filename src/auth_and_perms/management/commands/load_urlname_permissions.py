from django.contrib.auth.models import Permission
from django.core.management import BaseCommand

from humanresources.management.commands.urlname_permissions import URLNAME_PERMISSIONS
from humanresources.models import PermissionsCategoryManagement


class Command(BaseCommand):
    help = 'Load permission category'

    def get_permission(self, app_codename):
        perm = None
        val = app_codename.split('.')
        if len(val) == 2:
            perm = Permission.objects.filter(
                codename=val[1],
                content_type__app_label=val[0])

        return perm

    def load_urlname_permissions(self):

        for url_name, item_list in URLNAME_PERMISSIONS.items():

            for obj in item_list:
                perm = self.get_permission(obj['permission'])

                if perm:
                    permcat = PermissionsCategoryManagement.objects.filter(name=obj['name'], category=obj['category'],
                                                                         permission=perm.first(), url_name=url_name)

                    if not permcat.exists():
                        new_permcat = PermissionsCategoryManagement(
                            name=obj['name'], category=obj['category'], permission=perm.first(), url_name=url_name
                        )
                        new_permcat.save()
                    else:
                        print("'"+obj['name']+ "' already exists.")

                else:
                    print("'"+obj['permission'] + "' doesn't exist.")


    def handle(self, *args, **options):
        PermissionsCategoryManagement.objects.all().delete()
        self.load_urlname_permissions()