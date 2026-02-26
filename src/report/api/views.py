from datetime import datetime

from django.conf import settings
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djgentelella.objectmanagement import AuthAllPermBaseObjectManagement
from rest_framework import viewsets, mixins
from rest_framework.authentication import SessionAuthentication
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from laboratory.utils import (
    PermissionByOrganization,
)
from report.api.filterset import ObjectChangeLogFilterSet, PrecursorReportValuesFilter
from report.models import (
    TaskReport,
    ObjectChangeLogReportBuilder,
    ObjectChangeLogReport,
    RegencyReportBuilder,
    RegencyReport,
)
from report.api.serializers import (
    ReportDataTableSerializer,
    ObjectChangeDataTableSerializer,
    ValidateObjectChangeFilters,
    RegencyDataTableSerializer,
    PrecursorReportValuesDataTableSerializer,
    PrecursorReportValuesSerializer,
    PrecursorReportValuesValidateSerializer,
)
from django.db import connection

from report.utils import filter_period, format_date
from laboratory.models import PrecursorReportValues
from django.contrib.admin.models import LogEntry, DELETION, CHANGE, ADDITION
from laboratory.utils import organilab_logentry


class ReportDataViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = TaskReport.objects.all()
    serializer_class = ReportDataTableSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    ordering_fields = ["pk"]
    ordering = ("pk",)
    limit = 10
    offset = 0
    report = None

    def get_queryset(self):
        self.datadict = {
            column["name"]: "ll.row_data->>" + str(i)
            for i, column in enumerate(self.report.table_content["columns"])
        }
        self.translation_columns = {
            self.datadict[data]: self.request.GET[data].lower()
            for data in self.datadict
            if data in self.request.GET
        }
        sql_query = (
            """Select ll.row_data::json from report_taskreport as lab join (SELECT id, jsonb_array_elements(jsonb_extract_path("table_content",  'dataset' )) as row_data from report_taskreport where id=%s) as ll on ll.id=lab.id %s order by %s %s;"""  # noqa: E501
            % (
                self.pk,
                self.get_where_clause(),
                self.get_ordering(),
                self.get_limit_and_offset(),
            )
        )
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            return list(map(lambda x: x[0], cursor))

    def get_queryset_total(self):
        sql_query = (
            """Select COUNT(ll.row_data->>0) from report_taskreport as lab join (SELECT id, jsonb_array_elements(jsonb_extract_path("table_content",  'dataset' )) as row_data from report_taskreport where id=%s) as ll on ll.id=lab.id"""  # noqa: E501
            % (self.pk,)
        )
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            return cursor.fetchone()[0]

    def get_queryset_record_filtered_total(self):
        sql_query = (
            """Select COUNT(ll.row_data->>0) from report_taskreport as lab join (SELECT id, jsonb_array_elements(jsonb_extract_path("table_content",  'dataset' )) as row_data from report_taskreport where id= %s ) as ll on ll.id=lab.id %s"""  # noqa: E501
            % (self.pk, self.get_where_clause())
        )
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            return cursor.fetchone()[0]

    def get_where_clause(self):
        where_clause = ""
        for i, item in enumerate(self.translation_columns):

            if i:
                where_clause += " AND "
            where_clause += "LOWER(%s) LIKE '%%%s%%'" % (
                item,
                self.clean_where_item(self.translation_columns[item]),
            )
        if where_clause:
            where_clause = "where " + where_clause

        return where_clause

    def clean_where_item(self, value):
        return value

    def get_ordering(self):
        if "ordering" in self.request.GET:
            self.ordering = self.request.GET.getlist("ordering")
        order_by_str = ""
        ordering_str = ""
        order_asc_desc = ""

        for i, ordering in enumerate(self.ordering):

            if ordering.startswith("-"):
                ordering_str = self.datadict[ordering[1::]]
                order_asc_desc = "desc"
            else:
                ordering_str = self.datadict[ordering]
                order_asc_desc = "asc"

            if i:
                order_by_str += " , "
            order_by_str += ordering_str + " " + order_asc_desc

        return order_by_str

    def get_limit_and_offset(self):
        limit_offset_str = ""

        if "limit" in self.request.GET:
            self.limit = self.request.GET.get("limit", self.limit)

        if "offset" in self.request.GET:
            self.offset = self.request.GET.get("offset", self.offset)

        limit_offset_str = "limit %s offset %s" % (self.limit, self.offset)

        return limit_offset_str

    def get_serializer(self, data):
        return self.serializer_class(data)

    def paginate_queryset(self, queryset):
        self.paginator = self.pagination_class()
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def retrieve(self, request, pk, **kwargs):
        self.request = request
        self.pk = pk
        self.report = get_object_or_404(TaskReport, pk=pk)
        data = self.get_queryset()

        response = {
            "data": data,
            "recordsTotal": self.get_queryset_total(),
            "recordsFiltered": self.get_queryset_record_filtered_total(),
            "draw": self.request.GET.get("draw", 1),
        }

        return Response(self.get_serializer(response).data)


class ReportDataLogViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = ObjectChangeLogReportBuilder.objects.all().using(
        settings.READONLY_DATABASE
    )
    serializer_class = ObjectChangeDataTableSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = [
        "update_time",
        "old_value",
        "new_value",
        "diff_value",
        "user__first_name",
        "user__last_name",
        "user__username",
    ]
    filterset_class = ObjectChangeLogFilterSet
    ordering_fields = [
        "pk",
        "user",
        "update_time",
        "old_value",
        "new_value",
        "diff_value",
    ]
    ordering = ("pk", "user", "update_time", "old_value", "new_value", "diff_value")
    laboratory = None
    object = None
    unit = None
    report = None

    def get_queryset(self):
        queryset = self.queryset
        if self.report:
            return queryset.filter(report=self.report)
        else:
            return queryset.none()

    def format_date_range(self, value):
        dev = None
        try:
            dev = datetime.strptime(value, "%m/%d/%Y")
        except ValueError as e:
            pass
        return dev

    def filter_period(self, dates, queryset):

        dates = dates.split("-")
        if len(dates) != 2:
            return queryset

        dates[0] = self.format_date_range(dates[0].strip())
        dates[1] = self.format_date_range(dates[1].strip())
        return queryset.filter(update_time__gte=dates[0], update_time__lte=dates[1])

    def create_extra_filters(self, queryset):
        filters_list = ["user", "new_value", "old_value", "diff_value"]

        filters = {"new_value": "", "diff_value": "", "old_value": "", "user": ""}

        queryset = queryset.annotate(
            fullname=Concat("user__first_name", Value(" "), "user__last_name")
        )
        for data in self.request.GET:
            if data in filters_list:
                filters[data] = self.request.GET.get(data, "")
        queryset = queryset.filter(
            Q(fullname__icontains=filters["user"]),
            Q(user__username__icontains=filters["user"]),
            Q(new_value__icontains=filters["new_value"]),
            Q(old_value__icontains=filters["old_value"]),
            Q(diff_value__icontains=filters["diff_value"]),
        ).distinct()

        if "update_time" in self.request.GET:
            queryset = self.filter_period(self.request.GET.get("update_time"), queryset)

        return queryset

    def retrieve(self, request, pk, **kwargs):
        task_report = get_object_or_404(TaskReport, pk=pk)

        validate_serializer = ValidateObjectChangeFilters(data=self.request.GET)
        if validate_serializer.is_valid():
            self.laboratory = validate_serializer.validated_data["laboratory"]
            self.object = validate_serializer.validated_data["object"]
            self.unit = validate_serializer.validated_data["unit"]
            self.report = ObjectChangeLogReport.objects.filter(
                task_report=task_report,
                laboratory=self.laboratory,
                object=self.object,
                unit=self.unit,
            ).first()

        queryset = self.filter_queryset(self.get_queryset())

        if "ordering" in self.request.GET:
            queryset = queryset.order_by(self.request.GET["ordering"])

        queryset = self.create_extra_filters(queryset)
        data = self.paginate_queryset(queryset)

        total = ObjectChangeLogReportBuilder.objects.count()
        response = {
            "data": data,
            "recordsTotal": total,
            "recordsFiltered": queryset.count(),
            "draw": self.request.GET.get("draw", 1),
        }
        return Response(self.get_serializer(response).data)


