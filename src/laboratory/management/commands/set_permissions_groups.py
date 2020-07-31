from django.contrib.auth.models import Permission, Group
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Set permissions groups'

    def handle(self, *args, **options):

        for g in Group.objects.all():
            print(g.name.upper())
            for p in g.permissions.all():
                print("Nombre: "+p.name+"\tCodename: "+p.codename)

