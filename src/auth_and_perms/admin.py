from django.contrib import admin
from auth_and_perms import models

class RolAdmin(admin.ModelAdmin):
    filter_horizontal = ['permissions']

admin.site.register(models.Profile)
admin.site.register(models.Rol, RolAdmin)
admin.site.register(models.ProfilePermission)