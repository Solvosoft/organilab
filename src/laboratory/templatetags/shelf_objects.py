from laboratory.models import Laboratory, ShelfObject, Shelf
from django import template

register = template.Library()


@register.simple_tag
def get_shelfs(lab):
    objects = Shelf.objects.filter(furniture__labroom__laboratory=lab, discard=True,furniture__dataconfig__isnull=False).distinct()

    return objects

@register.simple_tag
def get_shelf_objects(shelf):
    objects = ShelfObject.objects.filter(shelf=shelf)
    return objects