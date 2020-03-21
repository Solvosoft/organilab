from django.contrib import admin

from risk_management.models import PriorityConstrain, ZoneType, RiskZone

admin.site.register(PriorityConstrain)
admin.site.register(ZoneType )
admin.site.register(RiskZone )
