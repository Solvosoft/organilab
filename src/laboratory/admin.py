from django.contrib import admin
from django.db.models import Q
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from auth_and_perms.admin import DELETED_USER_TAG_MARKERS
from laboratory import models
from laboratory.task_utils import create_informsperiods
from presentation.utils import update_qr_instance
from django.core import serializers


class OrganizationInfoAdminMixin:
    organization_field = "organization"

    def get_list_select_related(self, request):
        related = getattr(super(), "get_list_select_related", None)
        base = (
            related(request)
            if callable(related)
            else getattr(self, "list_select_related", ())
        )
        if base is True:
            return True
        if not base:
            base = []
        elif isinstance(base, str):
            base = [base]
        else:
            base = list(base)

        organization_field = getattr(self, "organization_field", None)
        if organization_field and organization_field not in base:
            base.append(organization_field)
        return tuple(base)

    @admin.display(description=_("Organization ID"))
    def organization_id_display(self, obj):
        org = getattr(obj, self.organization_field, None)
        return org.id if org else "-"

    @admin.display(description=_("Organization name"))
    def organization_name_display(self, obj):
        org = getattr(obj, self.organization_field, None)
        return org.name if org else "-"


class OrganizationWhereActionAdminMixin:
    organization_field = "organization_where_action_taken"

    def get_list_select_related(self, request):
        related = getattr(super(), "get_list_select_related", None)
        base = (
            related(request)
            if callable(related)
            else getattr(self, "list_select_related", ())
        )
        if base is True:
            return True
        if not base:
            base = []
        elif isinstance(base, str):
            base = [base]
        else:
            base = list(base)

        organization_field = getattr(self, "organization_field", None)
        if organization_field and organization_field not in base:
            base.append(organization_field)
        return tuple(base)

    @admin.display(description=_("Organization ID"))
    def organization_id_display(self, obj):
        org = getattr(obj, self.organization_field, None)
        return org.id if org else "-"

    @admin.display(description=_("Organization name"))
    def organization_name_display(self, obj):
        org = getattr(obj, self.organization_field, None)
        return org.name if org else "-"


class DualOrganizationAdminMixin:
    def get_list_select_related(self, request):
        related = getattr(super(), "get_list_select_related", None)
        base = (
            related(request)
            if callable(related)
            else getattr(self, "list_select_related", ())
        )
        if base is True:
            return True
        if not base:
            base = []
        elif isinstance(base, str):
            base = [base]
        else:
            base = list(base)

        for field in ("organization_creator", "organization_register"):
            if field not in base:
                base.append(field)
        return tuple(base)

    @admin.display(description=_("Creator Org ID"))
    def organization_creator_id_display(self, obj):
        return obj.organization_creator.id if obj.organization_creator else "-"

    @admin.display(description=_("Creator Org name"))
    def organization_creator_name_display(self, obj):
        return obj.organization_creator.name if obj.organization_creator else "-"

    @admin.display(description=_("Register Org ID"))
    def organization_register_id_display(self, obj):
        return obj.organization_register.id if obj.organization_register else "-"

    @admin.display(description=_("Register Org name"))
    def organization_register_name_display(self, obj):
        return obj.organization_register.name if obj.organization_register else "-"


@admin.action(description="Regenerate QR")
def regenerate_qr_codes(admin, request, queryset):
    for instance in queryset:
        update_qr_instance(
            instance.shelf_object_url,
            instance,
            instance.in_where_laboratory.organization.pk,
        )


class ShelfObject_Admin(admin.ModelAdmin):
    list_display = ("id", "object", "quantity", "measurement_unit")
    actions = [regenerate_qr_codes]


class Object_Admin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ("code", "name", "type", "is_precursor")


@admin.action(description="Run new informs utilities")
def create_informs(admin, request, queryset):
    for instance in queryset:
        create_informsperiods(instance)


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


class UserOrganizationInline(admin.TabularInline):
    model = models.UserOrganization
    extra = 1


