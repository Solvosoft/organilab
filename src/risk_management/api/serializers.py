from django.db.models import Q
from django.urls import reverse
from django_filters.rest_framework import FilterSet
from rest_framework import serializers
from risk_management.models import RiskZone, ZoneType, PriorityConstrain
from django.utils.translation import gettext as _


class RiskZoneShowUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskZone
        exclude = ['priority']


class RiskZoneTableSerializer(serializers.ModelSerializer):
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
    data = serializers.ListField(child=RiskZoneTableSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class RiskZoneFilterSet(FilterSet):
    class Meta:
        model = RiskZone
        fields = {'name': ['icontains']}


class ZoneTypeShowUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZoneType
        fields = '__all__'


class ZoneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZoneType
        fields = ['name', 'priority_validator']


class ZoneTypeTableSerializer(serializers.ModelSerializer):
    action = serializers.SerializerMethodField()
    priority_validator = serializers.SerializerMethodField()

    def get_priority_validator(self, obj=None):
        salida = """<ul>"""
        for p in obj.priority_validator.all():
            salida += """<li>{item}</li>""".format(item=p.__str__())
        salida += """</ul>"""
        return salida

    def get_action(self, obj=None):
        html = """
        <button class="btn btn-outline-info"
                         data-bs-toggle="modal"
                         onclick="show_zone_type({pk})"
                         data-bs-target="#update_zone_type_modal"
                         aria-label="{edit}">
                        <i class="fa fa-pencil-square-o" aria-hidden="true"></i>{edit}</button>

                   <a class="btn btn-outline-danger" onclick="delete_zone_type({pk})">
                            <i class="fa fa-times" 
                            aria-hidden="true"></i> {delete} </a>""".format(pk=obj.pk,
                                                                            edit=_("Edit"),
                                                                            delete=_("Remove"), )

        return html

    class Meta:
        model = ZoneType

        fields = ['name', 'action', 'priority_validator']


class ZoneTypeDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ZoneTypeTableSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class ZoneTypeFilterSet(FilterSet):
    class Meta:
        model = ZoneType
        fields = {'name': ['icontains']}
