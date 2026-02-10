from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand

from auth_and_perms.models import Profile, ProfilePermission
from auth_and_perms.views.user_org_creation import (
    set_rol_administrator_on_org,
    create_user_organization,
)
from laboratory.models import (
    OrganizationStructure,
    Laboratory,
    UserOrganization,
    OrganizationStructureRelations,
)
from faker import Faker

fake = Faker()


class Command(BaseCommand):
    help = "Create a Organization structure"
    num_of_orgs = 3
    num_of_children = 2
    num_of_cousin = 3
    lab_per_org = 3
    lab_per_children = 2
    lab_per_cousin = 1

    user_per_org = 2
    user_per_lab_org = 3
    user_per_children = 2
    user_per_lab_children = 4
    user_per_cousing = 1
    user_per_lab_cousing = 1
    org_contenttype = ContentType.objects.filter(
        app_label="laboratory", model="organizationstructure"
    ).first()
    lab_contenttype = ContentType.objects.filter(
        app_label="laboratory", model="laboratory"
    ).first()

    def create_laboratory(self, num_of_lab, org, post_name="", user_per_lab=1):
        for x in range(num_of_lab):
            lab = Laboratory.objects.create(
                name="Laboratory %d %s" % (x, post_name),
                phone_number="8888888",
                location="85,10",
                email="lab%d%s@organilab.org" % (x, post_name),
                coordinator="",
                unit="development",
                organization=org,
            )
            print(lab.pk, lab.name)
            self.create_user_lab_organization(org, lab, user_per_lab)
            self.create_organizationstructurerelations_laboratory(org, lab)

    def create_user_organization(
        self,
        organization,
        num_org=1,
        appenduser=[],
        usertype=UserOrganization.ADMINISTRATOR,
    ):
        users = []
        for num in range(num_org):
            user = User.objects.create_user(
                "user_%d_%d" % (num, organization.pk), fake.free_email(), "admin12345"
            )
            user.first_name = fake.first_name_nonbinary()
            user.last_name = fake.last_name()
            data = {"phone_number": "8888", "id_card": "88888", "job_position": "test"}
            create_user_organization(user, organization, data, user_type=usertype)
            users.append(user)
        for user in appenduser:
            set_rol_administrator_on_org(user.profile, organization)
        return users

    def create_user_lab_organization(self, organization, laboratory, num_org=1):
        for num in range(num_org):
            user = User.objects.create_user(
                "user_%d_%d_%d" % (num, organization.pk, laboratory.pk),
                fake.free_email(),
                "admin12345",
            )
            user.first_name = fake.first_name_nonbinary()
            user.last_name = fake.last_name()
            user.save()
            profile = Profile.objects.create(
                user=user, phone_number="8888", id_card="88888", job_position="test"
            )
            UserOrganization.objects.create(
                organization=organization,
                user=user,
                type_in_organization=UserOrganization.LABORATORY_USER,
            )

            ProfilePermission.objects.create(
                profile=profile,
                content_type=self.lab_contenttype,
                object_id=laboratory.pk,
            )

    def create_organizationstructurerelations(self, organization):
        OrganizationStructureRelations.objects.create(
            organization=organization,
            content_type=self.org_contenttype,
            object_id=organization.pk,
        )

    def create_organizationstructurerelations_laboratory(self, organization, lab):
        OrganizationStructureRelations.objects.create(
            organization=organization,
            content_type=self.lab_contenttype,
            object_id=lab.pk,
        )
        print(
            "OrganizationStructureRelations ",
            organization.pk,
            lab.pk,
            self.lab_contenttype,
        )

    def create_organizations(self):
        for org_num in range(self.num_of_orgs):
            org = OrganizationStructure.objects.create(
                name="Mi org %d" % org_num, level=0, position=0
            )
            org.name = "Mi org %d %d" % (org.pk, org_num)
            org.save()
            print(org.pk, org.name)
            users = self.create_user_organization(org, num_org=self.user_per_org)
            self.create_organizationstructurerelations(org)
            # create_laboratory(self, num_of_lab, org, post_name="", user_per_lab=1)
            self.create_laboratory(
                self.lab_per_org,
                org,
                post_name="%d" % org_num,
                user_per_lab=self.user_per_lab_org,
            )
            for children_num in range(self.num_of_children):
                org_chi = OrganizationStructure.objects.create(
                    name="Mi org %d %d - %d" % (org.pk, org_num, children_num),
                    level=1,
                    parent=org,
                    position=1,
                )
                self.create_user_organization(
                    org_chi,
                    num_org=self.user_per_children,
                    appenduser=users,
                    usertype=UserOrganization.LABORATORY_MANAGER,
                )
                self.create_organizationstructurerelations(org_chi)
                self.create_laboratory(
                    self.lab_per_children,
                    org_chi,
                    post_name="%d - %d" % (org_num, children_num),
                    user_per_lab=self.user_per_lab_children,
                )
                for cousin_num in range(self.num_of_cousin):
                    org_cousin = OrganizationStructure.objects.create(
                        name="Mi org %d %d %d - %d -- %d"
                        % (org.pk, org_chi.pk, org_num, children_num, cousin_num),
                        level=2,
                        parent=org_chi,
                        position=2,
                    )
                    self.create_organizationstructurerelations(org_cousin)
                    self.create_user_organization(
                        org_cousin,
                        num_org=self.user_per_cousing,
                        appenduser=users,
                        usertype=UserOrganization.LABORATORY_MANAGER,
                    )
                    self.create_laboratory(
                        self.lab_per_cousin,
                        org_cousin,
                        post_name="%d - %d -- %d" % (org_num, children_num, cousin_num),
                        user_per_lab=self.user_per_lab_cousing,
                    )

    def handle(self, *args, **options):
        self.create_organizations()
