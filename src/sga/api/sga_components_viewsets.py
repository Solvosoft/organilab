from django.conf import settings
from django.http import JsonResponse
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
from django.utils.translation import gettext_lazy as _

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
    permissions_by_endpoint = {
        "list": ["sga.view_warningword"]
    }

    def _check_permission_on_organization(self, request, org_pk, method_name):
        if request.user.has_perms(self.permissions_by_endpoint[method_name]):
            self.organization = get_object_or_404(
                OrganizationStructure.objects.using(settings.READONLY_DATABASE),
                pk=org_pk
            )
            user_is_allowed_on_organization(request.user, self.organization)
        else:
            raise PermissionDenied()

    def list(self, request, org_pk, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, 'list')
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
    permissions_by_endpoint = {
        "create": ["sga.view_warningword", "sga.add_warningword"],
        "list": ["sga.view_warningword"],
        "update": ["sga.view_warningword", "sga.change_warningword"],
        "destroy": ["sga.view_warningword", "sga.delete_warningword"]
    }

    def _check_permission_on_organization(self, request, org_pk, method_name):
        if request.user.has_perms(self.permissions_by_endpoint[method_name]):
            self.organization = get_object_or_404(
                OrganizationStructure.objects.using(settings.READONLY_DATABASE),
                pk=org_pk
            )
            user_is_allowed_on_organization(request.user, self.organization)
        else:
            raise PermissionDenied()

    def retrieve(self, request, org_pk, pk=None, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, 'list')
        if pk:
            warning_word = get_object_or_404(WarningWord, pk=pk)
            serializer = self.get_serializer(warning_word)

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, org_pk, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, "create")
        serializer = WarningWordSerializer(data=request.data)

        if serializer.is_valid():
            warning_word = serializer.save()
            organilab_logentry(request.user, warning_word, ADDITION,
                               'warningword', relobj=[self.organization],
                               changed_data=list(serializer.validated_data.keys()))

            return JsonResponse({"detail": _("Warning word created successfully.")},
                                status=status.HTTP_201_CREATED)

        return JsonResponse({'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, org_pk, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, 'list')
        queryset = self.get_queryset().order_by('weigth')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse({'data': serializer.data})

    def update(self, request, org_pk, pk=None, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, 'update')
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=org_pk
        )

        if pk:
            warning_word = get_object_or_404(WarningWord, pk=pk)
            serializer = WarningWordSerializer(warning_word, data=request.data)

            if serializer.is_valid():
                warning_word = serializer.save()
                organilab_logentry(request.user, warning_word, CHANGE,
                                   'warningword', relobj=[organization],
                                   changed_data=list(serializer.validated_data.keys()))

                return JsonResponse({"detail": _("Updated")},
                                    status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, org_pk, pk=None, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, 'destroy')
        organization = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE),
            pk=org_pk
        )

        if pk:
            warning_word = get_object_or_404(WarningWord, pk=pk)
            organilab_logentry(request.user, warning_word, DELETION,
                               'warningword', relobj=[organization])
            warning_word.delete()

            return JsonResponse({'detail': _('Deleted successfully')},
                                status=status.HTTP_200_OK)

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
    permissions_by_endpoint = {
        "add_danger_indication": ["sga.view_dangerindication", "sga.add_dangerindication"],
        "list_danger_indications": ["sga.view_dangerindication"],
        "update_danger_indication": ["sga.view_dangerindication", "sga.change_dangerindication"],
        "delete_danger_indication": ["sga.view_dangerindication", "sga.delete_dangerindication"]
    }

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
            danger_indication = serializer.save()
            organilab_logentry(request.user, danger_indication, ADDITION,
                               'dangerindication', relobj=[organization],
                               changed_data=list(serializer.validated_data.keys()))

            danger_indications = self.get_queryset().order_by('code')
            template = render_to_string('sga/substance/danger_indication_api.html',
                                        {'danger_indications': danger_indications},
                                        request)

            return Response({'data': template}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def list_danger_indications(self, request, org_pk):
        self._check_permission_on_organization(request, org_pk, 'list_danger_indications')
        danger_indications = self.get_queryset().order_by('code')
        template = render_to_string('sga/substance/danger_indication_api.html',
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
                danger_indication = serializer.save()
                organilab_logentry(request.user, danger_indication, CHANGE,
                                   'dangerindication', relobj=[organization],
                                   changed_data=list(serializer.validated_data.keys()))

                danger_indications = DangerIndication.objects.all()

                template = render_to_string('sga/substance/danger_indication_api.html',
                                            {'danger_indications': danger_indications},
                                            request)

                return Response({'data': template}, status=status.HTTP_200_OK)  # Devolver Json

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
            template = render_to_string('sga/substance/danger_indication_api.html',
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
    permissions_by_endpoint = {
        "add_prudence_advice": ["sga.view_prudenceadvice", "sga.add_prudenceadvice"],
        "list_prudence_advices": ["sga.view_prudenceadvice"],
        "update_prudence_advice": ["sga.view_prudenceadvice", "sga.change_prudenceadvice"],
        "delete_prudence_advice": ["sga.view_prudenceadvice", "sga.change_prudenceadvice"]
    }

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
            prudence_advice = serializer.save()
            organilab_logentry(request.user, prudence_advice, ADDITION,
                               'prudenceadvice', relobj=[organization],
                               changed_data=list(serializer.validated_data.keys()))

            prudence_advices = self.get_queryset().order_by('code')
            template = render_to_string('sga/substance/prudence_advice_api.html',
                                        {'prudence_advices': prudence_advices},
                                        request)

            return Response({'data': template}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def list_prudence_advices(self, request, org_pk):
        self._check_permission_on_organization(request, org_pk, 'list_prudence_advices')
        prudence_advices = self.get_queryset().order_by('code')
        template = render_to_string('sga/substance/prudence_advice_api.html',
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
                prudence_advice = serializer.save()
                organilab_logentry(request.user, prudence_advice, CHANGE,
                                   'prudenceadvice', relobj=[organization],
                                   changed_data=list(serializer.validated_data.keys()))

                prudence_advices = PrudenceAdvice.objects.all()

                template = render_to_string('sga/substance/prudence_advice_api.html',
                                            {'prudence_advices': prudence_advices},
                                            request)

                return Response({'data': template}, status=status.HTTP_200_OK)  # Devolver Json

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
            template = render_to_string('sga/substance/prudence_advice_api.html',
                                        {'prudence_advices': prudence_advices},
                                        request)

            return Response({'data': template}, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)
