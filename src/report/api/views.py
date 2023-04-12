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


class ReportDataViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = TaskReport.objects.all()
    serializer_class = ReportDataTableSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    ordering_fields = ['pk']
    ordering = ('pk', )
    report = None

    def get_queryset(self):
        return TaskReport.objects.filter(pk=self.pk).annotate(content=F('table_content'), filter=Q(table_content__dataset__0__7__icontains='Litros')).values_list('content', flat=True)[0]

    def get_serializer(self, data):
        return self.serializer_class(data)

    def paginate_queryset(self, queryset):
        self.paginator = self.pagination_class()
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def retrieve(self, request, pk, **kwargs):
        self.request = request
        self.pk = pk
        self.report = get_object_or_404(TaskReport, pk=pk)
        queryset = self.get_queryset()
        total = len(queryset)
        data = self.paginate_queryset(queryset)
        response = {'data': data, 'recordsTotal': total,
                    'recordsFiltered': total,
                    'draw': self.request.GET.get('draw', 1)}
        return Response(self.get_serializer(response).data)