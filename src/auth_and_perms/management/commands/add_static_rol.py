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
        self.data = {
          "name": "Manejo de sustancias del laboratorio",
          "color": "#80EEB3",
          "permissions": [
              276,
              455,
              658,
              661,
              44,
              1,
              40,
              34,
              33,
              79,
              604,
              26,
              657,
              27,
              25,
              682,
              683,
              685,
              674,
              675,
              677,
              670,
              671,
              673,
              609,
              612,
              662,
              663,
              665,
              424,
              427
            ]
        }
    def create_rol(self):
        rol = Rol.objects.create(name=self.data["name"], color=self.data["color"])
        for perm in self.data["permissions"]:
            rol.permissions.add(perm)

    def handle(self, *args, **options):
        self.init()
        self.create_rol()
