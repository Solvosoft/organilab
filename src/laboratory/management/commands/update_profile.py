from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from auth_and_perms.models import Profile, ProfilePermission
from laboratory.models import OrganizationUserManagement, Laboratory, OrganizationStructure


class Command(BaseCommand):
    help = 'Create a user profile'

    def handle(self, *args, **options):
        for user in User.objects.filter(profile__isnull=True):
            Profile.objects.create(user=user, phone_number='5068888888',
                id_card='0000000', job_position='')

        for org in OrganizationStructure.objects.all():
            query = OrganizationUserManagement.objects.filter(organization=org)
            if query.count()>1:
                base = query[0]
                query=query.exclude(pk=base.pk)
                for q in query:
                    for user in q.users.all():
                        base.users.add(user)
                print(query.delete())
        for profile in Profile.objects.all():
            for pp in ProfilePermission.objects.filter(profile=profile):
                if pp.content_type.model == 'laboratory':
                    oum = OrganizationUserManagement.objects.filter(
                        organization=pp.content_object.organization,
                        users=profile.user
                    )
                    if not oum.exists():
                        print(pp.content_object.organization, pp.content_object.organization.pk)
                        org, created=OrganizationUserManagement.objects.get_or_create(organization=pp.content_object.organization)
                        org.users.add(profile.user)
                ProfilePermission.objects.get_or_create(
                                                 profile=profile,
                                                 content_type=ContentType.objects.filter(
                                                     app_label=profile._meta.app_label,
                                                     model=profile._meta.model_name).first(),
                                                 object_id=profile.pk)





