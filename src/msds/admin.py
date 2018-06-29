from django.contrib import admin
from msds.models import MSDSObject

# Register your models here.


class msdsAdmin(admin.ModelAdmin):
    search_fields = ['provider', 'product']
    list_display = ['provider', 'product']


admin.site.register(MSDSObject, msdsAdmin)
