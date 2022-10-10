from django.contrib import admin
from msds.models import MSDSObject, OrganilabNode, RegulationDocument


class msdsAdmin(admin.ModelAdmin):
    search_fields = ['provider', 'product']
    list_display = ['provider', 'product']


class OrganilabNodeMPTTAdmin(admin.ModelAdmin):
    mptt_level_indent = 20


admin.site.register(OrganilabNode, OrganilabNodeMPTTAdmin)
admin.site.register(MSDSObject, msdsAdmin)
admin.site.register(RegulationDocument)