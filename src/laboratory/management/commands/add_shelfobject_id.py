from django.core.management.base import BaseCommand
from laboratory.models import ShelfObject, ObjectLogChange


def add_shelf_object(self):
    queryset = ObjectLogChange.objects.all()
    for query in queryset:
        shelf_object = ShelfObject.objects.filter(
            object=query.object,
            measurement_unit=query.measurement_unit,
            quantity=query.new_value,
            in_where_laboratory=query.laboratory,
        ).first()
        if shelf_object:
            if shelf_object.object.is_precursor:
                query.shelf_object_id = shelf_object.pk
                query.save()
            else:
                query.shelf_object_id = shelf_object.pk
                query.save()


class Command(BaseCommand):

    help = "Add Shelf Object Id in ObjectLogChange"

    def handle(self, *args, **options):
        add_shelf_object()
