from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from academic.models import MyProcedure
from auth_and_perms.models import ProfilePermission, Profile
from derb.models import CustomForm
from laboratory.models import OrganizationStructure, Laboratory, Object, \
    Furniture, ShelfObjectEquipmentCharacteristics, ShelfObjectLog, \
    ShelfObjectMaintenance, ShelfObjectCalibrate, ShelfObjectTraining, \
    ShelfObjectGuarantee, UserOrganization, ObjectLogChange, Inform, InformScheduler, \
    InformsPeriod, OrganizationStructureRelations, LabOrgLogEntry, RegisterUserQR
from msds.models import MSDSObject
from reservations_management.models import ReservedProducts
from risk_management.models import RiskZone, PriorityConstrain, IncidentReport, Regent, \
    Buildings, Structure
from sga.models import Substance, TemplateSGA, BuilderInformation, DisplayLabel, \
    ReviewSubstance


class Command(BaseCommand):
    help = "Create QR"

    def init(self):
        self.parent_org = OrganizationStructure.objects.get(pk=178)
        self.child_org = OrganizationStructure.objects.filter(pk__in=[26,45,108])

    def merge_laboratories(self):
        lab_contenttype = ContentType.objects.filter(app_label="laboratory",
                                                     model="laboratory").first()
        org_contenttype = (ContentType.objects.filter(app_label="laboratory",
                                                      model="organizationstructure").
                           first())

        (Laboratory.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (Object.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (ShelfObjectEquipmentCharacteristics.objects.
         filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (ShelfObjectMaintenance.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (ShelfObjectLog.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (ShelfObjectCalibrate.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (ShelfObjectTraining.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (ShelfObjectGuarantee.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (UserOrganization.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (ObjectLogChange.objects.
         filter(organization_where_action_taken__in=self.child_org).
         update(organization_where_action_taken=self.parent_org))

        (Inform.objects.filter(organization__in=self.child_org,
                              content_type=org_contenttype).
         update(organization=self.parent_org, object_id=self.parent_org.pk))

        (Inform.objects.filter(organization__in=self.child_org,
                              content_type=lab_contenttype).
         update(organization=self.parent_org))

        (LabOrgLogEntry.objects.filter(content_type=org_contenttype).
         update(object_id=self.parent_org.pk))


        (RegisterUserQR.objects.filter(organization_creator__in=self.child_org,
                                      content_type=lab_contenttype).
         update(organization_creator=self.parent_org))

        (RegisterUserQR.objects.filter(organization_register__in=self.child_org,
                                      content_type=lab_contenttype).
         update(organization_register=self.parent_org))

        (InformScheduler.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (InformsPeriod.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (OrganizationStructureRelations.objects.filter(organization__in=self.child_org,
                                                      content_type=lab_contenttype).
         update(organization=self.parent_org))

    def merge_risks_management(self):
        (PriorityConstrain.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (RiskZone.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (IncidentReport.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (Regent.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (Buildings.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (Structure.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

    def merge_auth_and_perms(self):
        contenttype = ContentType.objects.filter(app_label="laboratory",
                                                 model="organizationstructure").first()
        lab_contenttype = ContentType.objects.filter(app_label="laboratory",
                                                     model="laboratory").first()
        pp=ProfilePermission.objects.filter(object_id__in=self.child_org.values_list("pk", flat=True),
                                         content_type=contenttype)
        for p in pp:
            p.object_id = self.parent_org.pk
            self.parent_org.rol.add(*p.rol.all())
            self.parent_org.save()
            p.save()

        for child in self.child_org:

            users_lab = (UserOrganization.objects.filter(organization=child).
                         values_list("user", flat=True))
            profiles_lab = Profile.objects.filter(user__in=users_lab).distinct()

            for p in ProfilePermission.objects.filter(object_id__in=child.laboratory_set.all().values_list("pk", flat=True),
                                         content_type=lab_contenttype,
                                                        profile__in=profiles_lab):
                self.parent_org.rol.add(*p.rol.all())
                self.parent_org.save()

    def merge_derb(self):
        (CustomForm.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

    def merge_reservations(self):
        (ReservedProducts.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

    def merge_msds(self):
        (MSDSObject.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

    def merge_academic(self):
        org_contenttype = (ContentType.objects.filter(app_label="laboratory",
                                                     model="organizationstructure").
                           first())
        (MyProcedure.objects.filter(organization__in=self.child_org,
                                   content_type=org_contenttype).
         update(organization=self.parent_org, object_id=self.parent_org.pk))

    def merge_sga(self):
        (Substance.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (BuilderInformation.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (TemplateSGA.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (DisplayLabel.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

        (ReviewSubstance.objects.filter(organization__in=self.child_org).
         update(organization=self.parent_org))

    def delete_organizations(self):
        self.child_org.delete()


    def handle(self, *args, **options):
        self.init()
        self.merge_auth_and_perms()
        self.merge_laboratories()
        self.merge_risks_management()
        self.merge_derb()
        self.merge_reservations()
        self.merge_msds()
        self.merge_academic()
        self.merge_sga()
        self.delete_organizations()
