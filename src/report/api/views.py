from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from laboratory.models import TaskReport
from report.api.serializers import ReportDataTableSerializer
from django.db import connection

class ReportDataViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = TaskReport.objects.all()
    serializer_class = ReportDataTableSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    ordering_fields = ['pk']
    ordering = ('pk', )
    limit = 10
    offset = 0
    report = None

    def get_queryset(self):

        self.datadict={column['name']:'ll.row_data->>'+str(i) for i,column in enumerate(self.report.table_content['columns'])}
        self.translation_columns={self.datadict[data]:self.request.GET[data].lower() for data in self.datadict if data in self.request.GET}
        sql_query="""Select ll.row_data::json from laboratory_taskreport as lab join (SELECT id, jsonb_array_elements(jsonb_extract_path("table_content",  'dataset' )) as row_data from laboratory_taskreport where id=%s) as ll on ll.id=lab.id %s order by %s %s;"""%(self.pk, self.get_where_clause(), self.get_ordering(), self.get_limit_and_offset())

        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            return list(map(lambda x: x[0], cursor))

    def get_queryset_total(self):
        sql_query = """Select COUNT(ll.row_data->>0) from laboratory_taskreport as lab join (SELECT id, jsonb_array_elements(jsonb_extract_path("table_content",  'dataset' )) as row_data from laboratory_taskreport where id=%s) as ll on ll.id=lab.id""" %(self.pk,)
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            return cursor.fetchone()[0]

    def get_queryset_record_filtered_total(self):
        sql_query = """Select COUNT(ll.row_data->>0) from laboratory_taskreport as lab join (SELECT id, jsonb_array_elements(jsonb_extract_path("table_content",  'dataset' )) as row_data from laboratory_taskreport where id= %s ) as ll on ll.id=lab.id %s""" % (self.pk, self.get_where_clause())
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            return cursor.fetchone()[0]

    def get_where_clause(self):
        where_clause=""
        for i,item in enumerate(self.translation_columns):

            if i:
                where_clause+=" AND "
            where_clause+="LOWER(%s) LIKE '%%%s%%'" % (item,self.clean_where_item(self.translation_columns[item]))
        if where_clause:
            where_clause="where "+where_clause

        return where_clause

    def clean_where_item(self, value):
        return value

    def get_ordering(self):
        if 'ordering' in self.request.GET:
            self.ordering=self.request.GET.getlist('ordering')
        order_by_str=""
        ordering_str=""
        order_asc_desc=""

        for i,ordering in enumerate(self.ordering):

            if ordering.startswith("-"):
                ordering_str=self.datadict[ordering[1::]]
                order_asc_desc="desc"
            else:
                ordering_str=self.datadict[ordering]
                order_asc_desc="asc"

            if i:
                order_by_str+=' , '
            order_by_str+= ordering_str+" "+order_asc_desc

        return order_by_str

    def get_limit_and_offset(self):
        limit_offset_str =""

        if 'limit' in self.request.GET:
            self.limit=self.request.GET.get('limit',self.limit)

        if 'offset' in self.request.GET:
            self.offset = self.request.GET.get('offset', self.offset)

        limit_offset_str = "limit %s offset %s" %(self.limit,self.offset)

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

        response = {'data': data, 'recordsTotal': self.get_queryset_total(),
                    'recordsFiltered': self.get_queryset_record_filtered_total(),
                    'draw': self.request.GET.get('draw', 1)}


        return Response(self.get_serializer(response).data)