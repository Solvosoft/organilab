from django.contrib import admin

from risk_management.models import PriorityConstrain, ZoneType, RiskZone, \
    IncidentReport, Buildings
from sga.models import HCodeCategory

admin.site.register(PriorityConstrain)
admin.site.register(ZoneType)
admin.site.register(RiskZone)
admin.site.register(IncidentReport)
admin.site.register(HCodeCategory)
admin.site.register(Buildings)
