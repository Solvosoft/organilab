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

from sga.models import WarningWord, DangerIndication, PrudenceAdvice
from sga.api.serializers import WarningWordSerializer, WarningWordDataTableSerializer, \
    DangerIndicationSerializer, DangerIndicationDataTableSerializer, \
    PrudenceAdviceSerializer, PrudenceAdviceDataTableSerializer
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

            warning_words = self.get_queryset().order_by('weigth')
            template = render_to_string('sga/warning_word.html',
                                        {'warning_words': warning_words},
                                        request)

            return Response({'data': template}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def list_warning_words(self, request, org_pk):
        self._check_permission_on_organization(request, org_pk, 'list_warning_words')
        warning_words = self.get_queryset().order_by('weigth')
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

                warning_words = self.get_queryset().order_by('weigth')

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
            warning_word = get_object_or_404(WarningWord, pk=pk)
            organilab_logentry(request.user, warning_word, DELETION,
                               'warningword', relobj=[organization])
            warning_word.delete()

            warning_words = self.get_queryset().order_by('weigth')
            template = render_to_string('sga/warning_word.html',
                                        {'warning_words': warning_words},
                                        request)

            return Response({'data': template}, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class DangerIndicationTableView(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = DangerIndicationDataTableSerializer
    queryset = DangerIndication.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['code', 'description', 'warning_words__name']
    filterset_fields = ['code', 'description', 'warning_words__name']
    ordering_fields = ['code']

    def list(self, request, *args, **kwargs):
        recordsTotal = self.get_queryset().count()
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {'data': data,
                    'recordsTotal': recordsTotal,
                    'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}

        return Response(self.get_serializer(response).data)


class DangerIndicationAPI(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication, BaseAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = DangerIndication.objects.all()
    serializer_class = DangerIndicationSerializer
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
    def add_danger_indication(self, request, org_pk):
        self._check_permission_on_organization(request, org_pk, 'add_danger_indication')
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=org_pk
        )
        serializer = DangerIndicationSerializer(data=request.data)

        if serializer.is_valid():
            danger_indication = DangerIndication.objects.create(
                code=serializer.data['code'],
                description=serializer.data['description'],
                warning_class=serializer.data['warning_class'],
                warning_category=serializer.data['warning_category'],
                prudence_advice=serializer.data['prudence_advice']
            )
            danger_indication.save()
            organilab_logentry(request.user, danger_indication, ADDITION,
                               'dangerindication', relobj=[organization])

            danger_indications = self.get_queryset().order_by('code')
            template = render_to_string('sga/danger_indication.html',
                                        {'danger_indications': danger_indications},
                                        request)

            return Response({'data': template}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def list_danger_indications(self, request, org_pk):
        self._check_permission_on_organization(request, org_pk, 'list_danger_indications')
        danger_indications = self.get_queryset().order_by('code')
        template = render_to_string('sga/danger_indication.html',
                                    {'danger_indications': danger_indications},
                                    request)

        return Response({'data': template})

    @action(detail=True, methods=['put'])
    def update_danger_indication(self, request, org_pk, pk=None):
        self._check_permission_on_organization(request, org_pk, 'update_danger_indication')
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=org_pk
        )
        danger_indication = None

        if pk:
            serializer = DangerIndicationSerializer(data=request.data)

            if serializer.is_valid():
                danger_indication = get_object_or_404(DangerIndication, pk=pk)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            if danger_indication:
                danger_indication.code = serializer.data['code'],
                danger_indication.description = serializer.data['description'],
                danger_indication.warning_class = serializer.data['warning_class'],
                danger_indication.warning_category = serializer.data['warning_category'],
                danger_indication.prudence_advice = serializer.data['prudence_advice']

                danger_indication.save()
                organilab_logentry(request.user, danger_indication, CHANGE,
                                   'dangerindication', relobj=[organization])

                danger_indications = self.get_queryset().order_by('code')

                template = render_to_string('sga/danger_indication.html',
                                            {'danger_indications': danger_indications},
                                            request)

                return Response({'data': template}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def delete_danger_indication(self, request, org_pk, pk=None):
        self._check_permission_on_organization(request, org_pk, 'delete_danger_indication')
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=org_pk
        )

        if pk:
            danger_indication = get_object_or_404(DangerIndication, pk=pk)
            organilab_logentry(request.user, danger_indication, DELETION,
                               'dangerindication', relobj=[organization])
            danger_indication.delete()

            danger_indications = self.get_queryset().order_by('code')
            template = render_to_string('sga/danger_indication.html',
                                        {'danger_indications': danger_indications},
                                        request)

            return Response({'data': template}, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class PrudenceAdviceTableView(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = PrudenceAdviceDataTableSerializer
    queryset = PrudenceAdvice.objects.all()
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['code', 'name', 'prudence_advice_help']
    filterset_fields = ['code', 'name', 'prudence_advice_help']
    ordering_fields = ['code']

    def list(self, request, *args, **kwargs):
        recordsTotal = self.get_queryset().count()
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {'data': data,
                    'recordsTotal': recordsTotal,
                    'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}

        return Response(self.get_serializer(response).data)


class PrudenceAdviceAPI(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication, BaseAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = PrudenceAdvice.objects.all()
    serializer_class = PrudenceAdviceSerializer
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
    def add_prudence_advice(self, request, org_pk):
        self._check_permission_on_organization(request, org_pk, 'add_prudence_advice')
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=org_pk
        )
        serializer = PrudenceAdviceSerializer(data=request.data)

        if serializer.is_valid():
            prudence_advice = PrudenceAdvice.objects.create(
                code=serializer.data['code'],
                name=serializer.data['name'],
                prudence_advice_help=serializer.data['prudence_advice_help']
            )
            prudence_advice.save()
            organilab_logentry(request.user, prudence_advice, ADDITION,
                               'prudenceadvice', relobj=[organization])

            prudence_advices = self.get_queryset().order_by('code')
            template = render_to_string('sga/prudence_advice.html',
                                        {'prudence_advices': prudence_advices},
                                        request)

            return Response({'data': template}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def list_prudence_advices(self, request, org_pk):
        self._check_permission_on_organization(request, org_pk, 'list_prudence_advices')
        prudence_advices = self.get_queryset().order_by('code')
        template = render_to_string('sga/prudence_advice.html',
                                    {'prudence_advices': prudence_advices},
                                    request)

        return Response({'data': template})

    @action(detail=True, methods=['put'])
    def update_prudence_advice(self, request, org_pk, pk=None):
        self._check_permission_on_organization(request, org_pk, 'update_prudence_advice')
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=org_pk
        )
        prudence_advice = None

        if pk:
            serializer = PrudenceAdviceSerializer(data=request.data)

            if serializer.is_valid():
                prudence_advice = get_object_or_404(PrudenceAdvice, pk=pk)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            if prudence_advice:
                prudence_advice.code = request.data['code']
                prudence_advice.name = request.data['name']
                prudence_advice.prudence_advice_help = request.data['prudence_advice_help']
                prudence_advice.save()
                organilab_logentry(request.user, prudence_advice, CHANGE,
                                   'prudenceadvice', relobj=[organization])

                prudence_advices = self.get_queryset().order_by('code')

                template = render_to_string('sga/prudence_advice.html',
                                            {'prudence_advices': prudence_advices},
                                            request)

                return Response({'data': template}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def delete_prudence_advice(self, request, org_pk, pk=None):
        self._check_permission_on_organization(request, org_pk, 'delete_prudence_advice')
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=org_pk
        )

        if pk:
            prudence_advice = get_object_or_404(PrudenceAdvice, pk=pk)
            organilab_logentry(request.user, prudence_advice, DELETION,
                               'prudenceadvice', relobj=[organization])
            prudence_advice.delete()

            prudence_advices = self.get_queryset().order_by('code')
            template = render_to_string('sga/prudence_advice.html',
                                        {'prudence_advices': prudence_advices},
                                        request)

            return Response({'data': template}, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)
