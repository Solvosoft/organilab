from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from laboratory.models import Object, OrganizationStructure, ObjectFeatures, \
    SustanceCharacteristics, Catalog
from sga.models import DangerPrudence, DangerIndication


class Command(BaseCommand):

    help = 'Move objects to una db'


    def transfer_users(self):
        users_una = User.objects.all().using("unadb")
        for user in users_una:
            u=User.objects.create_user(username=user.username, email=user.email,
                                     password=user.password,first_name=user.first_name,
                                     last_name=user.last_name,
                                     is_active=user.is_active,
                                     is_staff=user.is_staff,
                                     is_superuser=user.is_superuser,
                                       )
            u.user_permissions.add(*list(user.user_permissions.all().values_list("pk",flat=True)))
            u.save()

    def create_danger_indication(self, indication, database):
        danger_indication = DangerIndication.objects.filter(description=indication.description, code=indication.code).first()
        if not danger_indication:
            danger_indication = DangerIndication.objects.create(description=indication.description, code=indication.code).using(database)
            danger_indication.save()
            return danger_indication
        return None

    def create_danger_prudence(self, prudence, database):
        danger_prudence = DangerIndication.objects.filter(description=prudence.description, code=prudence.code).first()
        if not danger_prudence:
            danger_prudence = DangerPrudence.objects.create(description=prudence.description, code=prudence.code).using(database)
            danger_prudence.save()
            return danger_prudence
        return None

    def create_catalog(self, catalog, key, database):
        if not Catalog.objects.filter(key=key, description=catalog.description).exists():
            catalog = Catalog.objects.create(key=key, description=catalog.description).using(database)
            catalog.save()
            return catalog
        return None

    def transfer_objects_from_una_to_default(self, is_una, db_send, db_receive) :

        objects_data = Object.objects.using(db_send)
        orgs = None
        if is_una:
            orgs = OrganizationStructure.objects.using(db_receive).get(pk=1)
        else:
            orgs = OrganizationStructure.objects.using(db_receive).get(pk=104)
        count = 0
        for obj in objects_data:

            if not Object.objects.filter(code=obj.code, name=obj.name).using(db_receive).exists():

                new_obj = Object.objects.create(
                    name=obj.name,
                    code=obj.code,
                    synonym=obj.synonym,
                    type=obj.type,
                    is_public=obj.is_public,
                    model=obj.model,
                    place=obj.place,
                    serie=obj.serie,
                    description=obj.description,
                organization=orgs).using(db_receive)

                #Clona caracteristicas de objetos
                for feature in obj.features.all():
                    obj_fea= None
                    if ObjectFeatures.objects.filter(name=feature.name).using(db_receive).exists():
                        obj_fea = ObjectFeatures.objects.get(name=feature.name).using(db_receive)
                    else:
                        obj_fea = ObjectFeatures.objects.create(name=feature.name, description=feature.description).using(db_receive)
                    new_obj.features.add(obj_fea)

                #Clona sustancia caracteristicas
                if obj.type == "reactive":
                    sus_cara = SustanceCharacteristics.objects.filter(object=obj).using(db_send).first()
                    new_reactive_sus = SustanceCharacteristics.objects.create(object=new_obj).using(db_receive)
                    if sus_cara:
                        for indication in sus_cara.danger_indication.all():
                            danger_indication = self.create_danger_indication(indication, db_receive)
                            new_reactive_sus.danger_indication.add(danger_indication)
                        for prudence in sus_cara.danger_prudence:
                            danger_prudence = self.create_danger_prudence(prudence, db_receive)
                            new_reactive_sus.danger_prudence.add(danger_prudence)
                        if sus_cara.iarc:
                            iarc = self.create_catalog(sus_cara.iarc, "IARC", db_receive)
                            new_reactive_sus.iarc= iarc
                        if sus_cara.imdg:
                            imdg = self.create_catalog(sus_cara.imdg, "IDMG", db_receive)
                            new_reactive_sus.imdg= imdg

                        for storage in sus_cara.storage_class.all():
                            storage_class = self.create_catalog(storage, "storage_class", db_receive)
                            new_reactive_sus.storage_class.add(storage_class)

                        for nfpa in sus_cara.nfpa.all():
                            nfpa_data = self.create_catalog(nfpa, "nfpa", db_receive)
                            new_reactive_sus.nfpa.add(nfpa_data)

                        for white in sus_cara.white_organ.all():
                            white_organ = self.create_catalog(white, "nfpa", db_receive)
                            new_reactive_sus.white_organ.add(white_organ)

                        if sus_cara.precursor_type:
                            precursor_type = self.create_catalog(sus_cara.precursor_type, "precursor_type", db_receive)
                            new_reactive_sus.precursor_type=(precursor_type)
                        new_reactive_sus.save()

                    else:
                       SustanceCharacteristics.objects.create(object=new_obj).using(db_receive)

                new_obj.save()
                count+=1
                print(new_obj)

    def handle(self, *args, **options):
        self.transfer_users()
        self.transfer_objects_from_una_to_default(False, "unadb", "default")
        self.transfer_objects_from_una_to_default(True, "default", "unadb")
