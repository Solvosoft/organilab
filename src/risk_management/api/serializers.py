from django.db.models import Q
from django.urls import reverse
from django_filters.rest_framework import FilterSet
from rest_framework import serializers
from risk_management.models import RiskZone, ZoneType
from django.utils.translation import gettext as _


class RiskZoneShowUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskZone
        exclude = ['priority']


class RiskZoneSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    action = serializers.SerializerMethodField()
    laboratories_count = serializers.SerializerMethodField()

    def get_name(self, obj=None):
        return """<a href="{urlupdate}">{name}</a>""".format(name=obj.name,
                                                             urlupdate=reverse(
                                                                 'riskmanagement:riskzone_update',
                                                                 kwargs={'pk': obj.pk}))

    def get_laboratories_count(self, obj=None):
        return """<span class ="fs-6 prior_{priority} badge">
                    {lab_count}
                    </span >""".format(priority=obj.priority,
                                       lab_count=obj.laboratories.all().count())

    def get_action(self, obj=None):
        html = """
        <button class="btn btn-warning text-white risk_zone_input"
                         data-bs-toggle="modal"
                         onclick="show_risk_zone({pk})"
                         data-bs-target="#update_zone_risk_modal"
                         aria-label="{edit}">
                        <i class="fa fa-pencil-square-o" aria-hidden="true"></i>{edit}</button>
                        
                    <input type="hidden" id="id_{pk}"  name="id_risk_zone" value="{pk}">      
                   <a class="btn btn-danger text-white"
                        href="{urldelete}">
                            <i class="fa fa-times" 
                            aria-hidden="true"></i> {delete} </a>""".format(pk=obj.pk,
                                                                            edit=_("Edit"),
                                                                            delete=_("Remove"),
                                                                            urledit=reverse(
                                                                                'riskmanagement:riskzone_update',
                                                                                kwargs={
                                                                                    'pk': obj.pk}),
                                                                            urldelete=reverse(
                                                                                'riskmanagement:riskzone_delete',
                                                                                kwargs={
                                                                                    'pk': obj.pk}),
                                                                            )

        return html

    class Meta:
        model = RiskZone

        fields = ['name', 'action', 'laboratories_count']


class RiskZoneDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=RiskZoneSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class RiskZoneFilterSet(FilterSet):
    class Meta:
        model = RiskZone
        fields = {'name': ['icontains']}


class ZoneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZoneType
        fields = ['name', 'priority_validator']
