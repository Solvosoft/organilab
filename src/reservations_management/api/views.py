from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404

from reservations_management.models import ReservedProducts
from reservations_management.api.serializers import ReservedProductSerializer

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
        serializer = ReservedProductSerializer(
            reserved_product, data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApiListReservationReservedProduct(APIView):
    
    def get(self, request, pk, format=None):
        reserved_products = ReservedProducts.objects.filter(reservation_id=pk)
        serializer = ReservedProductSerializer(reserved_products,many= True)
        return Response(serializer.data)
 
