from django.core.management.base import BaseCommand
from laboratory.models import ShelfObject, ObjectLogChange



class Command(BaseCommand):

    help = "Add Shelf Object Id in ObjectLogChange"

    def update_shelf_object(self):
        queryset = ShelfObject.objects.filter(in_where_laboratory__pk=137,
                                              object__type=0,
                                              object__name__startswith="Vitek")
        for query in queryset:
            obj = query.container.object
            obj.name = f"Caja Vitek {obj.materialcapacity.capacity} {obj.materialcapacity.capacity_measurement_unit.description}"
            obj.save()
        containers = queryset.filter(container__object__materialcapacity__capacity=20.0)
        container = containers.first()
        container_sixty = containers.filter(container__object__materialcapacity__capacity=60.0).first()
        containers_delete = []
        for shelf_obj in containers:
            if container.pk != shelf_obj.container.pk:
                containers_delete.append(shelf_obj.container.pk)
                shelf_obj.container = container
                shelf_obj.save()

        container.save()
        ShelfObject.objects.filter(pk__in=containers_delete).delete()


    def handle(self, *args, **options):
        self.update_shelf_object()
