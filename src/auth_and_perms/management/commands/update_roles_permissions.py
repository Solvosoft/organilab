from django.contrib.auth.models import Permission
from django.core.management import BaseCommand
from auth_and_perms.models import Rol


class Command(BaseCommand):
    help = "Load new Rol"

    def add_arguments(self, parser):
        parser.add_argument(
            "--noinput",
            action="store_true",
            help="Do ask to continue",
        )

    def init(self):
        self.data = [
            {
                "laboratoryroom": [
                    "add_laboratoryroom",
                    "change_laboratoryroom",
                    "delete_laboratoryroom",
                    "view_laboratoryroom",
                ],
                "furniture": [
                    "add_furniture",
                    "change_furniture",
                    "delete_furniture",
                    "view_furniture",
                ],
                "shelf": [
                    "add_shelf",
                    "change_shelf",
                    "delete_shelf",
                    "view_shelf",
                ],
                "objectfeatures": [
                    "add_objectfeatures",
                    "change_objectfeatures",
                    "delete_objectfeatures",
                    "view_objectfeatures",
                ],
            }
        ]

    def create_rol(self):
        student_rol = Rol.objects.get(name="Estudiante")

        for perm in self.data:
            for model, perms in perm.items():
                permissions = Permission.objects.filter(
                    codename__in=perms,
                    content_type__app_label="laboratory",
                    content_type__model=model,
                )
                if permissions:
                    print(permissions)
                    student_rol.permissions.add(*permissions)

    def handle(self, *args, **options):
        self.init()
        self.create_rol()
