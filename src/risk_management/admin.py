from django.contrib import admin

from risk_management.models import PriorityConstrain, ZoneType, RiskZone, \
    IncidentReport, Buildings, EstablishmentLogs
from sga.models import HCodeCategory

class EstablishmentLogsAdmin(admin.ModelAdmin):
    list_display = ['id', 'content_type', 'object_id', 'date']
    list_filter = ['date', 'content_type']
    fields = ['content_type', 'object_id', 'physical', 'health',
              'environmental', 'establishment_status', 'table_content', 'date']

admin.site.register(PriorityConstrain)
admin.site.register(ZoneType)
admin.site.register(RiskZone)
admin.site.register(IncidentReport)
admin.site.register(HCodeCategory)
admin.site.register(Buildings)
admin.site.register(EstablishmentLogs, EstablishmentLogsAdmin)
