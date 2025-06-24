from django.contrib.admin.models import ADDITION, CHANGE
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils.timezone import now
from laboratory.models import ShelfObject, ObjectLogChange, Catalog, Laboratory, Object
from django.utils.translation import gettext_lazy as _

class Command(BaseCommand):

    help = 'Update subect message in ObjectLogChange'

    def update_precursor(self):
        ObjectLogChange.objects.filter(subject="Add").update(subject=_("Income"))
        ObjectLogChange.objects.filter(subject="Create").update(subject=_("Income"))
        ObjectLogChange.objects.filter(subject="Substract").update(subject=_("Spend"))

    def handle(self, *args, **options):
        self.update_precursor()
