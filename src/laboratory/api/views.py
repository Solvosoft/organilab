from django.contrib.admin.models import LogEntry
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.db.models import Value, DateField
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets, mixins
from rest_framework.authentication import SessionAuthentication, BaseAuthentication
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from laboratory.api import serializers
from laboratory.api.forms import CommentInformForm, ShelfObjectLabviewForm
from laboratory.api.serializers import ReservedProductsSerializer, ReservationSerializer, \
    ReservedProductsSerializerUpdate, CommentsSerializer, ProtocolFilterSet, LogEntryFilterSet, ShelfObjectSerialize, \
    LogEntryUserDataTableSerializer, ShelfLabViewSerializer
from laboratory.models import CommentInform, Inform, Protocol, OrganizationStructure, \
    Laboratory, InformsPeriod, ShelfObject, Shelf
from laboratory.utils import get_logentries_org_management
from reservations_management.models import ReservedProducts


class ApiReservedProductsCRUD(APIView):
    def get_object(self, pk):
        try:
            return ReservedProducts.objects.get(pk=pk)
        except ReservedProducts.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        serializer = ReservedProductsSerializer(data=request.data)

        if serializer.is_valid():
            laboratory = get_object_or_404(Laboratory, pk=int(request.data['lab']))
            instance = serializer.save()
            instance.laboratory = laboratory
            instance.save()

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

    authentication_classes =[SessionAuthentication,BaseAuthentication]
    permission_classes = [IsAuthenticated]
    queryset= CommentInform.objects.all()
    serializer_class = CommentsSerializer

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
            comments=self.get_queryset().filter(inform=inform).order_by('pk')
            template = render_to_string('laboratory/comment.html', {'comments':comments, 'user':request.user},request)
            return Response({'data':template}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        comments = queryset.none()

        if request.method == "GET":
            form = CommentInformForm(request.GET)

            if form.is_valid():
                comments = queryset.filter(inform__pk=form.cleaned_data['inform']).order_by('pk')

        template = render_to_string('laboratory/comment.html', {'comments': comments, 'user':request.user}, request)
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


class ProtocolViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ProtocolDataTableSerializer
    queryset = Protocol.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['name', 'short_description']
    filterset_class = ProtocolFilterSet
    ordering_fields = ['pk']
    ordering = ('pk', )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        lab_pk = self.request.GET.get('lab_pk', None)
        if lab_pk:
            queryset = queryset.filter(laboratory__pk=lab_pk)
        else:
            queryset = queryset.none()
        return queryset


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {'data': data, 'recordsTotal': Protocol.objects.count(), 'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}
        return Response(self.get_serializer(response).data)


class LogEntryViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.LogEntryDataTableSerializer
    queryset = LogEntry.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['object_repr', 'action_flag']
    filterset_class =LogEntryFilterSet
    ordering_fields = ['pk']
    ordering = ('pk', )

    def get_queryset(self):
        filters = {}
        org = self.request.GET.get('org', None)
        qr_obj = self.request.GET.get('qr_obj', None)
        queryset = self.queryset.none()

        if not qr_obj:
            log_entries = get_logentries_org_management(self, org)
            filters.update({'pk__in': log_entries})
        else:
            if qr_obj.isnumeric():
                self.serializer_class = LogEntryUserDataTableSerializer
                qr_obj = int(qr_obj)
                detail = [
                    "[{'changed': {'fields': ['Login', %d]}}]" %(qr_obj),
                    "[{'added': {'fields': ['Register', %d]}}]" %(qr_obj)
                ]

                filters.update({
                    'action_flag__in': [1, 2],
                    'content_type__app_label': 'auth',
                    'content_type__model': 'user',
                    'change_message__in': detail
                })

        if filters:
            queryset = self.queryset.filter(**filters).distinct()

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {'data': data, 'recordsTotal': LogEntry.objects.count(), 'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}
        return Response(self.get_serializer(response).data)


class InformViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.InformDataTableSerializer
    queryset = Inform.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['name', 'creation_date', ]  # for the global search
    filterset_class = serializers.InformFilterSet
    ordering_fields = ['creation_date']
    ordering = ('-creation_date',)  # default order

    def get_queryset(self):
        period = self.request.GET.get('period', None)
        if not period:
            return self.queryset.none()
        period = get_object_or_404(InformsPeriod, pk=period)
        queryset = super().get_queryset().filter(pk__in=period.informs.values_list('pk', flat=True),
                                                 organization=self.organization)
        queryset=queryset.annotate(
            start_application_date=Value(period.start_application_date, DateField()),
            close_application_date=Value(period.close_application_date, DateField())
        )
        return queryset

    def retrieve(self, request, pk, **kwargs):
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {'data': data, 'recordsTotal': Inform.objects.count(),
                    'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}
        return Response(self.get_serializer(response).data)


class ShelfObjectAPI(APIView):
    def get_object(self, pk):
        try:
            return ShelfObject.objects.filter(shelf__pk=pk)
        except ShelfObject.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, request, org_pk):
        solicitud = self.get_object(request.GET['shelf'])
        serializer = ShelfObjectSerialize(solicitud,context={'org_pk':org_pk}, many=True)
        return Response(serializer.data)

class ShelfObjectGraphicAPI(APIView):
    def get(self, request):
        queryset = ShelfObject.objects.filter(shelf__pk=request.GET['shelf'])
        labels = []
        data = []
        if queryset:
            self.show_chart = True
            for obj in queryset:
               data.append(obj.quantity)
               labels.append(obj.object.name)

        return Response({'labels':labels,'data':data})


@method_decorator(permission_required('laboratory.delete_shelf'), name='dispatch')
class ShelfList(APIView):
    def post(self, request):
        serializer = serializers.ShelfPkList(data=request.data)
        if serializer.is_valid(raise_exception=True):
            shelfs = Shelf.objects.filter(pk__in=serializer.data['shelfs'])
            data = render_to_string(template_name="laboratory/components/shelfdetail.html", context={'shelfs':shelfs}, request=request)
        return Response({'data':data})



class ShelfObjectViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ShelfObjectTableSerializer
    queryset = ShelfObject.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['name', 'last_update', ]  # for the global search
    filterset_class = serializers.ShelfObjectFilterSet
    ordering_fields = ['last_update']
    ordering = ('-last_update',)  # default order

    def get_queryset(self):
        if self.data['shelf'] is None:
            return self.queryset.none()
        return self.queryset.filter(
            in_where_laboratory=self.data['laboratory'],
            shelf=self.data['shelf']

        )

    def retrieve(self, request, pk, **kwargs):
        self.organization = get_object_or_404(OrganizationStructure, pk=pk)
        validate_serializer = ShelfLabViewSerializer(data=request.GET)
        validate_serializer.set_user(request.user)
        validate_serializer.is_valid(raise_exception=True)
        self.data = validate_serializer.data

        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {'data': data, 'recordsTotal': ShelfObject.objects.count(),
                    'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}
        return Response(self.get_serializer(response).data)
