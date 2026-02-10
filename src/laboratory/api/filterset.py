from django.contrib.admin.models import LogEntry
from django.db.models import Q
from django_filters import FilterSet, DateFromToRangeFilter, CharFilter
from django.db.models.functions import Concat
from djgentelella.fields.drfdatetime import DateRangeTextWidget

from laboratory.models import (
    EquipmentType,
    Catalog,
    Protocol,
    Inform,
    Provider,
    ObjectFeatures,
    Object,
    ShelfObject,
)
from sga.models import Substance
from django.db.models.expressions import Value


class SubstanceFilterSet(FilterSet):
    def filter_queryset(self, queryset):
        search = self.request.GET.get("search", "")
        if search:
            queryset = queryset.annotate(
                fullname=Concat(
                    "created_by__first_name", Value(" "), "created_by__last_name"
                )
            )
            queryset = queryset.filter(
                Q(created_by__username__icontains=search)
                | Q(fullname__icontains=search)
                | Q(comercial_name__icontains=search)
                | Q(uipa_name__icontains=search)
            ).distinct()
        return queryset

    class Meta:
        model = Substance
        fields = ["created_by", "comercial_name", "uipa_name"]


class InstrumentalFamilyFilter(FilterSet):
    class Meta:
        model = Catalog
        fields = {"id": ["exact"], "description": ["icontains"]}


class ProviderFilter(FilterSet):
    class Meta:
        model = Provider
        fields = {
            "id": ["exact"],
            "name": ["icontains"],
            "phone_number": ["icontains"],
            "email": ["icontains"],
            "legal_identity": ["icontains"],
            "laboratory__name": ["icontains"],
        }


class ObjectFeatureFilter(FilterSet):
    class Meta:
        model = ObjectFeatures
        fields = {
            "id": ["exact"],
            "name": ["icontains"],
            "description": ["icontains"],
        }


class ObjectFilter(FilterSet):
    class Meta:
        model = Object
        fields = {
            "id": ["exact"],
            "name": ["icontains"],
            "code": ["icontains"],
            "model": ["icontains"],
            "serie": ["icontains"],
            "plaque": ["icontains"],
            "is_container": ["exact"],
        }


class EquipmentTypeFilter(FilterSet):
    class Meta:
        model = EquipmentType
        fields = {"id": ["exact"], "description": ["icontains"], "name": ["icontains"]}


class EquipmentFilter(FilterSet):
    class Meta:
        model = Object
        fields = {
            "id": ["exact"],
            "name": ["icontains"],
            "code": ["icontains"],
            "equipmentcharacteristics__equipment_type": ["exact"],
        }


class ProtocolFilterSet(FilterSet):
    class Meta:
        model = Protocol
        fields = {}


class LogEntryFilterSet(FilterSet):
    action_time = DateFromToRangeFilter(
        widget=DateRangeTextWidget(attrs={"placeholder": "YYYY/MM/DD"})
    )
    user = CharFilter(field_name="user", method="filter_user")

    def filter_user(self, queryset, name, value):
        return queryset.filter(
            Q(user__first_name__icontains=value)
            | Q(user__last_name__icontains=value)
            | Q(user__username__icontains=value)
        )

    class Meta:
        model = LogEntry
        fields = ["object_repr", "change_message", "action_flag", "user"]


class InformFilterSet(FilterSet):
    class Meta:
        model = Inform
        fields = {"name": ["icontains"], "status": ["exact"]}


class ReactiveFilter(FilterSet):
    class Meta:
        model = Object
        fields = {
            "id": ["exact"],
            "name": ["icontains"],
            "code": ["icontains"],
            "synonym": ["icontains"],
        }


class ShelObjectReactiveFilter(FilterSet):
    object_name = CharFilter(
        field_name="object__name", lookup_expr="icontains", distinct=True
    )
    labroom_name = CharFilter(
        field_name="shelf__furniture__labroom__name",
        lookup_expr="icontains",
        distinct=True,
    )
    shelf_name = CharFilter(
        field_name="shelf__name", lookup_expr="icontains", distinct=True
    )
    furniture_name = CharFilter(
        field_name="shelf__furniture__name", lookup_expr="icontains", distinct=True
    )
    container_name = CharFilter(
        field_name="container__object__name", lookup_expr="icontains", distinct=True
    )
    measurement_description = CharFilter(
        field_name="measurement_unit__description", lookup_expr="exact", distinct=True
    )
    measurement_key = CharFilter(
        field_name="measurement_unit__key", lookup_expr="exact", distinct=True
    )

    class Meta:
        model = ShelfObject
        fields = {
            "id": ["exact"],
            "quantity": ["exact", "gte", "lte"],
        }
