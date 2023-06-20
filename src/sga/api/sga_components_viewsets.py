from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.admin.models import ADDITION, DELETION, CHANGE
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets, status
from rest_framework.authentication import SessionAuthentication, BaseAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.filters import SearchFilter, OrderingFilter

from sga.models import WarningWord
from sga.api.serializers import WarningWordSerializer, WarningWordDataTableSerializer
from laboratory.models import OrganizationStructure
from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.utils import organilab_logentry


class WarningWordTableView(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = WarningWordDataTableSerializer
    queryset = WarningWord.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'weigth']
    filterset_fields = ['name', 'weigth']
    ordering_fields = ['weigth']

    def list(self, request, *args, **kwargs):
        recordsTotal = self.get_queryset().count()
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {'data': data,
                    'recordsTotal': recordsTotal,
                    'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}

        return Response(self.get_serializer(response).data)


class WarningWordAPI(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication, BaseAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = WarningWord.objects.all()
    serializer_class = WarningWordSerializer
    permissions_by_endpoint = {}

    def _check_permission_on_organization(self, request, org_pk, method_name):
        if request.user.has_perms(self.permissions_by_endpoint[method_name]):
            self.organization = get_object_or_404(
                OrganizationStructure.objects.using(settings.READONLY_DATABASE),
                pk=org_pk
            )
            user_is_allowed_on_organization(request.user, self.organization)
        else:
            raise PermissionDenied()

    @action(detail=False, methods=['post'])
    def add_warning_word(self, request, org_pk):
        self._check_permission_on_organization(request, org_pk, 'add_warning_word')
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=org_pk
        )
        serializer = WarningWordSerializer(data=request.data)

        if serializer.is_valid():
            warning_word = WarningWord.objects.create(
                name=serializer.data['name'],
                weigth=serializer.data['weigth']
            )
            warning_word.save()
            organilab_logentry(request.user, warning_word, ADDITION,
                               'warningword', relobj=[organization])

            warning_words = self.get_queryset().order_by('pk')
            template = render_to_string('sga/warning_word.html',
                                        {'warning_words': warning_words},
                                        request)

            return Response({'data': template}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def list_warning_words(self, request, org_pk):
        self._check_permission_on_organization(request, org_pk, 'list_warning_words')
        warning_words = self.get_queryset().order_by('pk')
        template = render_to_string('sga/warning_word.html',
                                    {'warning_words': warning_words},
                                    request)

        return Response({'data': template})

    @action(detail=True, methods=['put'])
    def update_warning_word(self, request, org_pk, pk=None):
        self._check_permission_on_organization(request, org_pk, 'update_warning_word')
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=org_pk
        )
        warning_word = None

        if pk:
            serializer = WarningWordSerializer(data=request.data)

            if serializer.is_valid():
                warning_word = get_object_or_404(WarningWord, pk=pk)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            if warning_word:
                warning_word.name = request.data['name']
                warning_word.weigth = request.data['weigth']
                warning_word.save()
                organilab_logentry(request.user, warning_word, CHANGE,
                                   'warningword', relobj=[organization])

                warning_words = self.get_queryset().order_by('pk')

                template = render_to_string('sga/warning_word.html',
                                            {'warning_words': warning_words},
                                            request)

                return Response({'data': template}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def delete_warning_word(self, request, org_pk, pk=None):
        self._check_permission_on_organization(request, org_pk, 'delete_warning_word')
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=org_pk
        )

        if pk:
            warning_word = get_object_or_404(
                WarningWord.objects.using(settings.READONLY_DATABASE),
                pk=pk
            )
            organilab_logentry(request.user, warning_word, DELETION,
                               'warningword', relobj=[organization])
            warning_word.delete()

            warning_words = self.get_queryset().order_by('pk')
            template = render_to_string('sga/warning_word.html',
                                        {'warning_words': warning_words},
                                        request)

            return Response({'data': template}, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)
