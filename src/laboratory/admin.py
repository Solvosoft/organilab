from django.contrib import admin
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from laboratory import models
from laboratory.task_utils import create_informsperiods
from presentation.utils import update_qr_instance
from django.core import serializers


@admin.action(description="Regenerate QR")
def regenerate_qr_codes(admin, request, queryset):
    for instance in queryset:
        update_qr_instance(
            instance.shelf_object_url,
            instance,
            instance.in_where_laboratory.organization.pk,
        )


class ShelfObject_Admin(admin.ModelAdmin):
    actions = [regenerate_qr_codes]


class Object_Admin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ("code", "name", "type", "is_precursor")


class OrganizationStrutureAdmin(admin.ModelAdmin):
    search_fields = ["name", "laboratory__name"]
    list_display = ["name", "laboratories"]
    mptt_level_indent = 20


@admin.action(description="Run new informs utilities")
def create_informs(admin, request, queryset):
    for instance in queryset:
        create_informsperiods(instance)


class PeriodScheduledAdmin(admin.TabularInline):
    model = models.InformsPeriod


class InformSchedulerAdmin(admin.ModelAdmin):
    search_fields = [
        "name",
    ]
    list_display = [
        "name",
    ]
    actions = [create_informs]
    inlines = [PeriodScheduledAdmin]


@admin.action(description="Export Laboratory")
def export_laboratory(admin, request, queryset):
    response = HttpResponse(
        content_type="Application/json",
        headers={"Content-Disposition": 'attachment; filename="laboratory.json"'},
    )
    labrooms = models.LaboratoryRoom.objects.filter(laboratory__in=queryset)
    furnutures = models.Furniture.objects.filter(labroom__in=labrooms)
    shelfs = models.Shelf.objects.filter(furniture__in=furnutures)
    shelfsobject = models.ShelfObject.objects.filter(shelf__in=shelfs)
    objs = [*labrooms, *furnutures, *shelfs, *shelfsobject]
    serializers.serialize("json", objs, stream=response)
    return response


class LaboratoryAdmin(admin.ModelAdmin):
    actions = [export_laboratory]
    search_fields = ["name"]
    list_filter = ["organization"]


class PrecursorReportValuesInline(admin.TabularInline):
    model = models.PrecursorReportValues
    fields = [
        "object",
        "measurement_unit",
        "previous_balance",
        "new_income",
        "stock",
        "month_expense",
        "final_balance",
    ]


class PrecursorReportAdmin(admin.ModelAdmin):
    search_fields = ["laboratory__name", "month", "year"]
    list_filter = ["laboratory__name", "month", "year"]
    list_display = ["consecutive", "laboratory", "month", "year"]
    inlines = (PrecursorReportValuesInline,)


class PrecursorReportValuesAdmin(admin.ModelAdmin):
    search_fields = [
        "precursor_report__laboratory__name",
        "object__code",
        "object__name",
    ]

    list_display = ["precursor_report", "object", "measurement_unit", "final_balance"]


class BaseUnittAdmin(admin.ModelAdmin):
    list_display = ["measurement_unit_base", "measurement_unit", "si_value"]


class ObjectLogAdmin(admin.ModelAdmin):
    list_display = ["object", "update_time"]


admin.site.register(models.Laboratory, LaboratoryAdmin)
admin.site.register(models.Protocol)
admin.site.register(models.LaboratoryRoom)
admin.site.register(models.Furniture)
admin.site.register(models.Shelf)
admin.site.register(models.ObjectFeatures)
admin.site.register(models.Object, Object_Admin)
admin.site.register(models.ShelfObject, ShelfObject_Admin)
admin.site.register(models.Catalog)
admin.site.register(models.BlockedListNotification)
admin.site.register(models.Provider)
admin.site.register(models.ObjectLogChange, ObjectLogAdmin)
admin.site.register(models.TranferObject)
admin.site.register(models.PrecursorReport, PrecursorReportAdmin)
admin.site.register(models.RegisterUserQR)
admin.site.register(models.OrganizationStructure, OrganizationStrutureAdmin)
admin.site.register(models.UserOrganization)
admin.site.register(models.InformScheduler, InformSchedulerAdmin)
admin.site.register(models.ShelfObjectObservation)
admin.site.register(models.BaseUnitValues, BaseUnittAdmin)
admin.site.register(models.PrecursorReportValues, PrecursorReportValuesAdmin)


admin.site.site_header = _("Organilab Administration site")
