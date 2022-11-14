from django.contrib import admin
from auth_and_perms import models


class RolAdmin(admin.ModelAdmin):
    filter_horizontal = ['permissions']


class AuthorizedApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'auth_token']

    @admin.display(empty_value='unknown')
    def auth_token(self, obj):
        if obj.user:
            return obj.user.auth_token.key
        return 'unknown'


admin.site.register(models.AuthorizedApplication, AuthorizedApplicationAdmin)
admin.site.register(models.Profile)
admin.site.register(models.Rol, RolAdmin)
admin.site.register(models.ProfilePermission)