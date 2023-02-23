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

@register.simple_tag
def get_lab_porcentage(lab):
    objects = Shelf.objects.filter(furniture__labroom__laboratory=lab, discard=True,furniture__dataconfig__isnull=False).distinct()
    amount=objects.count()
    porcentage = 0
    for obj in objects:
        porcentage+=obj.get_refuse_porcentage()
    try:
        porcentage = (porcentage / amount)
    except ZeroDivisionError:
        porcentage = 0
    return porcentage