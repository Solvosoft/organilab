from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from laboratory.models import Profile


class Command(BaseCommand):
    help = 'Create a user profile'

    def handle(self, *args, **options):
        for user in User.objects.filter(profile__isnull=True):
            Profile.objects.create(user=user, phone_number='5068888888',
                id_card='0000000', job_position='')
