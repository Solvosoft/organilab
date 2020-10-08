from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404

from reservations_management.models import ReservedProducts
from laboratory.api.serializers import ReservationSerializer


class ApiReservationCRUD(APIView):
    def get_object(self, pk):
        try:
            return ReservedProducts.objects.get(pk=pk)
        except ReservedProducts.DoesNotExist:
            raise Http404

    def post(self, request):
        serializer = ReservationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