@admin.register(models.OrganizationStructureRelations)
class OrganizationStructureRelationsAdmin(OrganizationInfoAdminMixin, admin.ModelAdmin):
    list_display = [
        "id",
        "organization_id_display",
        "organization_name_display",
        "content_type",
        "object_id",
        "content_object_display",
    ]
    list_filter = [("content_type", admin.RelatedOnlyFieldListFilter), "organization"]
    search_fields = ["organization__name", "object_id"]

    def content_object_display(self, obj):
        return str(obj.content_object) if obj.content_object else "-"

    content_object_display.short_description = _("Related object")


class SDSTraceabilityAdmin(admin.ModelAdmin):
    list_display = [
        "sustance_characteristics__obj__name",
        "source",
        "revision_date",
        "creation_date",
    ]
    list_filter = ["source"]
    search_fields = ["sustance_characteristics__cas_id_number"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "sustance_characteristics":
            kwargs["queryset"] = models.SustanceCharacteristics.objects.order_by("-id")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SustanceCharacteristicsAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "obj__name",
        "obj__code",
        "cas_id_number",
    ]
    list_filter = ["obj__name", "cas_id_number", "h_code"]
    search_fields = [
        "obj__name",
        "obj__code",
        "cas_id_number",
    ]


@admin.register(models.UserOrganization)
class UserOrganizationAdmin(OrganizationInfoAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "organization_id_display",
        "organization_name_display",
        "type_in_organization",
        "status",
    )
    list_filter = (
        "status",
        "type_in_organization",
        "organization",
    )
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "organization__name",
    )
    list_select_related = ("user", "organization")
    ordering = ("pk",)


@admin.register(models.Laboratory)
class LaboratoryAdmin(OrganizationInfoAdminMixin, admin.ModelAdmin):
    actions = [export_laboratory]
    search_fields = ["name", "organization__name"]
    list_filter = ["organization"]
    list_display = (
        "id",
        "name",
        "organization_id_display",
        "organization_name_display",
        "phone_number",
        "email",
        "responsible",
    )


@admin.register(models.Object)
class ObjectAdmin(OrganizationInfoAdminMixin, admin.ModelAdmin):
    search_fields = ["code", "name", "organization__name"]
    list_display = (
        "id",
        "code",
        "name",
        "organization_id_display",
        "organization_name_display",
        "type",
        "is_precursor",
        "is_public",
    )
    list_filter = ("type", "is_public", "is_dangerous", "organization")


@admin.register(models.ShelfObjectEquipmentCharacteristics)
class ShelfObjectEquipmentCharacteristicsAdmin(
    OrganizationInfoAdminMixin, admin.ModelAdmin
):
    list_display = (
        "id",
        "shelfobject",
        "organization_id_display",
        "organization_name_display",
        "provider",
        "equipment_price",
        "available_to_use",
        "have_guarantee",
    )
    search_fields = (
        "shelfobject__object__name",
        "shelfobject__object__code",
        "organization__name",
        "provider__name",
    )
    list_filter = ("available_to_use", "have_guarantee", "organization")


@admin.register(models.ShelfObjectMaintenance)
class ShelfObjectMaintenanceAdmin(OrganizationInfoAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "shelfobject",
        "organization_id_display",
        "organization_name_display",
        "maintenance_date",
        "provider_of_maintenance",
        "validator",
    )
    search_fields = (
        "shelfobject__object__name",
        "shelfobject__object__code",
        "organization__name",
        "provider_of_maintenance__name",
    )
    list_filter = ("maintenance_date", "organization")


@admin.register(models.ShelfObjectLog)
class ShelfObjectLogAdmin(OrganizationInfoAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "shelfobject",
        "organization_id_display",
        "organization_name_display",
        "description",
    )
    search_fields = (
        "shelfobject__object__name",
        "shelfobject__object__code",
        "organization__name",
        "description",
    )
    list_filter = ("organization",)


