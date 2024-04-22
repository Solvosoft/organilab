from django.core.management.base import BaseCommand
from laboratory.models import ShelfObject, ObjectLogChange
from laboratory.tasks import create_precursor_reports




class Command(BaseCommand):

    help = ''
    def update_changgelog(self):
        ObjectLogChange.objects.filter(type_action=0).update(type_action=1)
    def create_report(self):
        create_precursor_reports()

    def handle(self, *args, **options):
        self.create_report()
