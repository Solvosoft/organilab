from django.template.loader import render_to_string
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from risk_management.api.serializers import (RiskZoneFilterSet, ZoneTypeSerializer,
                                             RiskZoneShowUpdateSerializer, RiskZoneDataTableSerializer)
from risk_management.models import RiskZone
from django.utils.translation import gettext as _
from rest_framework.decorators import action
from risk_management.forms import ZoneTypeForm, RiskZoneCreateForm
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated


class RiskZoneUpdateviewset(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = RiskZoneShowUpdateSerializer

    def get_queryset(self, pk=None):
        if pk:
            return RiskZone.objects.filter(pk=pk).first()
        else:
            return RiskZone.objects.all()

    def update(self, request, *args, **kwargs):
        pk = kwargs['pk']
        risk_zone = self.get_queryset(pk)
        print(risk_zone, "pk:", pk)
        if risk_zone:
            risk_zone_serializer = self.serializer_class(risk_zone, data=request.data)
            if risk_zone_serializer.is_valid():
                risk_zone_serializer.save()
                return Response(risk_zone_serializer.data)
            return Response(risk_zone_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs['pk']
        risk_zone = self.get_queryset(pk)
        context = {
            'RiskZoneCreateForm': RiskZoneCreateForm(instance=risk_zone, user=request.user),
        }
        data = {'message': render_to_string("risk_management/edit_risk_zone_modal_body.html", context, request),
                'script': 'gt_find_initialize($("#modal-body"))'}
        return Response(data)


class RiskZoneViewSet(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated,)
    # authentication_classes = (TokenAuthentication,)
    serializer_class = RiskZoneDataTableSerializer
    pagination_class = LimitOffsetPagination
    queryset = RiskZone.objects.all()
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['name']  # for the global search
    filterset_class = RiskZoneFilterSet
    ordering_fields = ['name']
    # ordering = ('-zone_type',)  # default order
    ordering = ['pk']

    def get_queryset(self, pk=None):
        if pk:
            return RiskZone.objects.filter(pk=pk).first()
        else:
            return RiskZone.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {'data': data, 'recordsTotal': RiskZone.objects.count(), 'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}
        return Response(self.get_serializer(response).data)


class ZoneTypeViewSet(viewsets.ModelViewSet):
    serializer_class = ZoneTypeSerializer

    @action(methods=['get', 'post'], detail=False)
    def formzonetype(self, request, *args, **kwargs):
        if request.method == 'POST':
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            data = {
                'ok': True,
                'id': serializer.data['priority_validator'],
                'text': serializer.data['name']
            }
            return Response(data)

        context = {
            'ZoneTypeForm': ZoneTypeForm,
        }
        data = {
            'title': """<h4 class="modal-title">{trans}</h4>""".format(trans=_('Add new zone type')),
            'message': render_to_string("risk_management/add_zone_type_modal_form.html", context, request)
        }

        return Response(data)
