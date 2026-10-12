from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
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
from laboratory.models import OrganizationStructure, PrecursorReport, PrecursorReportValues
from django.contrib.admin.models import LogEntry, DELETION, CHANGE, ADDITION
from laboratory.utils import organilab_logentry
from django.utils.translation import gettext as _


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

    # Los valores que manda el navegador (filtros, límite, desplazamiento) van
    # siempre como parámetros de la consulta, nunca interpolados en el SQL: el
    # filtro por columna se pegaba con `%` y bastaba una comilla para inyectar.
    # Solo se interpolan nombres de columna, y esos salen de `datadict`.
    DATASET_SQL = (
        """from report_taskreport as lab join (SELECT id, jsonb_array_elements(jsonb_extract_path("table_content",  'dataset' )) as row_data from report_taskreport where id=%s) as ll on ll.id=lab.id"""  # noqa: E501
    )

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
        where_clause, where_params = self.get_where_clause()
        ordering = self.get_ordering()
        sql_query = "Select ll.row_data::json %s %s %s limit %%s offset %%s;" % (
            self.DATASET_SQL,
            where_clause,
            "order by " + ordering if ordering else "",
        )
        params = [self.report.pk] + where_params + list(self.get_limit_and_offset())
        with connection.cursor() as cursor:
            cursor.execute(sql_query, params)
            return list(map(lambda x: x[0], cursor))

    def get_queryset_total(self):
        sql_query = "Select COUNT(ll.row_data->>0) %s" % self.DATASET_SQL
        with connection.cursor() as cursor:
            cursor.execute(sql_query, [self.report.pk])
            return cursor.fetchone()[0]

    def get_queryset_record_filtered_total(self):
        where_clause, where_params = self.get_where_clause()
        sql_query = "Select COUNT(ll.row_data->>0) %s %s" % (self.DATASET_SQL, where_clause)
        with connection.cursor() as cursor:
            cursor.execute(sql_query, [self.report.pk] + where_params)
            return cursor.fetchone()[0]

    def get_where_clause(self):
        """Devuelve el `where` con marcadores y la lista de parámetros."""
        clauses = []
        params = []
        for item, value in self.translation_columns.items():
            clauses.append("LOWER(%s) LIKE %%s" % item)
            params.append("%%%s%%" % self.clean_where_item(value))
        where_clause = "where " + " AND ".join(clauses) if clauses else ""
        return where_clause, params

    def clean_where_item(self, value):
        return value

    def get_ordering(self):
        if "ordering" in self.request.GET:
            self.ordering = self.request.GET.getlist("ordering")
        order_by = []

        for ordering in self.ordering:
            column, order_asc_desc = ordering, "asc"
            if ordering.startswith("-"):
                column, order_asc_desc = ordering[1:], "desc"
            # Una columna que el reporte no tiene se ignora en vez de dar un 500.
            if column in self.datadict:
                order_by.append(self.datadict[column] + " " + order_asc_desc)

        return " , ".join(order_by)

    def get_limit_and_offset(self):
        """Límite y desplazamiento como enteros no negativos."""

        def as_int(name, default):
            try:
                return max(int(self.request.GET.get(name, default)), 0)
            except (TypeError, ValueError):
                return default

        self.limit = as_int("limit", self.limit)
        self.offset = as_int("offset", self.offset)
        return self.limit, self.offset

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
        # Una fecha que no se pudo leer queda en None, y filtrar con None da
        # ValueError (500): un rango ilegible no filtra.
        if None in dates:
            return queryset
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
            Q(new_value__icontains=filters["new_value"]),
            Q(old_value__icontains=filters["old_value"]),
            Q(diff_value__icontains=filters["diff_value"]),
        ).distinct()
        # El usuario se busca por nombre completo O por nombre de usuario, y solo
        # si se pidió: exigir ambas a la vez vaciaba la tabla al buscar por
        # nombre, y el `icontains` vacío sobre el join descartaba siempre las
        # filas sin usuario.
        # El filterset ya exige que `user` sea un pk, así que también se acepta
        # el pk aquí: con solo el texto, filtrar por usuario no daba nunca filas.
        if filters["user"]:
            user_q = Q(fullname__icontains=filters["user"]) | Q(
                user__username__icontains=filters["user"]
            )
            if filters["user"].isdigit():
                user_q |= Q(user__pk=int(filters["user"]))
            queryset = queryset.filter(user_q)

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
        return PrecursorReportValues.objects.filter(
            precursor_report=self.get_precursor_report()
        )

    def get_precursor_report(self):
        """El reporte de precursores de la URL, si es de la organización de la URL.

        Antes solo se filtraba por `precusor_pk`, así que desde la URL de la
        organización propia se leían y modificaban los valores de un reporte de
        cualquier otra organización.
        """
        if not hasattr(self, "_precursor_report"):
            organization = get_object_or_404(
                OrganizationStructure, pk=self.get_org_pk_or_error()
            )
            self._precursor_report = get_object_or_404(
                PrecursorReport,
                pk=self.get_precursor_pk_or_error(),
                laboratory__in=list(organization.get_my_laboratories),
            )
            self._related_objects = [self._precursor_report.laboratory, organization]
        return self._precursor_report

    def get_related_objects(self):
        """Laboratorio y organización a los que se ata la bitácora.

        Se pasaba el pk del reporte de precursores como `relobj`, y
        `organilab_logentry` lo interpreta como pk de laboratorio: la entrada
        quedaba colgada de otro laboratorio (o de ninguno).
        """
        self.get_precursor_report()
        return self._related_objects

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
        precusor_value = serializer.save(precursor_report=self.get_precursor_report())

        organilab_logentry(
            self.request.user,
            precusor_value,
            ADDITION,
            "precursorreportvalues",
            changed_data=list(serializer.validated_data.keys()),
            change_message=_("Created precursor report value"),
            relobj=self.get_related_objects(),
        )

    def perform_update(self, serializer):
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

        precusor_value = serializer.save(precursor_report=self.get_precursor_report())

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
            change_message=_("Updated precursor report value"),
            relobj=self.get_related_objects(),
        )

    def perform_destroy(self, instance):
        precusor_value_id = instance.pk
        precusor_value_repr = str(instance)

        organilab_logentry(
            self.request.user,
            instance,
            DELETION,
            "precursorreportvalues",
            changed_data=["object", "quantity"],
            change_message=_("Deleted precursor report value"),
            object_repr=precusor_value_repr,
            relobj=self.get_related_objects(),
        )

        instance.delete()
