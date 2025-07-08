import json
from pathlib import Path

from django.apps import apps
from django.apps.registry import Apps
from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db.models import F

from auth_and_perms.models import Rol, Profile, ProfilePermission
from auth_and_perms.views.user_org_creation import set_rol_administrator_on_org
from derb.models import CustomForm
from laboratory.models import Object, OrganizationStructure, ObjectFeatures, \
    SustanceCharacteristics, Catalog, Laboratory, LaboratoryRoom, Furniture, Shelf, \
    ShelfObject, ObjectLogChange, UserOrganization, MaterialCapacity, \
    EquipmentCharacteristics, ShelfObjectMaintenance, ShelfObjectLog, \
    ShelfObjectCalibrate, ShelfObjectGuarantee, ShelfObjectTraining, \
    ShelfObjectObservation, BaseUnitValues, TranferObject, ShelfObjectLimits, \
    RegisterUserQR, LabOrgLogEntry, PrecursorReport, PrecursorReportValues, Inform, \
    InformScheduler
from laboratory.utils import register_laboratory_contenttype
from risk_management.models import RiskZone, ZoneType, PriorityConstrain, Buildings, \
    Regent
from sga.models import DangerPrudence, DangerIndication
from django.db import connections

class Command(BaseCommand):

    help = 'Move objects to una db'

    def transfer_many_categories(self, cats, key):
        for cat in cats:
            self.get_or_create_catalog(cat['id'], key)

    def get_una_file(self, path):
        if path:
            path =Path(settings.MEDIA_UNA_ROOT +"/" + path)
            nfile = open(path, 'rb')
            return File(nfile, name=path.name)

    def process_objectfeatures(self):
        ob = ObjectFeatures.objects.using('organilabprod').all()
        for o in ob:
            ObjectFeatures.objects.get_or_create(
                name=o.name,
                description=o.description
            )

    def get_or_create_catalog(self, cat_id, key_value, using='organilabprod'):
        unacat = Catalog.objects.using(using).filter(key=key_value, pk=cat_id).values('description')
        newcat, created = Catalog.objects.get_or_create(key=key_value, description=unacat[0]['description'])
        return newcat

    def create_base_units(self):
        units = BaseUnitValues.objects.using('organilabprod').all()
        for u in units:
            BaseUnitValues.objects.create(
                measurement_unit_base=self.get_or_create_catalog(u.measurement_unit_base.description,
                                                                    'units'),
                measurement_unit=self.get_or_create_catalog(u.measurement_unit.description,
                                                                    'units'),
                si_value=u.si_value
            )
    def transfer_sustancecharacteristics(self, obj, old_id):
        substances=SustanceCharacteristics.objects.using('organilabprod').filter(obj_id=old_id).distinct('id')
        for subs in substances:
            sc=SustanceCharacteristics.objects.create(
                obj=obj,
                bioaccumulable=subs.bioaccumulable,
                molecular_formula=subs.molecular_formula,
                cas_id_number=subs.molecular_formula,
                security_sheet=self.get_una_file(subs.security_sheet),
                is_precursor=subs.is_precursor,
                valid_molecular_formula=subs.valid_molecular_formula,
                seveso_list=subs.seveso_list
            )
            if subs['iarc_id']:
                sc.iarc=self.get_or_create_catalog(subs.iarc.pk, "IARC")
            if subs['imdg_id']:
                sc.imdg=self.get_or_create_catalog(subs.imdg.pk, "IDMG")
            if subs['precursor_type_id']:
                sc.precursor_type = self.get_or_create_catalog(subs.precursor_type.pk,
                                                               "Precursor"
                                                               )
            self.transfer_many_categories(subs['id'],
                                          sc.white_organ.all().values_list('pk', flat=True))
            self.transfer_many_categories(subs['id'],
                                          sc.h_code.all().values_list('pk', flat=True))
            self.transfer_many_categories(subs['id'],
                                          sc.ue_code.all().values_list('pk', flat=True))
            self.transfer_many_categories(subs['id'],
                                          sc.nfpa.all().values_list('pk', flat=True))
            self.transfer_many_categories(subs['id'],
                                          sc.storage_class.all().values_list('pk', flat=True))

            sc.save()
    def create_material_capacity(self, obj, capacity, unit):
        MaterialCapacity.objects.create(
            object=obj,
            capacity=capacity,
            capacity_measurement_unit=Catalog.objects.get(description=unit, key='units')
        )

    def transfer_features(self, old, new):
        for feature in old.features.all():
            of = ObjectFeatures.objects.filter(name=feature.name).first()
            if of:
                new.features.add(of)

    def transfer_objects(self, organization):
        objs = Object.objects.using('organilabprod').all()
        for obj in objs:
            threshold = True if obj['type']==0 else False
            o=Object.objects.create(
                organization=organization,
                code=obj.code,
                name = obj.name,
                synonym = obj.synonym,
                type = obj.type,
                is_public = obj.is_public,
                description = obj.descripcion,
                model = obj.model,
                serie = obj.serie,
                plaque = obj.plaque,
                is_container = obj.is_container,
                has_threshold = threshold
            )
            if obj.type == Object.MATERIAL:
                if hasattr(obj, 'material_capacity'):
                    self.create_material_capacity(o, obj.material_capacity.capacity,
                                                  obj.material_capacity.capacity_measurement_unit.description)

            self.transfer_sustancecharacteristics(o, obj)
            self.objects[obj.pk] = o
            self.transfer_features(obj, o)

    def shelfobject_equipment(self, old_shelfobject,shelf_object):
        equipment = EquipmentCharacteristics.objects.using('organilabprod').filter(shelfobject=old_shelfobject)
        for e in equipment:
            equipment=EquipmentCharacteristics.objects.create(
                shelfobject=shelf_object,
                equipment_price = e.equipment_price,
                purchase_equipment_date = e.purchase_equipment_date,
                delivery_equipment_date = e.delivery_equipment_date,
                have_guarantee = e.have_guarantee,
                contract_of_maintenance = self.get_una_file(e.contract_of_maintenance),
                notes = e.notes,
                available_to_use = e.available_to_use,
                first_date_use = e.first_date_use,
                organization = shelf_object.in_where_laboratory.organization,
             )
            if e.authorized_roles_to_use_equipment:
                for ro in e.authorized_roles_to_use_equipment.all():
                    rol, created = Rol.objects.get_or_create(
                        name=ro.name,
                        color=ro.color
                    )
                    equipment.authorized_roles_to_use_equipment.add(rol)

    def create_equipment_maintenance(self, old_shelfobject,shelf_object):
        maintenance = ShelfObjectMaintenance.objects.using('organilabprod').filter(shelfobject=old_shelfobject)
        for m in maintenance:
            maintenance=ShelfObjectMaintenance.objects.create(
                shelfobject=shelf_object,
                maintenance_date = m.maintenance_date,
                #validator = m.validator,
                maintenance_observation = m.maintenance_observation,
                organization = shelf_object.in_where_laboratory.organization,
            )

    def create_equipment_Log(self, old_shelfobject,shelf_object):
        log = ShelfObjectLog.objects.using('organilabprod').filter(shelfobject=old_shelfobject)
        for l in log:
            ShelfObjectLog.objects.create(
                shelfobject=shelf_object,
                description = l.description,
                orgsnization = shelf_object.in_where_laboratory.organization
            )
    def create_equiment_calibrate(self, old_shelfobject,shelf_object):
        calibrate = ShelfObjectCalibrate.objects.using('organilabprod').filter(shelfobject=old_shelfobject)
        for c in calibrate:
            ShelfObjectCalibrate.objects.create(
                shelfobject=shelf_object,
                observation = c.observation,
                calibrate_name = c.calibrate_name,
                validator = c.validator,
                calibration_date = c.calibration_date,
                organization = shelf_object.in_where_laboratory.organization
            )

    def create_equipment_guarentee(self, old_shelfobject,shelf_object):
        guarantee = ShelfObjectGuarantee.objects.using('organilabprod').filter(shelfobject=old_shelfobject)
        for g in guarantee:
            ShelfObjectGuarantee.objects.create(
                shelfobject=shelf_object,
                guarantee_initial_date = g.guarantee_initial_date,
                guarantee_final_date = g.guarantee_final_date,
                contract = self.get_una_file(g.contract),
                organization = shelf_object.in_where_laboratory.organization
            )
    def create_equipment_training(self, old_shelfobject,shelf_object):
        trainings = ShelfObjectTraining.objects.using('organilabprod').filter(shelfobject=old_shelfobject)
        for t in trainings:
            training = ShelfObjectTraining.objects.create(
                shelfobject=shelf_object,
                initial_date = t.initial_date,
                final_date = t.final_date,
                number_of_hours = t.number_of_hours,
                external_people_receive_training = t.external_people_receive_training,
                observation = t.observation,
                place = t.place,
                organization = shelf_object.in_where_laboratory.organization
            )
            if training.intern_people_receive_training:
                for i in training.intern_people_receive_training.all():
                    rol, created = Rol.objects.get_or_create(
                        name=i.name,
                        color=i.color
                    )
                    training.intern_people_receive_training.add(rol)

    def create_shelfobject_observation(self, old_shelfobject,shelf_object):
        observation = ShelfObjectObservation.objects.using('organilabprod').filter(shelfobject=old_shelfobject)
        for o in observation:
            user = None
            if o.created_by:
                user = User.objects.filter(username=o.created_by.username).first()
            ShelfObjectObservation.objects.create(
                shelfobject=shelf_object,
                action_taken = o.action_taken,
                description = o.description,
                organization = shelf_object.in_where_laboratory.organization,
                created_by = user,
                creation_date = o.creation_date,
                last_update = o.last_update,
            )

    def create_shelfobject_limits(self, limit):
        new_limit = None
        if limit:
            new_limit = ShelfObjectLimits.objects.create(
            minimum_limit=limit.minimum_limit,
            maximum_limit=limit.maximum_limit,
            expiration_date=limit.expiration_date
            )
        return new_limit

    def create_shelfobject_material(self, organization):
        su=ShelfObject.objects.using('organilabprod').filter(in_where_laboratory__organization=organization, object__type=Object.MATERIAL)
        for s in su:
            lab=None
            if s.in_where_laboratory:
                lab = Laboratory.objects.filter(name= s.in_where_laboratory.name).first()
            shelf_object = ShelfObject.objects.create(
                shelf=self.shelfs[s.shelf.pk],
                object=self.objects[s.object.pk],
                quantity=s.quantity,
                quantity_base_unit = s.quantity_base_unit,
                measurement_unit=self.get_or_create_catalog(s.measurement_unit.description,
                                                            'units'),
                in_where_laboratory=lab,
                batch=s.batch,
                status=s.status,
                mark_as_discard=s.mark_as_discard,
                description=s.description,
                creation_date=s.creation_date,
                last_update=s.last_update,
            )
            self.create_shelfobject_observation(s,shelf_object)

    def migrate_shelfobject(self, old_organization):
        su=(ShelfObject.objects.using('organilabprod').filter(in_where_laboratory__organization=old_organization).
            exclude(object__type=Object.MATERIAL))
        for s in su:
            lab = None
            if s.in_where_laboratory:
                lab = Laboratory.objects.filter(name= s.in_where_laboratory.name).first()
            shelf_object = ShelfObject.objects.create(
                shelf=self.shelfs[s.shelf.pk],
                object=self.objects[s.object.pk],
                quantity=s.quantity,
                quantity_base_unit = s.quantity_base_unit,
                measurement_unit=self.get_or_create_catalog(s.measurement_unit.description,
                                                            'units'),
                in_where_laboratory=lab,
                batch=s.batch,
                status=s.status,
                mark_as_discard=s.mark_as_discard,
                description=s.description,
                creation_date=s.creation_date,
                last_update=s.last_update,
                physical_status=s.physical_status,
                concentration=s.concentration
            )
            self.create_shelfobject_observation(s,shelf_object)
            if s.object.type == Object.REACTIVE:
                shelf_object.limits = self.create_shelfobject_limits(s.limits)
                container = ShelfObject.objects.filter(shelf=shelf_object.shelf, object=s.object.container)
            if s.object.type == Object.EQUIPMENT:
                self.shelfobject_equipment(s,shelf_object)
                self.create_equipment_maintenance(s,shelf_object)
                self.create_equiment_calibrate(s,shelf_object)
                self.create_equipment_guarentee(s,shelf_object)
                self.create_equipment_training(s,shelf_object)

            shelf_object.save()

    def create_transfer_objects(self, old_organization):
        transfer=TranferObject.objects.using('organilabprod').filter(laboratory_send__organization=old_organization)
        for t in transfer:
            user = None
            lab_send = None
            lab_received = None
            if t.laboratory_send:
                lab_send = Laboratory.objects.filter(name=t.laboratory_send.name).first()
            if t.laboratory_received:
                lab_received = Laboratory.objects.filter(name=t.laboratory_received.name).first()
            if t.created_by:
                user = User.objects.filter(username=t.created_by.username).first()
            TranferObject.objects.create(
                    object=self.objects[t.object.pk],
                    laboratory_send=lab_send,
                    laboratory_received=lab_received,
                    quantity=t.quantity,
                    update_time=t.update_time,
                    state=t.state,
                    status=t.status,
                    mark_as_discard=t.mark_as_discard,
                    created_by=user,
                    creation_date=t.creation_date,
                    last_update=t.last_update,
                )


    def transfer_users(self):
        users_prod = User.objects.using('organilabprod').all()
        for user in users_prod:
            if not User.objects.filter(username=user.username).exists():
                u, created =User.objects.get_or_create(username=user.username, email=user.email,
                                         password=user.password,first_name=user.first_name,
                                         last_name=user.last_name,
                                         is_active=user.is_active,
                                         is_staff=user.is_staff,
                                         is_superuser=user.is_superuser,
                                           )
                u.user_permissions.add(*list(user.user_permissions.all().values_list("pk",flat=True)))
                u.save()
                if hasattr(user, 'profile'):
                    profile = Profile.objects.using('organilabprod').filter(user=u).first()
                    Profile.objects.create(
                        user=u,
                        phone_number=profile.phone_number,
                        id_card = profile.id_card,
                        job_position = profile.job_position,
                        language = profile.language
                    )
                else:
                    Profile.objects.get_or_create(
                        user=u,
                        phone_number='2277-3000',
                        id_card = '88888888',
                        job_position = 'Gestor de organilab'
                    )
        self.user = User.objects.filter(username=settings.DEFAULT_MIGRATION_USER).first()


    def add_users_in_organizations(self,users, organization):
        for user in users:
            if not UserOrganization.objects.filter(user=user, organization=organization).exists():
                UserOrganization.objects.create(user=user, organization=organization, status=True, type_in_organization=UserOrganization.LABORATORY_USER)

    def transfer_organizations(self, organization):
        self.organizations = {}
        organization_una= OrganizationStructure.objects.get(name='UNA')
        level = organization.level
        orga = {"name": organization.name, "position": organization.position, "level": level}
        if level == 0:
            orga["parent"] = organization_una
            new_org = OrganizationStructure.objects.create(**orga)
            self.organization = new_org
        else:
            orga["parent"] = self.organization
            new_org = OrganizationStructure.objects.create(**orga)
        level += 1
        self.organizations[organization.pk] = new_org
        set_rol_administrator_on_org(self.user.profile, new_org)
        users = [user for user in organization.users.all().values_list('username', flat=True)]
        self.add_users_in_organizations(User.objects.filter(username__in=users),organization_una)

    def transfer_rols(self):
        rols = Rol.objects.using('organilabprod').all()
        for rol in rols:
            obj, created = Rol.objects.get_or_create(
                name=rol.name,
                color=rol.color
            )
            if created:
                obj.permissions.add(*list(rol.permissions.all().values_list("pk",flat=True)))
                obj.save()

    def create_laboratory_rooms(self, rooms,laboratory,):
        for room in rooms:
            labroom = LaboratoryRoom.objects.create(laboratory=laboratory,  name=room.name, created_by=self.user)
            self.labrooms[room.pk] = labroom

    def get_dataconfig(self, data, furniture):
        dd=json.loads(data)
        dataconfig=[]
        for r in dd:
            rl=[]
            for c in r:
                l=[]
                for item in c:
                    unashelf = Shelf.objects.using('organilabprod').filter(pk=item)
                    shelf_type, created = Catalog.objects.get(description=unashelf.type.name,key="container_type" )
                    container_shelf = None
                    if unashelf.container_shelf:
                        container_shelf = Shelf.objects.filter(pk=unashelf.container_shelf.name, funiture=furniture).first()
                    s = Shelf.objects.create(
                        created_by=self.user,
                        furniture=furniture,
                        name=unashelf.name,
                        color = unashelf.color,
                        type=self.get_or_create_catalog(unashelf.type.description,
                                                                    'container_type'),
                        quantity=unashelf.quantity,
                        measurement_unit=self.get_or_create_catalog(unashelf.measurement_unit.description,
                                                                    'units'),
                        discard=unashelf.discard,
                        container_shelf= container_shelf,
                        description=unashelf.description,
                        infinity_quantity=unashelf.infinity_quantity,
                        limit_only_objects=unashelf.limit_only_objects
                    )
                    if unashelf.limit_only_objects:
                        s.available_objects_when_limit.add(unashelf.available_objects_when_limit.all().values_list('pk', flat=True))
                        s.save()
                    self.shelfs[unashelf.pk]=s
                    l.append(s.pk)
                rl.append(l)
        dataconfig.append(rl)
        return json.dumps(dataconfig)

    def create_furniture(self,organization):
        furnitures = Furniture.objects.using('organilabprod').filter(labroom__laboratory__organization=organization)
        for furn in furnitures:
            catalog = Catalog.objects.filter(description=furn.type.name,key="furniture_type" ).first()
            if furn.labroom_id in self.labrooms:
                f=Furniture.objects.create(
                    name=furn.name,
                    labroom=self.labrooms[furn.labroom.pk],
                    type=catalog,
                    color=furn.color
                )
                f.dataconfig=self.get_dataconfig(furn.dataconfig, f)
                f.save()
            else:
                pass

    def create_laboratories(self,organization):
        labs = Laboratory.objects.using('organilabprod').filter(organization=organization)
        parent_org = OrganizationStructure.objects.filter(name='UNA').first()

        for lab in labs:
            if not Laboratory.objects.filter(name=lab.name, organization=parent_org).exists():
                responsible = None
                if lab.responsable:
                    responsible = User.objects.filter(username=lab.responsible.username).first()
                newlab, created=Laboratory.objects.create(
                    name=lab.name,
                    phone_number = lab.phone_number,
                    location = lab.location,
                    geolocation =  lab.geolocation,
                    email = lab.email,
                    coordinator = lab.coordinator,
                    unit = lab.unit,
                    organization = parent_org,
                    created_by=self.user,
                    responsible=responsible,
                    description=lab.description,
                    area=lab.area,
                    nearby_sites=self.get_una_file(lab.nearby_sites),
                    water_resources_affected=self.get_una_file(lab.water_resources_affected),
                )
                self.laboratories[lab.pk] = newlab
            else:
                self.laboratories[lab.pk] = lab

                self.create_laboratory_rooms(lab.get_rooms().values('name', flat=True), newlab)

                org = OrganizationStructure.objects.filter(name=lab.organization.name).first()
                register_laboratory_contenttype(org, newlab)
                register_laboratory_contenttype(parent_org, newlab)
                for user in User.objects.all():
                    if not hasattr(user, 'profile'):
                        Profile.objects.get_or_create(
                            user=user,
                                )
                    pp = ProfilePermission.objects.create(
                        profile=user.profile,
                        content_type=ContentType.objects.get_for_model(Laboratory),
                        object_id=newlab.pk
                    )
    def create_priority(self):
        priority=PriorityConstrain.objects.using('organilabprod').values('id', 'operation', 'left_value', 'right_value', 'priority')
        for p in priority:
            priorities, created = PriorityConstrain.objects.get_or_create(
                operation=p['operation'],
                left_value=p['left_value'],
                right_value=p['right_value'],
                priority=p['priority']
            )
            self.priority[p.pk]=priorities.pk

    def create_regents(self, organization):
        regents=Regent.objects.using('organilabprod').filter(organization=organization)
        for r in regents:
            user = User.objects.filter(username=r.user.username).first()
            regents = Regent.objects.get_or_create(
                user=r.user,
                type_regent=r.type_regent
            )
            if r.laboratories.exists():
                for lab in r.laboratories.filter(organization=organization):
                    regents.laboratories.add(lab)

    def create_buildings(self, organization):
        buildings=Buildings.objects.using('organilabprod').all()
        for b in buildings:
            manager = None
            if b.manager:
                manager = User.objects.filter(username=b.manager.username).first()

            building = Buildings.objects.create(
                name=b.name,
                geolocation=b.geolocation,
                phone=b.phone,
                manager=manager,
                is_asociaty_buildings=b.is_asociaty_buildings,
                nearby_buildings=b.nearby_buildings,
                has_water_resources=b.has_water_resources,
                has_nearby_sites=self.get_una_file(b.has_nearby_sites),
                area=b.area,
                plans=self.get_una_file(b.plans),
                security_plan=self.get_una_file(b.security_plan),
                regulatory_plans=self.get_una_file(b.regulatory_plans),
                emergency_plan=self.get_una_file(b.emergency_plan),
                organization=organization
            )

            if b.laboratories.exists():
                for lab in b.laboratories.filter(organization=organization):
                    laboratory = Laboratory.objects.filter(name=lab.name).first()
                    if laboratory:
                        building.laboratories.add(laboratory)

            if b.regents.exists():
                for regent in b.regents.all():
                    reg = Regent.objects.filter(user=regent.user, organization=organization).first()
                    if reg:
                        building.regents.add(reg)
            building.save()

    def create_risk_zone(self, organization):
        zu=ZoneType.objects.using('organilabprod').all()
        for z in zu:
            zone, created = ZoneType.objects.get_or_create(name=z.name)
            if created:
                zone.priority_validator.add(*[self.priority[priority.pk] for priority in z.priority_validator.all()])
        for risk in RiskZone.objects.using('organilabprod').filter(organization=organization):
            zone = ZoneType.objects.filter(name=risk.zone_type.name).first()
            rz=RiskZone.objects.create(
                organization=organization,
                name=risk.name,
                num_workers =  risk.num_workers,
                zone_type = zone,
                priority = risk.priority
            )
            if risk.buildings.exists():
                for b in risk.buildings.all():
                    building = Buildings.objects.filter(name=b.name, organization=organization).first()
                    if building:
                        rz.buildings.add(building)

    def create_objectlogs(self,organization):
        logs = (ObjectLogChange.objects.using('organilabprod').
                filter(organization=organization).order_by('pk'))
        for log in logs:
            lab=None
            lab_name = None
            if log.laboratory:
                lab = Laboratory.objects.filter(name=log.laboratory.name).first()
            ObjectLogChange.objects.create(
                laboratory=lab,
                user=User.objects.filter(username=log.user.username).first(),
                old_value=log.old_value,
                new_value=log.new_value,
                diff_value=log.diff_value,
                update_time=log.update_time,
                precursor=log.precursor,
                measurement_unit=Catalog.objects.filter(description=log.measurement_unit.description).first(),
                subject=log.subject,
                provider=log.provider,
                bill=log.bill,
                type_action=log.type_action,
                note=log.note,
                organization_where_action_taken=organization,
                object=self.objects[log.object.pk]
            )

    def create_register_user_qr(self, organization):
        qr=RegisterUserQR.objects.using('organilabprod').filter(organization_creator=organization)
        for q in qr:
            rol = None
            org_register = None
            org_creator = None
            if q.organization_register:
                org_register = OrganizationStructure.objects.filter(name=q.organization_register.name).first()
            if q.organization_creator:
                org_creator = OrganizationStructure.objects.filter(name=q.organization_creator.name).first()
            if q.role:
                rol = Rol.objects.filter(name=q.role.name).first()
            active_user = User.objects.filter(username=q.created_by.username).first()
            created_by = User.objects.filter(username=q.created_by.username).first()
            content_type = ContentType.objects.filter(app_label=q.content_type.app_label, model=q.content_type.model).first()
            object_id = 0
            if q.content_object.model == "laboratory":
                object_id = Laboratory.objects.filter(name=q.content_object.name).first().pk
            elif q.content_object.model == "organizationstructure":
                object_id = OrganizationStructure.objects.filter(name=q.content_object.name).first().pk
            RegisterUserQR.objects.create(
                created_by = created_by,
                activate_user = active_user,
                url = q.url,
                register_user_qr = self.get_una_file(q.register_user_qr),
                role = rol,
                organization_creator = org_creator,
                organization_register = org_register,
                code = q.code,
                last_update = q.last_update,
                creation_date = q.creation_date,
                content_type = content_type,
                object_id = object_id,
            )

    def lab_org_log_entry(self):
        logs = LabOrgLogEntry.objects.using('organilabprod').all()
        for log in logs:
            object_id = 0
            entry = self.entries[log.log_entry.pk]
            if log.content_type.model == "laboratory":
                object_id = Laboratory.objects.using('organilabprod').filter(pk=log.object_id).first()
            elif log.content_type.model == "organizationstructure":
                object_id = OrganizationStructure.objects.using('organilabprod').filter(pk=log.object_id).first()
            LabOrgLogEntry.objects.create(
                log_entry=entry,
                content_type=ContentType.objects.filter(app_label=log.content_type.app_label, model=log.content_type.model).first(),
                object_id=object_id,
            )

    def migrate_precursor_report_values(self, precursor_report):
        reports = PrecursorReportValues.objects.using('organilabprod').filter(precursor_report=precursor_report)
        for report in reports:
            PrecursorReportValues.objects.create(
                    precursor_report = precursor_report,
                    object = self.objects[report.object.pk],
                    measurement_unit = self.get_or_create_catalog(report.measurement_unit.description,
                                                                'units'),
                    quantity = report.quantity,
                    previous_balance = report.previous_balance,
                    new_income = report.new_income,
                    bills = report.bills,
                    providers = report.providers,
                    stock = report.stock,
                    month_expense = report.month_expense,
                    final_balance = report.final_balance,
                    reason_to_spend = report.reason_to_spend
                )
    def migrate_precursors_reports(self):
        reports = PrecursorReport.objects.using('organilabprod').all()
        for report in reports:
            laboratory = None
            if report.laboratory:
                laboratory = Laboratory.objects.filter(name=report.laboratory.name).first()
            if laboratory:
                precursor_report = PrecursorReport.objects.create(
                    month = report.month,
                    year = report.year,
                    laboratory = laboratory,
                    consecutive = report.consecutive,
                    report_values = report.report_values,
                    month_belong = report.month_belong
                )
                self.migrate_precursor_report_values(precursor_report)

    def migrate_custom_forms(self, organization):
        self.forms = {}
        custom_forms = CustomForm.objects.using("organilabprod").filter(organization=organization)
        for form in custom_forms:
            org = self.organizations[organization.pk]
            forms = CustomForm.objects.create(
                name=form.name,
                status=form.status,
                schema=form.schema,
                organization=org
            )
            self.forms[form.pk] = forms

    def migrate_informs(self, organization):
        informs = Inform.objects.using("organilabprod").filter(organization=organization)
        for inform in informs:
            org = self.organizations[organization.pk]
            content_type = ContentType.objects.filter(app_label=inform.content_type.app_label, model=inform.content_type.model).first()
            user= None
            if inform.created_by:
                user = User.objects.filter(username=inform.created_by.username).first()
            Inform.objects.create(
                name=inform.name,
                custom_form=self.forms[inform.custom_form.pk],
                content_type=content_type,
                object_id= self.laboratories[inform.object_id].pk,
                context_object=inform.context_object,
                status=inform.status,
                creation_date=inform.creation_date,
                last_update=inform.last_update,
                organization=org,
                created_by=user
            )

    def migrate_informs_scheduler(self, organization):
        informs = InformScheduler.objects.using("organilabprod").filter(organization=organization)
        for inform in informs:
            org = self.organizations[organization.pk]
            user= None
            if inform.created_by:
                user = User.objects.filter(username=inform.created_by.username).first()
            InformScheduler.objects.create(
                name=inform.name,
                start_application_date=inform.start_application_date,
                close_application_date=inform.close_application_date,
                inform_template=self.forms[inform.inform_template.pk],
                active=inform.active,
                creation_date=inform.creation_date,
                last_update=inform.last_update,
                organization=org,
                created_by=user
            )

    def init_data(self):
        self.create_base_units()
        self.process_objectfeatures()
        self.transfer_users()
        organizations =[
            [42,93, 110, 136,137,143, 164, 167],
            [104,26,45,106, 108],
            [95,97, 100,98, 99]
        ]
        for orgs in organizations:
            for organization in (OrganizationStructure.objects.using('organilabprod').
                filter(pk__in=orgs)):
                #self.transfer_organizations(organization)
                #self.migrate_custom_forms(organization)
                #self.migrate_informs_scheduler(organization)
                #self.migrate_informs(organization)
                #self.create_register_user_qr(organization)
                #self.create_laboratories(organization)
                #self.create_furniture(organization)
                #self.transfer_objects(organization)
                #self.create_shelfobject_material(organization)
                #self.migrate_shelfobject(organization)
                print(organization.pk)
            print("------")

    def handle(self, *args, **options):
        self.user=None
        self.labrooms = {}
        self.shelfs={}
        self.objects = {}
        self.laboratories = {}

        self.init_data()

        #print(self.user)
        #self.transfer_organizations()
