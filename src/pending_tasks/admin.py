from django.contrib import admin

from pending_tasks.models import PendingTask, PendingTaskManager


@admin.register(PendingTask)
class PendingTaskAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        # "description",
        "status",
        "profile",
        "is_archived",
        "creation_date",
        "last_update",
    ]
    list_filter = ["status", "is_archived", "creation_date"]
    search_fields = ["name", "description"]
    raw_id_fields = ["profile", "created_by"]
    readonly_fields = ["creation_date", "last_update"]
    list_editable = ["status", "is_archived"]
    date_hierarchy = "creation_date"


class PendingTaskManagerAdmin(admin.ModelAdmin):
    list_display = ["id", "task", "content_type", "object_id"]
    list_filter = ["task", "content_type", "object_id"]
    search_fields = ["task", "content_type", "object_id"]


admin.site.register(PendingTaskManager, PendingTaskManagerAdmin)
