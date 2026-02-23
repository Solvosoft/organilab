from django.contrib import admin

from .models import PendingTask


@admin.register(PendingTask)
class PendingTaskAdmin(admin.ModelAdmin):
    list_display = ['description', 'status', 'profile', 'creation_date']
    list_filter = ['status', 'creation_date']
    search_fields = ['description']
    raw_id_fields = ['profile', 'organization', 'created_by']
    readonly_fields = ['creation_date', 'last_update']
