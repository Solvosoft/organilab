from django.contrib.auth.models import Permission, Group
from django.core.management import BaseCommand
from django.apps.registry import apps
from django.contrib.contenttypes.management import create_contenttypes
from django.contrib.auth.management import create_permissions

class Command(BaseCommand):
    help = 'Set permissions'

    def handle(self, *args, **options):

        """"
        Obtiene los grupos de usuarios y el codename de sus permisos, elimina todos los permisos registrados
        y los regenera, agrega los permisos correspondientes a cada grupo verficando si el permiso existe.

        """

        per_laboratory_administrator = None
        per_professor = None
        per_student = None

        laboratory_administrator = Group.objects.filter(name="Laboratory Administrator").first()
        professor = Group.objects.filter(name="Professor").first()
        student = Group.objects.filter(name="Student").first()

        if laboratory_administrator:
            per_laboratory_administrator = list(Group.objects.filter(name="Laboratory Administrator").values_list('permissions__codename', flat=True))
            per_laboratory_administrator += ['add_organizationusermanagement', 'change_organizationusermanagement',
                                            'delete_organizationusermanagement', 'view_organizationusermanagement']
        if professor:
            per_professor = list(Group.objects.filter(name="Professor").values_list('permissions__codename', flat=True))

        if student:
            per_student = list(Group.objects.filter(name="Student").values_list('permissions__codename', flat=True))


        Permission.objects.all().delete()
        for app_config in apps.get_app_configs():
            create_permissions(app_config)

        if laboratory_administrator and per_laboratory_administrator:

            for per in per_laboratory_administrator:
                permission = Permission.objects.filter(codename=per).first()
                if permission:
                    laboratory_administrator.permissions.add(permission)

        if professor and per_professor:

            for per in per_professor:
                permission = Permission.objects.filter(codename=per).first()
                if permission:
                    professor.permissions.add(permission)

        if student and per_student:

            for per in per_student:
                permission = Permission.objects.filter(codename=per).first()
                if permission:
                    student.permissions.add(permission)







