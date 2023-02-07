from django.contrib import admin
from django.utils.decorators import method_decorator

from laboratory import models
from django.utils.translation import gettext_lazy as _

from laboratory.task_utils import create_informsperiods


class Object_Admin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ('code', 'name', 'type', 'is_precursor')


class OrganizationStrutureAdmin(admin.ModelAdmin):
    search_fields = ["name", 'laboratories']
    list_display = ["name", 'laboratories']
    mptt_level_indent = 20

@admin.action(description='Run new informs utilities')
def create_informs(admin, request, queryset):
    for instance in queryset:
        create_informsperiods(instance)


class PeriodScheduledAdmin(admin.TabularInline):
    model = models.InformsPeriod

class InformSchedulerAdmin(admin.ModelAdmin):
    search_fields = ["name",]
    list_display = ["name",]
    actions = [create_informs]
    inlines = [PeriodScheduledAdmin]


admin.site.register(models.Laboratory)
admin.site.register(models.Protocol)
admin.site.register(models.LaboratoryRoom)
admin.site.register(models.Furniture)
admin.site.register(models.Shelf)
admin.site.register(models.OrganizationUserManagement)

admin.site.register(models.ObjectFeatures)
admin.site.register(models.Object, Object_Admin)
admin.site.register(models.ShelfObject)
admin.site.register(models.Catalog)
admin.site.register(models.BlockedListNotification)

admin.site.register(models.Provider)
admin.site.register(models.ObjectLogChange)
admin.site.register(models.TranferObject)
admin.site.register(models.PrecursorReport)


admin.site.register(models.OrganizationStructure, OrganizationStrutureAdmin)
admin.site.register(models.UserOrganization)
admin.site.register(models.InformScheduler, InformSchedulerAdmin)


admin.site.site_header = _('Organilab Administration site')
