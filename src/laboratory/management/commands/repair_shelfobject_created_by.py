from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from auth_and_perms.models import Profile
from laboratory.models import ShelfObject, ObjectLogChange

class Command(BaseCommand):

    help = 'Add Shelf Object Id in ObjectLogChange'

    def repair_shelf_object(self):
        so = ShelfObject.objects.filter(created_by__isnull=True)

        for soo in so:
            queryset = ObjectLogChange.objects.filter(
                object=soo.object,
                laboratory=soo.in_where_laboratory
            )
            for query in queryset:

                if User.objects.filter(pk=query.user_id).exists():
                    #print(query.pk, soo.pk, query.user_id)
                    soo.created_by_id=query.user_id
                    soo.save()
                    break
                else:
                    print("User doesn't exist: ", query.user_id)
                print("Searching: discarding: ", query.pk, soo.pk, query.user_id)

    def repair_profiles(self):
        for user in User.objects.filter(profile__isnull=True):
            Profile.objects.create(
                user=user,
                phone_number = '00000',
                id_card = '0000000',
                job_position = 'N/D'
            )

    def handle(self, *args, **options):
        #self.repair_shelf_object()
        self.repair_profiles()
