from rest_framework import permissions


class HasInstitutionAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("auth_and_perms.institution_can_access")


def can_manage_platform_users(user):
    return user.is_authenticated and (user.is_superuser or user.has_perm("auth_and_perms.can_manage_users"))


class CanManagePlatformUsers(permissions.BasePermission):
    """Borrar y fusionar usuarios es de plataforma: ningún rol de organización lo concede."""

    def has_permission(self, request, view):
        return can_manage_platform_users(request.user)