@admin.register(models.ShelfObjectCalibrate)
class ShelfObjectCalibrateAdmin(OrganizationInfoAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "shelfobject",
        "organization_id_display",
        "organization_name_display",
        "calibrate_name",
        "validator",
        "calibration_date",
    )
    search_fields = (
        "shelfobject__object__name",
        "shelfobject__object__code",
        "organization__name",
        "calibrate_name",
    )
    list_filter = ("calibration_date", "organization")


@admin.register(models.ShelfObjectTraining)
class ShelfObjectTrainingAdmin(OrganizationInfoAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "shelfobject",
        "organization_id_display",
        "organization_name_display",
        "training_initial_date",
        "training_final_date",
        "number_of_hours",
        "place",
    )
    search_fields = (
        "shelfobject__object__name",
        "shelfobject__object__code",
        "organization__name",
        "place",
    )
    list_filter = ("training_initial_date", "training_final_date", "organization")


@admin.register(models.ShelfObjectGuarantee)
class ShelfObjectGuaranteeAdmin(OrganizationInfoAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "shelfobject",
        "organization_id_display",
        "organization_name_display",
        "guarantee_initial_date",
        "guarantee_final_date",
    )
    search_fields = (
        "shelfobject__object__name",
        "shelfobject__object__code",
        "organization__name",
    )
    list_filter = ("guarantee_initial_date", "guarantee_final_date", "organization")


@admin.register(models.Inform)
class InformAdmin(OrganizationInfoAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "organization_id_display",
        "organization_name_display",
        "custom_form",
        "status",
        "content_type",
        "object_id",
    )
    search_fields = (
        "name",
        "organization__name",
        "custom_form__name",
        "object_id",
    )
    list_filter = ("status", "organization", ("content_type", admin.RelatedOnlyFieldListFilter))


class PeriodScheduledAdmin(admin.TabularInline):
    model = models.InformsPeriod
    extra = 0


@admin.action(description="Run new informs utilities")
def create_informs(admin, request, queryset):
    for instance in queryset:
        create_informsperiods(instance)


@admin.register(models.InformScheduler)
class InformSchedulerAdmin(OrganizationInfoAdminMixin, admin.ModelAdmin):
    search_fields = [
        "name",
        "organization__name",
    ]
    list_display = [
        "id",
        "name",
        "organization_id_display",
        "organization_name_display",
        "start_application_date",
        "close_application_date",
        "period_on_days",
        "active",
    ]
    list_filter = ("active", "organization")
    actions = [create_informs]
    inlines = [PeriodScheduledAdmin]


@admin.register(models.ObjectLogChange)
class ObjectLogAdmin(OrganizationWhereActionAdminMixin, admin.ModelAdmin):
    list_display = [
        "id",
        "object",
        "laboratory",
        "user_display",
        "organization_id_display",
        "organization_name_display",
        "old_value",
        "new_value",
        "diff_value",
        "measurement_unit",
        "update_time",
    ]

    @admin.display(description=_("User"), ordering="user")
    def user_display(self, obj):
        if obj.deleted_user_info:
            return f"{obj.user} ({obj.deleted_user_info})"
        return str(obj.user)

    search_fields = [
        "object__name",
        "object__code",
        "laboratory__name",
        "user__username",
        "organization_where_action_taken__name",
        "deleted_user_info",
    ]
    list_filter = [
        "update_time",
        "organization_where_action_taken",
        "precursor",
        "type_action",
        ("deleted_user_info", admin.EmptyFieldListFilter),
    ]


@admin.register(models.RegisterUserQR)
class RegisterUserQRAdmin(DualOrganizationAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "code",
        "created_by",
        "role",
        "activate_user",
        "organization_creator_id_display",
        "organization_creator_name_display",
        "organization_register_id_display",
        "organization_register_name_display",
        "url",
    )
    search_fields = (
        "code",
        "url",
        "created_by__username",
        "role__name",
        "organization_creator__name",
        "organization_register__name",
    )
    list_filter = (
        "activate_user",
        "organization_creator",
        "organization_register",
    )


