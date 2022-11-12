from django.template.loader import render_to_string
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.http import Http404

from laboratory.models import CommentInform, Inform
from reservations_management.models import ReservedProducts, Reservations
from laboratory.api.serializers import ReservedProductsSerializer, ReservationSerializer, ReservedProductsSerializerUpdate, CommentsSerializer


class ApiReservedProductsCRUD(APIView):
    def get_object(self, pk):
        try:
            return ReservedProducts.objects.get(pk=pk)
        except ReservedProducts.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        serializer = ReservedProductsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk):
        solicitud = self.get_object(pk)
        serializer = ReservedProductsSerializer(solicitud)
        return Response(serializer.data)

    def put(self, request, pk):
        solicitud = self.get_object(pk)
        serializer = ReservedProductsSerializerUpdate(solicitud, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        solicitud = self.get_object(pk)
        solicitud.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ApiReservationCRUD(APIView):
    def post(self, request):
        serializer = ReservationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CommentAPI(viewsets.ModelViewSet):
    queryset= CommentInform.objects.all()
    serializer_class = CommentsSerializer
    permission_classes = [IsAuthenticated]
    def get_comment(self, pk):
        try:
            return self.get_queryset().get(pk=pk)
        except CommentInform.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        serializer = CommentsSerializer(data=request.data)
        if serializer.is_valid():
            inform=Inform.objects.filter(pk=request.data['inform']).first()
            CommentInform.objects.create(
                creator=request.user,
                comment = serializer.data['comment'],
                inform = inform
            )
            template = render_to_string('laboratory/comment.html', {'comments': self.get_queryset().filter(inform=inform).order_by('pk'), 'user':request.user},request)
            return Response({'data':template}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        pk = None
        if 'pk' in kwargs:
            comments= self.get_queryset().filter(pk=pk)
            return Response(self.get_serializer(comments).data)
        else:

            template = render_to_string('laboratory/comment.html', {'comments': self.get_queryset().filter(inform__pk=int(request.GET.get('inform'))).order_by('pk'), 'user':request.user},request)
            return Response({'data':template})
    def update(self, request, pk=None):
        comment=None
        if pk:
            serializer = CommentsSerializer(data=request.data)
            if serializer.is_valid():
                comment = CommentInform.objects.filter(pk=pk).first()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            if comment:
                comment.comment=request.data['comment']
                comment.save()
                template = render_to_string('laboratory/comment.html',
                                            {'comments': self.get_queryset().filter(inform=comment.inform).order_by('pk'),
                                             'user': request.user},request)

                return Response({'data':template}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        if pk:
            comment = self.get_comment(pk)
            inform=comment.inform
            comment.delete()
            template= render_to_string('laboratory/comment.html', {'comments': self.get_queryset().filter(inform=inform).order_by('pk'), 'user':request.user},request)

            return Response({'data':template},status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
