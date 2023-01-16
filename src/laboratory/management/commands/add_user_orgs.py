from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from auth_and_perms.models import Profile, ProfilePermission
from laboratory.models import OrganizationUserManagement, UserOrganization


class Command(BaseCommand):
    help = 'Add user into orgas'

    def handle(self, *args, **options):
        UserOrganization.objects.all().delete()
        for org in OrganizationUserManagement.objects.all():
            for user in org.users.all():
                UserOrganization.objects.get_or_create(
                                                     organization=org.organization,
                                                     user=user)





