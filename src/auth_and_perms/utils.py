from auth_and_perms.models import Rol
from laboratory.models import OrganizationStructure


def get_roles_by_user(user):
    orgs = OrganizationStructure.os_manager.filter_user(user).values_list('pk', flat=True)
    return Rol.objects.filter(organizationstructure__in=orgs)