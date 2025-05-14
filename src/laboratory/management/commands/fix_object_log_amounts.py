from django.contrib.admin.models import ADDITION, CHANGE
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils.timezone import now
from laboratory.models import ShelfObject, ObjectLogChange, Catalog, Laboratory, Object
from django.utils.translation import gettext_lazy as _

class Command(BaseCommand):

    help = 'Add Shelf Object Id in ObjectLogChange'

    def set_objects(self):

        laboratories = Laboratory.objects.all()
        units = Catalog.objects.filter(key='units')
        user = User.objects.get(pk=936)

        for laboratory in laboratories:

            for unit in units:
                objs = ShelfObject.objects.filter(object__type=0, measurement_unit=unit,
                                               in_where_laboratory=laboratory).values_list(
                        "object", flat=True)
                objs = Object.objects.filter(pk__in=objs).distinct()
                for obj in objs:

                    objects = ObjectLogChange.objects.filter(object=obj,
                                                             measurement_unit=unit,
                                                             laboratory=laboratory)
                    shelfobject_total = \
                    ShelfObject.objects.filter(object=obj, measurement_unit=unit,
                                               in_where_laboratory=laboratory).aggregate(
                        total=Sum('quantity', default=0))['total']
                    is_precuror = obj.is_precursor
                    obj_total = objects.aggregate(total=Sum('diff_value', default=0))['total']
                    objects = objects.last()
                    attrw= dict(
                        object=obj,
                        laboratory=laboratory,
                        user=user,
                        old_value=objects.new_value,
                        new_value=objects.new_value - shelfobject_total,
                        diff_value=shelfobject_total,
                        update_time=now(),
                        measurement_unit=unit,
                        precursor=is_precuror,
                        subject= _("Adjustment quantities in logs"),
                        type_action=CHANGE,
                        note=_("Adjustment quantities in logs"),
                        organization_where_action_taken=laboratory.organization
                    )

                    if objects.new_value < shelfobject_total:
                        attrw['new_value'] = shelfobject_total
                        attrw['diff_value'] = shelfobject_total - objects.new_value
                        attrw['type_action'] = ADDITION
                    if objects.new_value > shelfobject_total or objects.new_value < shelfobject_total:
                        ObjectLogChange.objects.create(**attrw)
                    if obj.name == "Hexano":
                        print(shelfobject_total, obj_total)

    def handle(self, *args, **options):
        self.set_objects()
