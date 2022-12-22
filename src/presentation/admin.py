from django.contrib import admin

from presentation.models import Donation


class DonationAdmin(admin.ModelAdmin):
    search_fields = ['details']


admin.site.register(Donation, DonationAdmin)