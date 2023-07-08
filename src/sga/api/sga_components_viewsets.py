from django.conf import settings
from django.http import JsonResponse, QueryDict
from django.contrib.admin.models import ADDITION, DELETION, CHANGE
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets, status
from rest_framework.authentication import SessionAuthentication, BaseAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.exceptions import PermissionDenied
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
from sga.views.substance.forms import WarningWordForm, DangerIndicationForm, \
    PrudenceAdviceForm


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
        form = WarningWordForm(request.POST)

        if form.is_valid():
            warning_word = form.save()
            organilab_logentry(request.user, warning_word, ADDITION,
                               'warning word', relobj=[self.organization],
                               changed_data=form.changed_data)

            return JsonResponse({"detail": _("Item created successfully.")},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(status=status.HTTP_400_BAD_REQUEST)

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

        if pk:
            warning_word = get_object_or_404(WarningWord, pk=pk)
            form = WarningWordForm(request.data, instance=warning_word)

            if form.is_valid():
                warning_word = form.save()
                organilab_logentry(request.user, warning_word, CHANGE,
                                   'warning word', relobj=[self.organization],
                                   changed_data=form.changed_data)

                return JsonResponse({"detail": _("Item updated successfully.")},
                                    status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, org_pk, pk=None, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, 'destroy')

        if pk:
            warning_word = get_object_or_404(WarningWord, pk=pk)
            organilab_logentry(request.user, warning_word, DELETION,
                               'warning word', relobj=[self.organization])
            warning_word.delete()

            return JsonResponse({'detail': _('Item deleted successfully.')},
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
    permissions_by_endpoint = {
        "list": ["sga.view_dangerindication"]
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


class DangerIndicationAPI(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication, BaseAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = DangerIndication.objects.all()
    serializer_class = DangerIndicationSerializer
    permissions_by_endpoint = {
        "create": ["sga.view_dangerindication", "sga.add_dangerindication"],
        "list": ["sga.view_dangerindication"],
        "update": ["sga.view_dangerindication", "sga.change_dangerindication"],
        "destroy": ["sga.view_dangerindication", "sga.delete_dangerindication"]
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
            danger_indication = get_object_or_404(DangerIndication, pk=pk)
            serializer = self.get_serializer(danger_indication)

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, org_pk, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, 'create')
        form = DangerIndicationForm(request.POST)

        if form.is_valid():
            danger_indication = form.save()
            organilab_logentry(request.user, danger_indication, ADDITION,
                               'danger indication', relobj=[self.organization],
                               changed_data=form.changed_data)

            return JsonResponse({"detail": _("Item created successfully.")},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, org_pk, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, 'list')
        queryset = self.get_queryset().order_by('code')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)

            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse({'data': serializer.data})

    def update(self, request, org_pk, pk=None, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, 'update')

        if pk:
            danger_indication = get_object_or_404(DangerIndication, pk=pk)
            form = DangerIndicationForm(request.data, instance=danger_indication)

            if form.is_valid():
                danger_indication = form.save()
                organilab_logentry(request.user, danger_indication, CHANGE,
                                   'danger indication', relobj=[self.organization],
                                   changed_data=form.changed_data)

                return JsonResponse({'detail': _('Item updated successfully.')},
                                    status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, org_pk, pk=None, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, 'destroy')

        if pk:
            danger_indication = get_object_or_404(DangerIndication, pk=pk)
            organilab_logentry(request.user, danger_indication, DELETION,
                               'danger indication', relobj=[self.organization])
            danger_indication.delete()

            return JsonResponse({'detail': _('Item deleted successfully.')},
                                status=status.HTTP_200_OK)

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
    permissions_by_endpoint = {
        "list": ["sga.view_prudenceadvice"]
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


class PrudenceAdviceAPI(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication, BaseAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = PrudenceAdvice.objects.all()
    serializer_class = PrudenceAdviceSerializer
    permissions_by_endpoint = {
        "create": ["sga.view_prudenceadvice", "sga.add_prudenceadvice"],
        "list": ["sga.view_prudenceadvice"],
        "update": ["sga.view_prudenceadvice", "sga.change_prudenceadvice"],
        "destroy": ["sga.view_prudenceadvice", "sga.delete_prudenceadvice"]
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
            prudence_advice = get_object_or_404(PrudenceAdvice, pk=pk)
            serializer = self.get_serializer(prudence_advice)

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, org_pk, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, 'create')
        form = PrudenceAdviceForm(request.POST)

        if form.is_valid():
            prudence_advice = form.save()
            organilab_logentry(request.user, prudence_advice, ADDITION,
                               'prudence advice', relobj=[self.organization],
                               changed_data=form.changed_data)

            return JsonResponse({'detail': _("Item created successfully.")},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, org_pk, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, 'list')
        queryset = self.get_queryset().order_by('code')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)

            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return JsonResponse({'data': serializer.data})

    def update(self, request, org_pk, pk=None, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, 'update')

        if pk:
            prudence_advice = get_object_or_404(PrudenceAdvice, pk=pk)
            form = PrudenceAdviceForm(request.data, instance=prudence_advice)

            if form.is_valid():
                prudence_advice = form.save()
                organilab_logentry(request.user, prudence_advice, CHANGE,
                                   'prudence advice', relobj=[self.organization],
                                   changed_data=form.changed_data)

                return JsonResponse({'detail':  _("Item updated successfully.")},
                                    status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, org_pk, pk=None, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, 'destroy')

        if pk:
            prudence_advice = get_object_or_404(PrudenceAdvice, pk=pk)
            organilab_logentry(request.user, prudence_advice, DELETION,
                               'prudence advice', relobj=[self.organization])
            prudence_advice.delete()

            return JsonResponse({'detail': _('Item deleted successfully.')},
                                status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)
