from django.contrib import admin

from presentation.models import Donation
from presentation.models import FeedbackEntry


class DonationAdmin(admin.ModelAdmin):
    search_fields = ["details"]


admin.site.register(FeedbackEntry)
admin.site.register(Donation, DonationAdmin)
