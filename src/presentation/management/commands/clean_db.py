from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Q, Count

from auth_and_perms.models import UserTOTPDevice
from laboratory.models import OrganizationStructure, Laboratory


class Command(BaseCommand):
    """
    Usuarios de interés

    Ainhoacalvo                                     ainhoacalvo21@gmail.com
    Alejandromartinezaguilera3@gmail.com            Alejandromartinezaguilera3@gmail.com


    """
    DEL_USERS= [45, 127, 116, 112, 114, 115, 118, 119, 122, 120, 121, 117, 123, 124, 125, 126, 129, 130, 131, 113,
                133, 134, 127, 27, 18, 60, 57, 70, 75, 71, 73, 72, 23, 87, 88, 107]

    DEL_ORGANIZATIONS = [1,2,3,4,5,6,7,8,9,10,11,60, 61, 22, 44, 53, ]

    def delete_users_without_profile(self):
        usrs = User.objects.filter(profile=None)
        for usr in usrs:
            usr.delete()
        #print(list(usrs.values_list('pk', flat=True)))

    def delete_user_email_not_valid(self):
        emails = [
            'luis.zarate@solvosoft.com',
            'luisza14@gmail.com',
            'alfredoromero85@gmail.com',
            'prueba@gmail.com',
            'alfredo@colaborador.org',
            'william@organilab.com',
            'william@organilab.com',
            'marcegz31@gmail.com',
            'viqher@gmail.com',
            'estudiante@organilab.org',
        ]

        usrs = User.objects.filter(email__in=emails)
        usrs.delete()
        #print(list(usrs.values_list('pk', flat=True)))

    def delete_organizations(self):
        OrganizationStructure.objects.filter(pk__in=self.DEL_ORGANIZATIONS).delete()
        OrganizationStructure.objects.annotate(
            lab_count=Count("laboratory")
        ).filter(
            lab_count=0
        ).delete()

        OrganizationStructure.objects.annotate(
            lab_count=Count("userorganization")
        ).filter(
            lab_count=0
        ).delete()

    def delete_users(self):
        User.objects.annotate(
            user_count=Count("userorganization")
        ).filter(user_count=0).delete()

    def delete_laboratory(self):
        labs = Laboratory.objects.annotate(shobj_count=Count('rooms__furniture__shelf__shelfobject')).filter(shobj_count=0)
            #.delete()
        #print(list(labs.values_list('pk', flat=True)))

    def handle(self, *args, **options):
        #self.delete_laboratory()
        self.delete_users_without_profile()
        self.delete_user_email_not_valid()
        self.delete_laboratory()
        self.delete_organizations()
        self.delete_users()
