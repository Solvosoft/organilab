import base64
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db.models import Q, Count
from django.core import serializers
from laboratory.models import SustanceCharacteristics, Object, Catalog
import json
from django.conf import settings

def load_security_sheet(data):
    with open(Path(settings.MEDIA_ROOT) / data, 'rb') as f:
        dev= base64.b64encode(f.read())
    return dev.decode()


def get_name_security_sheet(data):
    return data.replace('security_sheets/', '')

def get_obj(data):
    obj = serializers.serialize('json', [data])
    instances = json.loads(obj)
    return instances[0]

def get_catalog(data):
    dev = []
    if data:
        if isinstance(data, list):
            dev = list(Catalog.objects.filter(pk__in=data).values('key', 'description'))
        else:
            dev = list(Catalog.objects.filter(pk=data).values('key', 'description'))
    return dev

class Command(BaseCommand):
    """
    export Object
    """

    def handle(self, *args, **options):
        sustances = SustanceCharacteristics.objects.all().annotate(c=Count('h_code')).order_by('c')[900:]
        objs = Object.objects.filter(pk__in=sustances.values_list('obj', flat=True))

        #with open("objs.json", "w") as out:
        #    serializers.serialize('json', sustances, stream=out)

        data = serializers.serialize('json', sustances)

        instances = json.loads(data)
        new_instances = []
        for instance in instances:
            scha=SustanceCharacteristics.objects.get(pk=instance['pk'])

            instance['fields']['obj'] = get_obj(scha.obj)
            if instance['fields']['security_sheet']:
                instance['fields']['security_sheet_name'] = get_name_security_sheet(instance['fields']['security_sheet'])
                instance['fields']['security_sheet'] = load_security_sheet(instance['fields']['security_sheet'])
                instance['fields']['iarc'] = get_catalog(instance['fields']['iarc'])
                instance['fields']['imdg'] = get_catalog(instance['fields']['imdg'])

                instance['fields']['precursor_type'] = get_catalog(instance['fields']['precursor_type'])

                instance['fields']['white_organ'] = get_catalog(instance['fields']['white_organ'])  # M
                instance['fields']['ue_code'] = get_catalog(instance['fields']['ue_code'])
                instance['fields']['nfpa'] = get_catalog(instance['fields']['nfpa'])
                instance['fields']['storage_class'] = get_catalog(instance['fields']['storage_class'])

            new_instances.append(instance)


        with open('file.json', "w") as fi:
            fi.write(json.dumps(new_instances))


        #data = serializers.serialize('json', objs)
        print(sustances.count(), objs.count())