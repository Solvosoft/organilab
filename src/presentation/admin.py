from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.utils.translation import gettext_lazy as _

from presentation.models import (
    Donation,
    FeedbackEntry,
    Tutorial,
    TutorialStep,
    TutorialProgress,
)


class DonationAdmin(admin.ModelAdmin):
    search_fields = ["details"]


class TutorialStepInline(admin.TabularInline):
    model = TutorialStep
    extra = 1
    ordering = ["order"]
    fields = [
        "order",
        "step_key",
        "title",
        "content",
        "step_type",
        "css_selector",
        "position",
        "action_url",
        "image",
    ]


class TutorialAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "slug",
        "chapter",
        "url_name",
        "is_active",
        "auto_start",
        "order",
    ]
    list_filter = ["chapter", "is_active", "auto_start"]
    search_fields = ["title", "slug", "description"]
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ["target_roles"]
    inlines = [TutorialStepInline]


class TutorialProgressAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "tutorial",
        "completed",
        "current_step",
        "dismissed",
        "started_at",
        "completed_at",
    ]
    list_filter = ["completed", "dismissed"]
    readonly_fields = [
        "user",
        "tutorial",
        "completed",
        "current_step",
        "started_at",
        "completed_at",
        "dismissed",
    ]


class FeedbackEntryAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "user", "laboratory_id"]
    search_fields = ["id", "title", "user__username", "user__email"]
    readonly_fields = [
        "title",
        "user",
        "laboratory_id",
        "explanation_rendered",
        "file_preview",
    ]
    fieldsets = [
        (
            None,
            {
                "fields": ["title", "user", "laboratory_id"],
            },
        ),
        (
            _("Content"),
            {
                "fields": ["explanation_rendered", "file_preview"],
            },
        ),
    ]

    def explanation_rendered(self, obj):
        if obj.explanation:
            html = obj.explanation.replace("../media/", settings.MEDIA_URL)
            return mark_safe(
                f'<div style="border:1px solid #ccc;border-radius:4px;padding:12px;min-height:60px">'
                f"{html}</div>"
            )
        return "-"

    explanation_rendered.short_description = _("Explanation")

    def file_preview(self, obj):
        if obj.related_file:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.related_file.url,
                obj.related_file.name,
            )
        return "-"

    file_preview.short_description = _("Related file")

    def has_add_permission(self, request):
        return False


admin.site.register(FeedbackEntry, FeedbackEntryAdmin)
admin.site.register(Donation, DonationAdmin)
admin.site.register(Tutorial, TutorialAdmin)
admin.site.register(TutorialProgress, TutorialProgressAdmin)
