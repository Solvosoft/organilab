from rest_framework import serializers
from reservations_management.models import ReservedProducts, Reservations
from laboratory.models import ShelfObject
#from djgentelella.fields.drfdatetime import DateTimeRangeTextWidget
#from django_filters import FilterSet

class ReservedProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReservedProducts
        fields = '__all__'

class PeservedProductsSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReservedProducts
        fields = "__all__"


class ReservedProductsDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ReservedProductSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)

class ReservedProductsFilterSet(FilterSet):
    #initial_date = DateTimeFromToRangeFilter(widget=DateTimeRangeTextWidget(attrs={'placeholder': 'YYYY/MM/DD'}))
    #final_time = DateTimeFromToRangeFilter(widget=DateTimeRangeTextWidget(attrs={'placeholder': 'YYYY/MM/DD HH:MM:SS'}))

    class Meta:
        model = ReservedProducts
        fields = {'shelf_object': ['icontains'], 'amount_required': ['icontains'],'status':['icontains']}

