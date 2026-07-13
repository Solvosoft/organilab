import zipfile

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from django.core import serializers
from django.db.models import Q
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
import io
from djgentelella.admin import LogEntryAdmin as DjgentelellaLogEntryAdmin
from auth_and_perms import models
from auth_and_perms.utils import preserve_audit_trail_before_delete

# Matches the tag preserve_audit_trail_before_delete stamps on object_repr,
# in either language it may have been written in (translation is resolved
# at delete time, not lazily, so old rows can be in either language).
DELETED_USER_TAG_MARKERS = ("Usuario eliminado", "Deleted user")


class ReassignedOnUserDeleteFilter(admin.SimpleListFilter):
    title = _("Reassigned on user delete")
    parameter_name = "reassigned_on_user_delete"

    def lookups(self, request, model_admin):
        return (("yes", _("Yes")),)

    def queryset(self, request, queryset):
        if self.value() == "yes":
            marker_query = Q()
            for marker in DELETED_USER_TAG_MARKERS:
                marker_query |= Q(object_repr__icontains=marker)
            return queryset.filter(marker_query)
        return queryset


class ExtendedLogEntryAdmin(DjgentelellaLogEntryAdmin):
    # Adds object_repr so entries reassigned/tagged on user delete (see
    # preserve_audit_trail_before_delete) are searchable by the original
    # user's name, not just by the (now reassigned) user__username.
    search_fields = tuple(DjgentelellaLogEntryAdmin.search_fields) + ("object_repr",)
    list_filter = tuple(DjgentelellaLogEntryAdmin.list_filter) + (
        ReassignedOnUserDeleteFilter,
    )


@admin.action(description="Export Laboratory")
def export_rol_perms(admin, request, queryset):
    buffer = io.BytesIO()
    zip_file = zipfile.ZipFile(buffer, "w")

    for rol in queryset:
        rols = models.ProfilePermission.objects.filter(rol=rol)
        zip_file.writestr(rol.name + ".json", serializers.serialize("json", rols))
    zip_file.close()
    buffer.seek(0)
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/x-zip-compressed",
        headers={"Content-Disposition": 'attachment; filename="permissionsrol.zip"'},
    )
    return response


class RolAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "color", "description"]
    search_fields = ["name", "description"]
    filter_horizontal = ["permissions"]
    actions = [export_rol_perms]


class AuthorizedApplicationAdmin(admin.ModelAdmin):
    list_display = ["name", "auth_token"]

    @admin.display(empty_value="unknown")
    def auth_token(self, obj):
        if obj.user:
            return obj.user.auth_token.key
        return "unknown"


class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "job_position",
        "phone_number",
        "language",
        "show_tutorials",
    ]
    list_select_related = ["user"]
    list_filter = ["language", "show_tutorials"]
    search_fields = [
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "id_card",
        "job_position",
    ]


class ProfilePermissionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "profile",
        "content_type",
        "object_id",
        "organization",
        "roles_display",
    ]
    list_filter = [
        ("content_type", admin.RelatedOnlyFieldListFilter),
        ("organization", admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        "profile__user__username",
        "profile__user__email",
        "rol__name",
        "organization__name",
    ]
    raw_id_fields = ["profile", "organization"]
    filter_horizontal = ["rol"]

    @admin.display(description=_("Roles"))
    def roles_display(self, obj):
        return ", ".join(obj.rol.values_list("name", flat=True))


class ImpostorAdmin(admin.ModelAdmin):
    search_fields = ["impostor__username", "imposted_as__username"]
    list_display = ["__str__", "impostor_ip", "logged_in", "logged_out"]
    date_hierarchy = "logged_in"


class UserAdmin(DjangoUserAdmin):
    def delete_model(self, request, obj):
        preserve_audit_trail_before_delete(obj)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            preserve_audit_trail_before_delete(obj)
        super().delete_queryset(request, queryset)


admin.site.register(models.AuthorizedApplication, AuthorizedApplicationAdmin)
admin.site.register(models.Profile, ProfileAdmin)
admin.site.register(models.Rol, RolAdmin)
admin.site.register(models.ProfilePermission, ProfilePermissionAdmin)
admin.site.register(models.ImpostorLog, ImpostorAdmin)
admin.site.register(models.GroupDescription)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
