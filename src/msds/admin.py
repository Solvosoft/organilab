from django.contrib import admin
from msds.models import OrganilabNode, RegulationDocument


class OrganilabNodeMPTTAdmin(admin.ModelAdmin):
    mptt_level_indent = 20


admin.site.register(OrganilabNode, OrganilabNodeMPTTAdmin)
admin.site.register(RegulationDocument)
