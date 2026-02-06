from rest_framework import permissions


class HasUNAAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("auth_and_perms.institution_can_access")
