from django.http import Http404
from django.utils.timezone import now
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from reservations_management.api.serializers import ReservedProductSerializer, ReservedProductsDataTableSerializer, \
    ReservedProductsFilterSet
from reservations_management.functions import add_decrease_stock_task
from reservations_management.models import ReservedProducts


# from rest_framework.permissions import IsAuthenticated
# from rest_framework.authentication import TokenAuthentication


class ApiReservedProductsCRUD(APIView):
    # authentication_classes = [
    #     TokenAuthentication
    # ]
    # permission_classes = [
    #     IsAuthenticated
    # ]

    def get_object(self, pk):
        try:
            return ReservedProducts.objects.get(pk=pk)
        except ReservedProducts.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        reserved_product = self.get_object(pk)
        serializer = ReservedProductSerializer(reserved_product)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        reserved_product = self.get_object(pk)
        last_status = reserved_product.status
        serializer = ReservedProductSerializer(
            reserved_product, data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            if (serializer.initial_data['status'] == '1' and last_status == 0):
                add_decrease_stock_task(reserved_product)

            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApiListReservationReservedProduct(APIView):

    def get(self, request, pk, format=None):
        reserved_products = ReservedProducts.objects.filter(reservation_id=pk)
        serializer = ReservedProductSerializer(reserved_products, many=True)
        return Response(serializer.data)



class ReservedProductViewSet(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated,)
    # authentication_classes = (TokenAuthentication,)
    serializer_class = ReservedProductsDataTableSerializer
    queryset = ReservedProducts.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['shelf_object__object__name', 'shelf_object__object__code', ]  # for the global search
    filterset_class = ReservedProductsFilterSet
    ordering_fields = ['shelf_object__object__name', 'shelf_object__object__code', ]
    ordering = ('-shelf_object__object__name',)  # default order

    def filter_queryset(self, queryset, pk):

        queryset = super().filter_queryset(queryset)

        if pk:
            queryset = queryset.filter(reservation__laboratory__pk=int(pk))
            queryset = queryset.filter(user_id=self.request.user)
        if self.request.GET['subfiltrar'] == 'false':
            queryset = queryset.filter(final_date__gte=now())
        return queryset
    def retrieve(self, request, *args, **kwargs):
        pk=kwargs['pk']
        queryset = self.filter_queryset(self.get_queryset(), pk)
        data = self.paginate_queryset(queryset)
        response = {'data': data, 'recordsTotal': ReservedProducts.objects.count(), 'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}
        return Response(self.get_serializer(response).data)



