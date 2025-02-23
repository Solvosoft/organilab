import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db.models import F

from auth_and_perms.models import Rol, Profile, ProfilePermission
from auth_and_perms.views.user_org_creation import set_rol_administrator_on_org
from laboratory.models import Object, OrganizationStructure, ObjectFeatures, \
    SustanceCharacteristics, Catalog, Laboratory, LaboratoryRoom, Furniture, Shelf, \
    ShelfObject
from laboratory.utils import register_laboratory_contenttype
from risk_management.models import RiskZone, ZoneType
from sga.models import DangerPrudence, DangerIndication
from django.db import connections

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
            Profile.objects.create(
                user=u,
                phone_number='2277-3000',
                id_card = '88888888',
                job_position = 'Gestor de organilab'
            )
        self.user = User.objects.filter(username=settings.DEFAULT_MIGRATION_USER).first()

    def transfer_organizations(self):
        names=list(OrganizationStructure.objects.using('unadb').all().order_by('id').values_list('name', flat=True))
        parent_name = names.pop(0)
        parent = OrganizationStructure.objects.create(name=parent_name)
        [parent.users.add(x) for x in User.objects.all()]
        for i, name in enumerate(names):
            org=OrganizationStructure.objects.create(name=name, parent=parent, position=i+1)
            set_rol_administrator_on_org(self.user.profile, org)

    def create_roles(self):
        parent = OrganizationStructure.objects.filter(name='UNA').first()

        for name in ['Solo Lectura', 'Lectura y agregado de sustancias', 'Técnico de Laboratorio',
                     'Regente', 'Estudiante', 'Profesor','Asistente de laboratorio', 'Administrativo superior']:
            r=Rol.objects.create(name=name)
            parent.rol.add(r)

    def create_laboratories(self):
        labs = Laboratory.objects.using('unadb').annotate(parent_name=F('organization__name')).values(
            'parent_name', 'organization', 'name', 'geolocation', 'location', 'phone_number' )
        parent_org = OrganizationStructure.objects.filter(name='UNA').first()
        for lab in labs:
            # todos los laboratorios pertenecen a la UNA, pero están relacionados a las otras organizaciones.
            newlab=Laboratory.objects.create(
                name=lab['name'],
                phone_number = lab['phone_number'],
                location = lab['location'],
                geolocation =  lab['geolocation'],
                email = 'labs@una.cr',
                coordinator = '',
                unit = '',
                organization = parent_org,
                created_by=self.user)
            org = OrganizationStructure.objects.filter(name=lab['parent_name']).first()
            register_laboratory_contenttype(org, newlab)
            register_laboratory_contenttype(parent_org, newlab)
            for user in User.objects.all():
                pp = ProfilePermission.objects.create(
                    profile=user.profile,
                    content_type=ContentType.objects.get_for_model(Laboratory),
                    object_id=newlab.pk
                )

    def create_laboratory_room(self):

        sql = '''SELECT r.id, l.name, r.laboratoryroom_id, lr.name  FROM public.laboratory_laboratory_rooms as r
join public.laboratory_laboratory as l on l.id = r.laboratory_id
join public.laboratory_laboratoryroom as lr on lr.id = r.laboratoryroom_id
ORDER BY r.id ASC '''

        with connections["unadb"].cursor() as cursor:
            cursor.execute(sql)
            for data in cursor.fetchall():
                lab=Laboratory.objects.filter(name=data[1]).first()
                labroom = LaboratoryRoom.objects.create(laboratory=lab,  name=data[3], created_by=self.user)
                self.labrooms[data[2]]=labroom

    def get_dataconfig(self, data, furniture):
        dd=json.loads(data)
        dataconfig=[]
        for r in dd:
            rl=[]
            for c in r:
                l=[]
                for item in c:
                    unashelf = Shelf.objects.using('unadb').filter(pk=item).values('type_id', 'furniture_id', 'name', 'id')
                    s = Shelf.objects.create(
                        created_by=self.user,
                        furniture=furniture,
                        name=unashelf[0]['name'],
                        type=Catalog.objects.filter(id=unashelf[0]['type_id']).first(),
                    )
                    self.shelfs[unashelf[0]['id']]=s
                    l.append(s.pk)
                rl.append(l)
        dataconfig.append(rl)
        return json.dumps(dataconfig)

    def create_furniture(self):
        furnitures = Furniture.objects.using('unadb').values('id', 'name', 'type_id', 'labroom_id', 'dataconfig')
        for furn in furnitures:
            catalog = Catalog.objects.filter(id=furn['type_id']).first()
            if furn['labroom_id'] in self.labrooms:
                f=Furniture.objects.create(
                    name=furn['name'],
                    labroom=self.labrooms[furn['labroom_id']],
                    type=catalog,
                    dataconfig=''
                )
                f.dataconfig=self.get_dataconfig(furn['dataconfig'], f)
                f.save()
            else:
                # print(furn)
                pass

    def get_una_file(self, path):
        if path:
            path =Path(settings.MEDIA_UNA_ROOT +"/" + path)
            nfile = open(path, 'rb')
            return File(nfile, name=path.name)

    def get_or_create_catalog(self, cat_id, key_value, using='unadb'):
        unacat = Catalog.objects.using(using).filter(key=key_value, pk=cat_id).values('description')
        newcat, created = Catalog.objects.get_or_create(key=key_value, description=unacat[0]['description'])
        return newcat

    def process_white_organ(self, sus_cara_id, obj):
        sql = '''SELECT wo.catalog_id, sc.id, lc.description FROM public.laboratory_sustancecharacteristics_white_organ as wo
join public.laboratory_sustancecharacteristics as sc on wo.sustancecharacteristics_id = sc.id
join public.laboratory_catalog as lc on lc.id=wo.catalog_id
where sc.id = %s
ORDER BY id ASC
        '''%(sus_cara_id,)

        with connections["unadb"].cursor() as cursor:
            cursor.execute(sql)
            for data in cursor.fetchall():
                cat = Catalog.objects.filter(description=data[2]).first()
                if cat is None:
                    cat = self.get_or_create_catalog(data[0], 'white_organ')

                obj.white_organ.add(cat)

    def process_danger_indication(self, sus_id, obj):
        di=DangerIndication.objects.using('unadb').filter(sustancecharacteristics=sus_id)
        for d in di:
            idi=DangerIndication.objects.get(code=d.code)
            obj.h_code.add(idi)
    def process_ue_code(self, sus_id, obj):
        sql = '''
        SELECT lc.description, ue.catalog_id FROM public.laboratory_sustancecharacteristics_ue_code as ue
 join public.laboratory_catalog as lc on lc.id=ue.catalog_id
    where ue.sustancecharacteristics_id = %s
        '''%(sus_id,)

        with connections["unadb"].cursor() as cursor:
            cursor.execute(sql)
            for data in cursor.fetchall():
                cat = Catalog.objects.filter(key="ue_code", description=data[0]).first()
                if cat is None:
                    cat = self.get_or_create_catalog(data[1], 'ue_code')
                obj.ue_code.add(cat)

    def process_nfpa(self, sus_id, obj):
        sql = '''
           SELECT lc.description, ue.catalog_id FROM public.laboratory_sustancecharacteristics_nfpa as ue
            join public.laboratory_catalog as lc on lc.id=ue.catalog_id
            where ue.sustancecharacteristics_id = %s
           ''' % (sus_id,)

        with connections["unadb"].cursor() as cursor:
            cursor.execute(sql)
            for data in cursor.fetchall():
                cat = Catalog.objects.filter(key="nfpa", description=data[0]).first()
                if cat is None:
                    cat = self.get_or_create_catalog(data[1], 'nfpa')
                obj.nfpa.add(cat)

    def process_storage_class(self, sus_id, obj):
        sql = '''
           SELECT lc.description, ue.catalog_id FROM public.laboratory_sustancecharacteristics_storage_class as ue
            join public.laboratory_catalog as lc on lc.id=ue.catalog_id
            where ue.sustancecharacteristics_id = %s
           ''' % (sus_id,)

        with connections["unadb"].cursor() as cursor:
            cursor.execute(sql)
            for data in cursor.fetchall():
                cat = Catalog.objects.filter(key="storage_class", description=data[0]).first()
                if cat is None:
                    cat = self.get_or_create_catalog(data[1], 'storage_class')
                obj.storage_class.add(cat)

    def transfer_sustancecharacteristics(self, obj, old_id):
        substances=SustanceCharacteristics.objects.using('unadb').filter(obj_id=old_id).values(
            'id', 'bioaccumulable', 'molecular_formula', 'cas_id_number',
            'security_sheet', 'is_precursor',
            'iarc_id', 'precursor_type_id', 'valid_molecular_formula', 'seveso_list',
            'imdg_id'
        )
        for subs in substances:
            sc=SustanceCharacteristics.objects.create(
                id=subs['id'],
                obj=obj,
                bioaccumulable=subs['bioaccumulable'],
                molecular_formula=subs['molecular_formula'],
                cas_id_number=subs['cas_id_number'],
                security_sheet=self.get_una_file(subs['security_sheet']),
                is_precursor=subs['is_precursor'],
                valid_molecular_formula=subs['valid_molecular_formula'],
                seveso_list=subs['seveso_list']
            )
            if subs['iarc_id']:
                sc.iarc=self.get_or_create_catalog(subs['iarc_id'], "IARC")
            if subs['imdg_id']:
                sc.imdg=self.get_or_create_catalog(subs['imdg_id'], "IDMG")
            if subs['precursor_type_id']:
                sc.precursor_type = self.get_or_create_catalog(subs['precursor_type_id'],
                                                               "Precursor"
                                                               )
            self.process_white_organ(subs['id'], sc)
            self.process_danger_indication(subs['id'], sc)
            self.process_ue_code(subs['id'], sc)
            self.process_nfpa(subs['id'], sc)
            self.process_storage_class(subs['id'], sc)

            sc.save()

    def transfer_una_object(self):
        objs = Object.objects.using('unadb').values(
            'id', 'type', 'code', 'description', 'name', 'model',
            'plaque', 'serie', 'is_public', 'synonym')
        for obj in objs:
            #features
            o=Object.objects.create(
                organization=OrganizationStructure.objects.filter(name='UNA').first(),
                id=obj['id'],
                code=obj['code'],
                name = obj['name'],
                synonym = obj['synonym'],
                type = obj['type'],
                is_public = obj['is_public'],
                description = obj['description'],
                model = obj['model'],
                serie = obj['serie'],
                plaque = obj['plaque'],
                is_container = False
            )
            self.transfer_sustancecharacteristics(o, obj['id'])
            self.objects[obj['id']] = o
    def migrate_shelfobject(self):
        su=ShelfObject.objects.using('unadb').all().values(
            'quantity', 'measurement_unit_id', 'object_id', 'shelf_id', 'limit_quantity')
        for s in su:
            ShelfObject.objects.create(
                shelf=self.shelfs[s['shelf_id']],
                object=self.objects[s['object_id']],
                quantity=s['quantity'],
                limit_quantity=s['limit_quantity'],
                measurement_unit=self.get_or_create_catalog(s['measurement_unit_id'],
                                                            'units'),
                in_where_laboratory=self.shelfs[s['shelf_id']].furniture.labroom.laboratory
            )
    def create_risk_zone(self):
        zu=ZoneType.objects.using('unadb').values('id', 'name')
        ZoneType.objects.all().delete()
        for z in zu:
            ZoneType.objects.get_or_create(pk=z['id'], name=z['name'])
        rz=RiskZone.objects.create(
            organization=OrganizationStructure.objects.filter(name='UNA').first(),
            name='UNA',
            num_workers =  1700,
            zone_type = ZoneType.objects.all().first(),
            priority = 1
        )
        for lab in Laboratory.objects.all():
            rz.laboratories.add(lab)
    def init_data(self):
        OrganizationStructure.objects.all().delete() # remove test organization
        Object.objects.all().delete()
        self.transfer_users()
        self.transfer_organizations()
        self.create_roles()
        self.create_laboratories()
        self.user.set_password('admin12345')
        self.user.save()
        self.create_laboratory_room()
        self.create_furniture()
        self.transfer_una_object()
        self.migrate_shelfobject()

    def handle(self, *args, **options):
        self.user=None
        self.labrooms = {}
        self.shelfs={}
        self.objects = {}

        #self.init_data()
        self.create_risk_zone()
