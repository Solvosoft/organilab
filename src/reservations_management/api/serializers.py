from django_filters.rest_framework import FilterSet, DateFromToRangeFilter
from djgentelella.fields.drfdatetime import DateTimeRangeTextWidget
from rest_framework import serializers

from reservations_management.models import ReservedProducts


class ReservedProductSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    initial_date = serializers.DateTimeField(format='%d/%m/%y %H:%M:%S')
    shelf_object = serializers.SerializerMethodField()
    action = serializers.SerializerMethodField()
    def get_status(self,obj=None):
        return obj.get_status_display()

    def get_action(self,obj=None):
        return "ELIMINAR"
    def get_shelf_object(self,obj=None):
        return obj.shelf_object.object.name
    class Meta:
        model = ReservedProducts
        fields = '__all__'



class ReservedProductsDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ReservedProductSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class ReservedProductsFilterSet(FilterSet):

    initial_date = DateFromToRangeFilter(widget=DateTimeRangeTextWidget(attrs={'placeholder': 'YYYY/MM/DD'}))
    final_time = DateFromToRangeFilter(widget=DateTimeRangeTextWidget(attrs={'placeholder': 'YYYY/MM/DD HH:MM:SS'}))

    class Meta:
        model = ReservedProducts
        fields = {'shelf_object__object__name': ['icontains'], 'amount_required': ['icontains'], 'status': ['icontains']}