@admin.register(models.InformsPeriod)
class InformsPeriodAdmin(OrganizationInfoAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "scheduler",
        "organization_id_display",
        "organization_name_display",
        "inform_template",
        "start_application_date",
        "close_application_date",
        "creation_date",
    )
    search_fields = (
        "scheduler__name",
        "organization__name",
        "inform_template__name",
    )
    list_filter = (
        "organization",
        "start_application_date",
        "close_application_date",
    )


@admin.register(models.ShelfObject)
class ShelfObjectAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "object",
        "quantity",
        "is_box",
        "quantity_units",
        "measurement_unit",
        "laboratory_name_display",
        "organization_id_display",
        "organization_name_display",
    )
    search_fields = (
        "object__name",
        "object__code",
        "in_where_laboratory__name",
        "in_where_laboratory__organization__name",
    )
    list_filter = (
        "measurement_unit",
        "in_where_laboratory",
        "in_where_laboratory__organization",
    )
    actions = [regenerate_qr_codes]
    list_select_related = (
        "object",
        "measurement_unit",
        "in_where_laboratory",
        "in_where_laboratory__organization",
    )

    @admin.display(description=_("Laboratory"), ordering="in_where_laboratory__name")
    def laboratory_name_display(self, obj):
        return obj.in_where_laboratory.name if obj.in_where_laboratory else "-"

    @admin.display(
        description=_("Organization ID"),
        ordering="in_where_laboratory__organization__id",
    )
    def organization_id_display(self, obj):
        org = getattr(obj.in_where_laboratory, "organization", None)
        return org.id if org else "-"

    @admin.display(
        description=_("Organization name"),
        ordering="in_where_laboratory__organization__name",
    )
    def organization_name_display(self, obj):
        org = getattr(obj.in_where_laboratory, "organization", None)
        return org.name if org else "-"


@admin.register(models.ObjectFeatures)
class ObjectFeaturesAdmin(admin.ModelAdmin):
    search_fields = ("name", "description")
    list_display = ("id", "name", "description")


@admin.register(models.Protocol)
class ProtocolAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "laboratory", "upload_by", "creation_date")
    search_fields = (
        "name",
        "short_description",
        "laboratory__name",
        "upload_by__username",
    )
    list_filter = ("laboratory", "creation_date")


@admin.register(models.LaboratoryRoom)
class LaboratoryRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "laboratory", "created_by", "creation_date")
    search_fields = ("name", "laboratory__name")
    list_filter = ("laboratory",)


@admin.register(models.Furniture)
class FurnitureAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "labroom", "type", "created_by", "creation_date")
    search_fields = ("name", "labroom__name", "labroom__laboratory__name")
    list_filter = ("type", "labroom")


@admin.register(models.Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "furniture",
        "type",
        "quantity",
        "measurement_unit",
        "discard",
        "infinity_quantity",
    )
    search_fields = ("name", "furniture__name", "furniture__labroom__name")
    list_filter = ("type", "discard", "infinity_quantity", "furniture")


@admin.register(models.Catalog)
class CatalogAdmin(admin.ModelAdmin):
    list_display = ("id", "key", "description")
    search_fields = ("key", "description")
    list_filter = ("key",)


@admin.register(models.BlockedListNotification)
class BlockedListNotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "object", "laboratory", "user")
    search_fields = (
        "object__name",
        "object__code",
        "laboratory__name",
        "user__username",
    )
    list_filter = ("laboratory", "user")


@admin.register(models.Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "phone_number",
        "email",
        "legal_identity",
        "laboratory",
    )
    search_fields = ("name", "email", "legal_identity", "laboratory__name")
    list_filter = ("laboratory",)


@admin.register(models.TranferObject)
class TranferObjectAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "object",
        "laboratory_send",
        "laboratory_received",
        "quantity",
        "status",
        "state",
        "mark_as_discard",
        "update_time",
    )
    search_fields = (
        "object__object__name",
        "object__object__code",
        "laboratory_send__name",
        "laboratory_received__name",
    )
    list_filter = (
        "status",
        "state",
        "mark_as_discard",
        "laboratory_send",
        "laboratory_received",
    )


