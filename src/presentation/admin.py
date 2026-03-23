from django.contrib import admin

from presentation.models import Donation, FeedbackEntry, Tutorial, TutorialStep, TutorialProgress


class DonationAdmin(admin.ModelAdmin):
    search_fields = ["details"]


class TutorialStepInline(admin.TabularInline):
    model = TutorialStep
    extra = 1
    ordering = ['order']
    fields = ['order', 'step_key', 'title', 'content', 'step_type',
              'css_selector', 'position', 'action_url', 'image']


class TutorialAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'chapter', 'url_name', 'is_active',
                    'auto_start', 'order']
    list_filter = ['chapter', 'is_active', 'auto_start']
    search_fields = ['title', 'slug', 'description']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['target_roles']
    inlines = [TutorialStepInline]


class TutorialProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'tutorial', 'completed', 'current_step',
                    'dismissed', 'started_at', 'completed_at']
    list_filter = ['completed', 'dismissed']
    readonly_fields = ['user', 'tutorial', 'completed', 'current_step',
                       'started_at', 'completed_at', 'dismissed']


admin.site.register(FeedbackEntry)
admin.site.register(Donation, DonationAdmin)
admin.site.register(Tutorial, TutorialAdmin)
admin.site.register(TutorialProgress, TutorialProgressAdmin)
