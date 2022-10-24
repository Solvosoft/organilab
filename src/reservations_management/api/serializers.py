
from datetime import datetime

from django.db.models import Q
from django_filters.rest_framework import FilterSet, DateFromToRangeFilter, DateTimeFromToRangeFilter
from djgentelella.fields.drfdatetime import DateTimeRangeTextWidget, DateRangeTextWidget
from rest_framework import serializers

from reservations_management.models import ReservedProducts
from laboratory.models import ShelfObject



class ReservedProductSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='get_status_display')
    initial_date = serializers.DateTimeField(format='%b. %d, %Y, %H:%M %p')
    final_date = serializers.DateTimeField(format='%b. %d, %Y, %H:%M %p')
    shelf_object = serializers.SerializerMethodField()
    action = serializers.SerializerMethodField()
    amount_required = serializers.SerializerMethodField()

    def get_amount_required(self,obj=None):
        return f'{obj.amount_required} {obj.shelf_object.measurement_unit.description}'

    def get_shelf_object(self, obj=None):
        return obj.shelf_object.object.name

    def get_action(self, obj=None):

        if obj.status == 3:

            html = """<button data-bs-toggle="modal"
                                      data-bs-target="#delete_selected_obj_reservation_modal"
                                      aria-label="trans" class="btn btn-md btn-danger"
                                      type="button" onclick="init_remove_reservation({id})"
                                      style="width:80%; margin-left:10%;">
                                      <i class="icons fa fa-trash"></i>
                              </button>
                              <input type="hidden" name="user_id" value="{user_id}">
                              <input type="hidden" name="rp_id" id="rp_id{id}" value="{id}">
                              <input type="hidden" name="so_id" id="so_id{shelf_obj_id}" value="{shelf_obj_id}">
                              <input type="hidden" name="status_num" value="{status}">""".format(id=obj.pk,
                                                                                                 user_id=obj.user.id,
                                                                                                 shelf_obj_id=obj.shelf_object.id,
                                                                                                 status=obj.status,
                                                                                                 trans="{% trans 'Remove' %}"
                                                                                                 )
            return html
        else:
            html = """<input type="hidden" name="status_num" value="{status}">""".format(status=obj.status)
            return html


    class Meta:
        model = ReservedProducts
        fields = '__all__'

class ReservedProductsDataTableSerializer(serializers.Serializer):
    data = serializers.ListField(child=ReservedProductSerializer(), required=True)
    draw = serializers.IntegerField(required=True)
    recordsFiltered = serializers.IntegerField(required=True)
    recordsTotal = serializers.IntegerField(required=True)


class ReservedProductsFilterSet(FilterSet):
    initial_date = DateFromToRangeFilter(widget=DateRangeTextWidget(attrs={'placeholder': 'YYYY/MM/DD HH:MM:SS'}))
    final_date = DateFromToRangeFilter(widget=DateRangeTextWidget(attrs={'placeholder': 'YYYY/MM/DD HH:MM:SS'}))
    class Meta:
        model = ReservedProducts
        fields = {'shelf_object__object__name': ['icontains'], 'status': ['exact']}

    @property
    def qs(self):
        queryset = super().qs
        q = self.request.GET.get('amount_required__icontains')

        if q:
            queryset = queryset.filter(Q(amount_required__icontains=q) |
                                       Q(shelf_object__measurement_unit__description__icontains=q)).distinct()

        return queryset