@admin.register(models.ShelfObjectObservation)
class ShelfObjectObservationAdmin(admin.ModelAdmin):
    list_display = ("id", "shelf_object", "action_taken", "created_by", "creation_date")
    search_fields = (
        "shelf_object__object__name",
        "shelf_object__object__code",
        "action_taken",
        "description",
    )
    list_filter = ("action_taken", "creation_date")


@admin.register(models.ObjectMaximumLimit)
class ObjectMaximumLimitAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "laboratory",
        "object",
        "quantity",
        "measurement_unit",
        "process_condition",
        "created_at",
    )
    search_fields = (
        "laboratory__name",
        "object__name",
        "object__code",
    )
    list_filter = ("laboratory", "measurement_unit", "process_condition", "created_at")


@admin.register(models.ReactiveLimit)
class ReactiveLimitAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "laboratory",
        "object",
        "minimum_limit",
        "maximum_limit",
        "measurement_unit",
    )
    search_fields = (
        "laboratory__name",
        "object__name",
        "object__code",
    )
    list_filter = ("laboratory", "measurement_unit")


class UserOrganizationInline(admin.TabularInline):
    model = models.UserOrganization
    fields = ("user", "type_in_organization", "status")
    extra = 1
    autocomplete_fields = ("user",)


@admin.register(models.OrganizationStructure)
class OrganizationStructureAdmin(admin.ModelAdmin):
    list_display = ("indented_name", "parent", "level", "position", "active")
    list_filter = ("active", "level")
    search_fields = ("name",)
    list_editable = ("active",)
    ordering = ("level", "position", "name")
    fields = ("name", "parent", "position", "level", "active", "rol")
    readonly_fields = ("level", "position")
    filter_horizontal = ("rol",)
    autocomplete_fields = ("parent",)
    inlines = [UserOrganizationInline]

    def indented_name(self, obj):
        indent = "—" * obj.level
        return f"{indent} {obj.name}" if obj.level else obj.name

    indented_name.short_description = "Name"


@admin.register(models.LabOrOrgRequest)
class LabOrOrgRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "entity_type",
        "status",
        "requested_by",
        "requested_at",
        "organization",
    )
    list_filter = ("entity_type", "status", "organization")
    search_fields = (
        "name",
        "requested_by__username",
        "requested_by__first_name",
        "requested_by__last_name",
        "organization__name",
    )
    readonly_fields = ("requested_at", "requested_by")
    list_select_related = ("requested_by", "organization")


class LabOrgReassignedOnUserDeleteFilter(admin.SimpleListFilter):
    title = _("Reassigned on user delete")
    parameter_name = "reassigned_on_user_delete"

    def lookups(self, request, model_admin):
        return (("yes", _("Yes")),)

    def queryset(self, request, queryset):
        if self.value() == "yes":
            marker_query = Q()
            for marker in DELETED_USER_TAG_MARKERS:
                marker_query |= Q(log_entry__object_repr__icontains=marker)
            return queryset.filter(marker_query)
        return queryset


class LabOrgLogEntryAdmin(admin.ModelAdmin):
    list_display = ["log_entry", "content_object"]
    search_fields = ["log_entry__object_repr", "log_entry__user__username"]
    list_filter = [LabOrgReassignedOnUserDeleteFilter]


admin.site.register(models.PrecursorReport, PrecursorReportAdmin)
admin.site.register(models.PrecursorReportValues, PrecursorReportValuesAdmin)
admin.site.register(models.SDSTraceability, SDSTraceabilityAdmin)
admin.site.register(models.ShelfObjectLimits)
admin.site.register(models.LabOrgLogEntry, LabOrgLogEntryAdmin)
admin.site.register(models.SustanceCharacteristics, SustanceCharacteristicsAdmin)
admin.site.site_header = _("Organilab Administration site")
