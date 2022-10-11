from django.contrib import admin
from laboratory import models
from django.utils.translation import gettext_lazy as _


class Object_Admin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ('code', 'name', 'type', 'is_precursor')


class OrganizationStrutureAdmin(admin.ModelAdmin):
    search_fields = ["name", 'laboratories']
    list_display = ["name", 'laboratories']
    mptt_level_indent = 20


class RolAdmin(admin.ModelAdmin):
    filter_horizontal = ['permissions']


admin.site.register(models.Laboratory)
admin.site.register(models.LaboratoryRoom)
admin.site.register(models.Furniture)
admin.site.register(models.Shelf)
admin.site.register(models.OrganizationUserManagement)
admin.site.register(models.Profile)
admin.site.register(models.ObjectFeatures)
admin.site.register(models.Object, Object_Admin)
admin.site.register(models.ShelfObject)
admin.site.register(models.Catalog)
admin.site.register(models.BlockedListNotification)
admin.site.register(models.Rol, RolAdmin)
admin.site.register(models.ProfilePermission)
admin.site.register(models.Provider)
admin.site.register(models.ObjectLogChange)
admin.site.register(models.TranferObject)
admin.site.register(models.PrecursorReport)


admin.site.register(models.OrganizationStructure, OrganizationStrutureAdmin)


admin.site.site_header = _('Organilab Administration site')
