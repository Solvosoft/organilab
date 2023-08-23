from django.db.models import Q
from django_filters import FilterSet, DateTimeFromToRangeFilter, CharFilter
from djgentelella.fields.drfdatetime import DateTimeRangeTextWidget
from rest_framework import serializers

from laboratory.models import ShelfObject, Object, Shelf
from laboratory.shelfobject.serializers import CatalogDetailSerializer


class ObjectContainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Object
        fields = ['id', 'name']

class ShelfContainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shelf
        fields = ['id', 'name']

class ContainerFilter(FilterSet):
    creation_date = DateTimeFromToRangeFilter(
        widget=DateTimeRangeTextWidget(attrs={'placeholder': 'YYYY/MM/DD HH:MM:SS'}))
    created_by = CharFilter(field_name='created_by', method='filter_user')

    def filter_user(self, queryset, name, value):
        return queryset.filter(Q(created_by__first_name__icontains=value) | Q(
            created_by__last_name__icontains=value) | Q(
            created_by__username__icontains=value))
    class Meta:
        model = ShelfObject
        fields  = {'id': ['exact'],
                   'object__name': ['icontains'],
                   'status__description': ['icontains'],
                   'measurement_unit__description': ['icontains'],
                   }

class ContainerListSerializer(serializers.ModelSerializer):
    object = ObjectContainerSerializer()
    shelf = ShelfContainerSerializer()
    status = CatalogDetailSerializer()
    measurement_unit = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    def get_created_by(self, obj):
        name = None
        if obj.created_by:
            name = obj.created_by.get_full_name()
            if not name:
                name = obj.created_by.username
        return name or ''

    def get_measurement_unit(self, obj):
        return obj.get_measurement_unit_display()

    class Meta:
        model = ShelfObject
        fields = ['id', 'object', 'shelf', 'status', 'measurement_unit', 'created_by',
                  'creation_date']

class ContainerDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ContainerListSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)
