import argparse
import base64
import json

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile

from laboratory.models import (
    Object,
    SustanceCharacteristics,
    OrganizationStructure,
    ObjectFeatures,
    Catalog,
)
from sga.models import DangerIndication


class Command(BaseCommand):
    """
    import Object
    """

    def get_sheet(self, data):
        if data["security_sheet"]:
            try:
                datab64 = base64.b64decode(data["security_sheet"])
                return ContentFile(datab64, name=data["security_sheet_name"])
            except Exception as e:
                return None

    def get_object(self, instance, org):
        orga = OrganizationStructure.objects.filter(pk=org[0]).first()
        fields = {}
        fields.update(instance["fields"]["obj"]["fields"])
        fields["organization"] = orga
        features = ObjectFeatures.objects.filter(pk__in=fields["features"])
        del fields["features"]
        obj = Object.objects.create(**fields)
        obj.features.add(*list(features))
        return obj

    def get_catalog(self, field, isfk):
        dev = None if isfk else []
        try:
            if field:
                for item in field:
                    if isinstance(item, int):
                        itc = Catalog.objects.get(pk=item)
                        dev.append(itc)
                    else:
                        itc, x = Catalog.objects.get_or_create(**item)
                        if isfk:
                            dev = itc
                            break
                        else:
                            dev.append(itc)
        except Exception as e:
            print(e)
        return dev

    def get_h_code(self, data):
        dev = []
        for x in data:

            di = DangerIndication.objects.filter(code=x).first()
            if di:
                dev.append(di)
        return dev

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("org_pk", nargs="+", type=int)
        parser.add_argument("json_file", nargs="+", type=argparse.FileType())

    def handle(self, *args, **options):
        for files in options["json_file"]:
            elements = json.load(files)
            for instance in elements:
                instance["fields"]["obj"] = self.get_object(instance, options["org_pk"])
                instance["fields"]["security_sheet"] = self.get_sheet(
                    instance["fields"]
                )
                if "security_sheet_name" in instance["fields"]:
                    del instance["fields"]["security_sheet_name"]

                instance["fields"]["iarc"] = self.get_catalog(
                    instance["fields"]["iarc"], True
                )
                instance["fields"]["imdg"] = self.get_catalog(
                    instance["fields"]["imdg"], True
                )
                instance["fields"]["precursor_type"] = self.get_catalog(
                    instance["fields"]["precursor_type"], True
                )

                white_organ = self.get_catalog(
                    instance["fields"]["white_organ"], False
                )  # M
                ue_code = self.get_catalog(instance["fields"]["ue_code"], False)
                nfpa = self.get_catalog(instance["fields"]["nfpa"], False)
                storage_class = self.get_catalog(
                    instance["fields"]["storage_class"], False
                )
                h_code = self.get_h_code(instance["fields"]["h_code"])

                del instance["fields"]["white_organ"]
                del instance["fields"]["ue_code"]
                del instance["fields"]["nfpa"]
                del instance["fields"]["storage_class"]
                del instance["fields"]["h_code"]

                createdinstance = SustanceCharacteristics.objects.create(
                    **instance["fields"]
                )

                createdinstance.white_organ.add(*white_organ)
                createdinstance.ue_code.add(*ue_code)
                createdinstance.nfpa.add(*nfpa)
                createdinstance.storage_class.add(*storage_class)
                createdinstance.h_code.add(*h_code)
