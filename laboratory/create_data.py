import random
from laboratory.models import LaboratoryRoom
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
            name='Testing furniture number %s' % (i+1),
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


def create_objects():
    pass


def create_shelf_objects():
    pass


def clean_models():
    LaboratoryRoom.objects.all().delete()
    Furniture.objects.all().delete()
    Shelf.objects.all().delete()


def random_choice(iterable):
    return random.choice(iterable)

def random_model_object(model):
    return model.objects.order_by('?').first()