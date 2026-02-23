from django import template
from django.shortcuts import get_object_or_404
from risk_management.models import Buildings, IncidentReport, RiskZone

register = template.Library()


@register.simple_tag()
def get_incidents(building):
    building = get_object_or_404(Buildings, pk=building)
    total = IncidentReport.objects.filter(buildings=building).count()
    return total


@register.simple_tag()
def get_incidents_by_zone(zone_pk):
    return zone_pk