class RegencyViewSetX(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = RegencyReportBuilder.objects.all().using(settings.READONLY_DATABASE)
    serializer_class = RegencyDataTableSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = [
        "substance",
        "danger_category",
        "total",
    ]
    filterset_class = None
    ordering_fields = [
        "substance",
        "danger_category",
        "total",
    ]
    ordering = ("substance", "danger_category", "total")
    report = None
    step = None

    def get_queryset(self):
        queryset = self.queryset
        if self.report and self.step:
            return queryset.filter(report=self.report, danger_list=self.step)
        else:
            return queryset.none()

    def retrieve(self, request, pk, **kwargs):
        task_report = get_object_or_404(TaskReport, pk=pk)

        self.step = request.GET.get("step", None)
        self.report = RegencyReport.objects.filter(
            task_report=task_report,
        ).first()

        queryset = self.filter_queryset(self.get_queryset())

        if "ordering" in self.request.GET:
            queryset = queryset.order_by(self.request.GET["ordering"])

        data = self.paginate_queryset(queryset)

        total = RegencyReportBuilder.objects.filter(report=self.report).count()
        response = {
            "data": data,
            "recordsTotal": total,
            "recordsFiltered": queryset.count(),
            "draw": self.request.GET.get("draw", 1),
        }
        return Response(self.get_serializer(response).data)


class RegencyViewSet(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": RegencyDataTableSerializer,
    }
    perms = {
        "list": ["laboratory.do_report"],
    }

    permission_classes = (PermissionByOrganization,)

    queryset = RegencyReportBuilder.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["substance", "danger_category"]
    ordering_fields = ["pk"]
    filterset_class = None

    def get_queryset(self):
        queryset = self.queryset
        if self.report and self.step:
            return queryset.filter(report=self.report, danger_list=int(self.step))
        else:
            return queryset.none()

    def list(self, request, *args, **kwargs):
        task = get_object_or_404(TaskReport, pk=self.request.GET.get("pk"))
        self.report = RegencyReport.objects.filter(task_report=task).first()
        self.step = request.GET.get("step", None)
        return super().list(request, *args, **kwargs)


class PrecursorReportValuesViewSet(AuthAllPermBaseObjectManagement):
    serializer_class = {
        "list": PrecursorReportValuesDataTableSerializer,
        "destroy": PrecursorReportValuesSerializer,
        "create": PrecursorReportValuesValidateSerializer,
        "update": PrecursorReportValuesValidateSerializer,
    }

    perms = {
        "list": ["laboratory.view_precursorreportvalues"],
        "create": ["laboratory.add_precursorreportvalues"],
        "update": ["laboratory.change_precursorreportvalues"],
        "destroy": ["laboratory.delete_precursorreportvalues"],
    }

    queryset = PrecursorReportValues.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ["id", "object__name"]
    filterset_class = PrecursorReportValuesFilter
    ordering_fields = ["pk"]
    ordering = "object__name"

    def get_queryset(self):
        precusor_pk = self.get_precursor_pk_or_error()

        qs = PrecursorReportValues.objects.all()

        if precusor_pk:
            qs = qs.filter(precursor_report_id=precusor_pk)

        return qs

    def get_precursor_pk_or_error(self):
        precusor_pk = self.kwargs.get("precusor_pk")
        if not precusor_pk:
            raise ValidationError(
                {"precusor_pk": _("This endpoint requires precusor_pk in the URL.")}
            )
        return precusor_pk

    def get_org_pk_or_error(self):
        org_pk = self.kwargs.get("org_pk")
        if not org_pk:
            raise ValidationError(
                {"org_pk": _("This endpoint requires org_pk in the URL.")}
            )
        return org_pk

    def perform_create(self, serializer):
        precusor_pk = self.get_precursor_pk_or_error()
        precusor_value = serializer.save(precursor_report_id=precusor_pk)

        organilab_logentry(
            self.request.user,
            precusor_value,
            ADDITION,
            "precursorreportvalues",
            changed_data=[],
            relobj=precusor_pk,
        )

    def perform_update(self, serializer):
        precusor_pk = self.get_precursor_pk_or_error()

        precusor_value_before = self.get_object()
        before = {
            "object_id": precusor_value_before.object_id,
            "measurement_unit_id": precusor_value_before.measurement_unit_id,
            "quantity": precusor_value_before.quantity,
            "previous_balance": precusor_value_before.previous_balance,
            "new_income": precusor_value_before.new_income,
            "bills": precusor_value_before.bills,
            "providers": precusor_value_before.providers,
            "stock": precusor_value_before.stock,
            "month_expense": precusor_value_before.month_expense,
            "final_balance": precusor_value_before.final_balance,
            "reason_to_spend": precusor_value_before.reason_to_spend,
        }

        precusor_value = serializer.save(precursor_report_id=precusor_pk)

        after = {
            "object_id": precusor_value.object_id,
            "measurement_unit_id": precusor_value.measurement_unit_id,
            "quantity": precusor_value.quantity,
            "previous_balance": precusor_value.previous_balance,
            "new_income": precusor_value.new_income,
            "bills": precusor_value.bills,
            "providers": precusor_value.providers,
            "stock": precusor_value.stock,
            "month_expense": precusor_value.month_expense,
            "final_balance": precusor_value.final_balance,
            "reason_to_spend": precusor_value.reason_to_spend,
        }

        changed_fields = [k for k in after.keys() if before.get(k) != after.get(k)]

        organilab_logentry(
            self.request.user,
            precusor_value,
            CHANGE,
            "precursorreportvalues",
            changed_data=changed_fields,
            relobj=precusor_pk,
        )

    def perform_destroy(self, instance):
        precusor_pk = self.get_precursor_pk_or_error()
        precusor_value_id = instance.pk
        precusor_value_repr = str(instance)

        organilab_logentry(
            self.request.user,
            instance,
            DELETION,
            "precursorreportvalues",
            changed_data=[],
            object_repr=precusor_value_repr,
            relobj=precusor_pk,
        )

        instance.delete()
