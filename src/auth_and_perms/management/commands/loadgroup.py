from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand
from auth_and_perms.management.commands.urlname_permissions import URLNAME_PERMISSIONS

class Command(BaseCommand):
    help = 'Load permission category'

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name='RegisterOrganization')
        group.permissions.clear()
        # ('codename', 'content_type__app_label')
        """
        PERMISSIONS = [
            ('laboratory', 'view_inform'),
            ('laboratory', 'add_inform'),
            ('laboratory', 'delete_inform'),
            ('laboratory', 'add_laboratory'),
            ('laboratory', 'change_laboratory'),
            ('laboratory', 'view_laboratory'),
            ('laboratory', 'add_furniture'),
            ('laboratory', 'change_furniture'),
            ('laboratory', 'view_furniture'),
            ('laboratory', 'delete_furniture'),
            ('laboratory', 'add_shelfobject'),
            ('laboratory', 'change_shelfobject'),
            ('laboratory', 'view_shelfobject'),
            ('laboratory', 'delete_shelfobject'),
            ('laboratory', 'add_shelf'),
            ('laboratory', 'change_shelf'),
            ('laboratory', 'view_shelf'),
            ('laboratory', 'delete_shelf'),
            ('laboratory', 'add_object'),
            ('laboratory', 'change_object'),
            ('laboratory', 'delete_object'),
            ('laboratory', 'view_object'),
            ('laboratory', 'view_report'),
            ('laboratory', 'add_objectfeatures'),
            ('laboratory', 'view_laboratoryroom'),
            ('laboratory', 'add_laboratoryroom'),
            ('laboratory', 'delete_laboratoryroom'),
            ('laboratory', 'change_laboratoryroom'),
            ('laboratory', 'do_report'),
            ('laboratory', 'view_organizationusermanagement'),
            ('laboratory', 'add_organizationusermanagement'),
            ('laboratory', 'change_organizationstructure'),
            ('laboratory', 'add_organizationstructure'),
            ('laboratory', 'delete_organizationstructure'),
            ('djreservation', 'add_reservation'),
            ('academic', 'view_procedure'),
            ('academic', 'add_procedurestep'),
            ('derb', 'add_customform'),
            ('sga', 'view_label'),
            ('sga', 'view_pictogram'),
            ('sga', 'change_templatesga'),
            ('sga', 'view_substance'),
            ('sga', 'view_prudenceadvice'),
            ('sga', 'add_pictogram'),
            ('sga', 'view_warningword'),
            ('sga', 'change_sgacomplement'),
            ('sga', 'change_securityleaf'),
            ('sga', 'add_personaltemplatesga'),
            ('sga', 'change_personaltemplatesga'),
            ('msds', 'view_msdsobject'),
            ('msds', 'create_msdsobject'),
            ('msds', 'change_msdsobject'),
            ('msds', 'delete_msdsobject'),
            ('auth_and_perms', 'add_rol'),
            ('auth_and_perms', 'add_profile'),
            ('risk_management', 'view_riskzone'),
            ('risk_management', 'add_riskzone'),
            ('risk_management', 'delete_riskzone'),
            ('risk_management', 'change_riskzone'),
            ('risk_management', 'view_riskzone'),
            ('risk_management', 'view_incidentreport'),
            ('risk_management', 'add_incidentreport'),
            ('risk_management', 'change_incidentreport'),
            ('risk_management', 'view_incidentreport'),
            ('risk_management', 'delete_incidentreport'),


        ]
        """

        PERMISSIONS = set()
        for item in URLNAME_PERMISSIONS:
            for perm in URLNAME_PERMISSIONS[item]:
                PERMISSIONS.add(perm['permission'])
        for perm in PERMISSIONS:
            perm = perm.split('.')
            permission = Permission.objects.filter(codename=perm[1], content_type__app_label=perm[0]).first()
            if permission:
                group.permissions.add(permission)
            else:
                print(perm)