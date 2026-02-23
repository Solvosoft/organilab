from rest_framework import permissions


class HasInstitutionAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("auth_and_perms.institution_can_access")

