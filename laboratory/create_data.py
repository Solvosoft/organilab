import random
from laboratory.models import LaboratoryRoom, ShelfObject
from laboratory.models import Object
from laboratory.models import ObjectFeatures
from laboratory.models import Furniture
from laboratory.models import Shelf

FURNITURE_LIST = [
    'Coat wardrobe',
    'White metal shelf',
    'Stationary metal shelf',
    'Centre office table',
    'Roller filling unit',
    'Desk',
    'Bookcase',
    'Radiator',
    'Open-shelf screen',
    'Filing cabinet'
]

LABORATORY_OBJECTS_LIST = [
    'Compound microscope',
    'Cover slip',
    'Glass slide',
    'Magnifying glass',
    'Hand lens',
    'Simple microscope',
    'Graduated cylinders',
    'Beaker',
    'Beaker tongs',
    'Florence flask'
    'Erlenmeyer flask',
    'Rubber stoppers',
    'Test tube',
    'Test tube rack',
    'Test tube holder',
    'Test tube brush',
    'Funnel',
    'Petri dish',
    'Meter stick',
    'Eye dropper',
    'Triple beam balance',
    'Thermometer',
    'Safety goggles',
    'Test tube clamp',
    'Ring stand'
]

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
            name=random_choice(FURNITURE_LIST),
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
        obj = Object.objects.create(
            shelf=random_model_object(Shelf),
            type=random_choice(Object.TYPE_CHOICES)[0],
            code='object_number_%d' % (i + 1),
            description='Object description',
            name=random_choice(LABORATORY_OBJECTS_LIST)
        )

        times = random.randint(0,3)
        for time in range(0, times):
            obj.features.add(random_model_object(ObjectFeatures))
        obj.save()


def create_shelf_objects(max=10):
    for i in range(0, max):
        ShelfObject.objects.create(
            object=random_model_object(Object),
            quantity=random.random() * 100,
            measurement_unit=random_choice((ShelfObject.CHOICES))[0]
        )

def create_data(max=100):
    clean_models()
    create_laboratory_rooms()
    create_furniture(max)
    create_shelf(max)
    create_object_features(max)
    create_objects(max)
    create_shelf_objects(max)


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
