import zipfile

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core import serializers
from django.http import HttpResponse
import io
from auth_and_perms import models
from auth_and_perms.users import delete_user, send_email_user_management


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

class ImpostorAdmin(admin.ModelAdmin):
    search_fields = ['impostor__username','imposted_as__username']
    list_display = ['__str__', 'impostor_ip', 'logged_in', 'logged_out']
    date_hierarchy = 'logged_in'

class DeleteUserListAdmin(admin.ModelAdmin):
    search_fields = ['user__username']
    list_display = ['__str__', 'last_login', 'creation_date', 'expiration_date']
    date_hierarchy =  'expiration_date'
    actions = ['merge_and_delete']

    @admin.action(description="Remove user correctly")
    def merge_and_delete(self, request, queryset):
        User = get_user_model()
        user_base = User.objects.filter(username="soporte@organilab.org").first()
        for user_delete in queryset:
            send_email_user_management(request, user_base, user_delete.user, "delete")
            delete_user(user_delete.user, user_base)

admin.site.register(models.AuthorizedApplication, AuthorizedApplicationAdmin)
admin.site.register(models.Profile, ProfileAdmin)
admin.site.register(models.Rol, RolAdmin)
admin.site.register(models.ProfilePermission, ProfilePermissionAdmin)
admin.site.register(models.ImpostorLog, ImpostorAdmin)
admin.site.register(models.DeleteUserList, DeleteUserListAdmin)
