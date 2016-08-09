import random
from laboratory.models import LaboratoryRoom, ShelfObject
from laboratory.models import Object
from laboratory.models import ObjectFeatures
from laboratory.models import Furniture
from laboratory.models import Shelf


def create_laboratory_rooms():
    names = [
        'Information Window',
        'Scale room',
        'Laboratory'
    ]
    for name in names:
        LaboratoryRoom.objects.create(name=name)


def create_furniture(max=10):
    for i in range(0, max):
        Furniture.objects.create(
            labroom=random_model_object(LaboratoryRoom),
            name='Testing furniture number %s' % (i + 1),
            type=random_choice(Furniture.TYPE_CHOICES)[0]
        )


def create_shelf(max=10):
    for i in range(0, max):
        Shelf.objects.create(
            furniture=random_model_object(Furniture),
            type=random_choice(Shelf.TYPE_CHOICES)[0]
        )


def create_object_features(max=10):
    for i in range(0, max):
        ObjectFeatures.objects.create(
            name=random_choice(ObjectFeatures.CHOICES)[0],
            description='No description'
        )


def create_objects(max=10):
    for i in range(0, max):
        Object.objects.create(
            shelf=random_model_object(Shelf),
            type=random_choice(Object.TYPE_CHOICES)[0],
            code='object_number_%d' % (i + 1),
            description='Object description',
            name='Object number %d' % (i + 1)
        )


def create_shelf_objects(max=10):
    for i in range(0, max):
        ShelfObject.objects.create(
            object=random_model_object(Object),
            quantity=random.random() * 100,
            measurement_unit=random_choice((ShelfObject.CHOICES))[0]
        )


def clean_models():
    LaboratoryRoom.objects.all().delete()
    Furniture.objects.all().delete()
    Shelf.objects.all().delete()
    ObjectFeatures.objects.all().delete()
    Object.objects.all().delete()
    ShelfObject.objects.all().delete()


def random_choice(iterable):
    return random.choice(iterable)


def random_model_object(model):
    return model.objects.order_by('?').first()
