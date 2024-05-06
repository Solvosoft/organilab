import zipfile

from django.contrib import admin
from django.core import serializers
from django.http import HttpResponse
import io
from auth_and_perms import models

@admin.action(description='Export Laboratory')
def export_rol_perms(admin, request, queryset):
    buffer = io.BytesIO()
    zip_file = zipfile.ZipFile(buffer, 'w')


    for rol in queryset:
        rols=models.ProfilePermission.objects.filter(rol=rol)
        zip_file.writestr(rol.name+".json", serializers.serialize('json', rols))
    zip_file.close()
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(),
        content_type='application/x-zip-compressed',
        headers={'Content-Disposition': 'attachment; filename="permissionsrol.zip"'})
    return response


class RolAdmin(admin.ModelAdmin):
    filter_horizontal = ['permissions']
    actions = [export_rol_perms]


class AuthorizedApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'auth_token']

    @admin.display(empty_value='unknown')
    def auth_token(self, obj):
        if obj.user:
            return obj.user.auth_token.key
        return 'unknown'

class ProfileAdmin(admin.ModelAdmin):
    search_fields = ['user__username', 'user__email']

class ProfilePermissionAdmin(admin.ModelAdmin):
    search_fields = ['profile__user__email']
admin.site.register(models.AuthorizedApplication, AuthorizedApplicationAdmin)
admin.site.register(models.Profile, ProfileAdmin)
admin.site.register(models.Rol, RolAdmin)
admin.site.register(models.ProfilePermission, ProfilePermissionAdmin)
