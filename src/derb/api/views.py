from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.authentication import SessionAuthentication
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from derb.api.serializers import (
    InformSerializer,
    LaboratorySerializer,
    ObjectsSerializer,
    IncidentReportSerializer,
    UsersSerializer,
)
from laboratory.models import Object, Inform, OrganizationStructure, Laboratory
from risk_management.models import IncidentReport
from auth_and_perms.organization_utils import (
    user_is_allowed_on_organization,
    organization_can_change_laboratory,
)


class QueryPagination(LimitOffsetPagination):
    default_limit = 10


class InformView(APIView):
    """
    This view gets all informs associated to a user.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = QueryPagination()

    def get(self, request, org_pk):
        org = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
        )
        user_is_allowed_on_organization(request.user, org)
        inform_queryset = Inform.objects.filter(
            organization=org, created_by=request.user
        )
        pagination = self.pagination_class
        paginated_query = pagination.paginate_queryset(inform_queryset, request)
        serializer = InformSerializer(paginated_query, many=True)
        return Response(serializer.data)


class LaboratoryByUserView(APIView):
    """
    This view gets all laboratories associated to a user.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = QueryPagination()

    def get(self, request, org_pk):
        lab_queryset = OrganizationStructure.os_manager.filter_labs_by_user(
            request.user
        )
        pagination = self.pagination_class
        paginated_query = pagination.paginate_queryset(lab_queryset, request)
        serializer = LaboratorySerializer(paginated_query, many=True)
        return Response(serializer.data)


class LaboratoryByOrgView(APIView):
    """
    This view gets all laboratories associated to an organization.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = QueryPagination()

    def get(self, request, org_pk):
        org = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
        )
        user_is_allowed_on_organization(request.user, org)
        lab_queryset = OrganizationStructure.os_manager.filter_labs_by_user(
            request.user, org_pk
        ).filter()
        pagination = self.pagination_class
        paginated_query = pagination.paginate_queryset(lab_queryset, request)
        serializer = LaboratorySerializer(paginated_query, many=True)
        return Response(serializer.data)


class ObjectsView(APIView):
    """
    This view gets all objects associated to an organization.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = QueryPagination()

    def get(self, request, org_pk):
        org = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
        )
        user_is_allowed_on_organization(request.user, org)
        objects_queryset = Object.objects.filter(organization__pk=org_pk)
        pagination = self.pagination_class
        paginated_query = pagination.paginate_queryset(objects_queryset, request)
        serializer = ObjectsSerializer(paginated_query, many=True)
        return Response(serializer.data)


class IncidentReportView(APIView):
    """
    This view gets all laboratories associated to an organization and a specific user.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = QueryPagination()

    def get(self, request, org_pk):
        org = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
        )
        user_is_allowed_on_organization(request.user, org)
        incident_queryset = IncidentReport.objects.filter(
            organization=org, created_by=request.user
        )
        pagination = self.pagination_class
        paginated_query = pagination.paginate_queryset(incident_queryset, request)
        serializer = IncidentReportSerializer(paginated_query, many=True)
        return Response(serializer.data)


class OrganizationUsersView(APIView):
    """
    This view gets all users associated to an organization.

    If lab parameter is included in the query, it gets all users that can access a lab
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = QueryPagination()

    def get(self, request, org_pk):
        org = get_object_or_404(
            OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk
        )
        user_is_allowed_on_organization(request.user, org)
        pagination = self.pagination_class
        try:
            lab_pk = int(request.query_params["lab"][0])
            lab = get_object_or_404(Laboratory, pk=lab_pk)
            organization_can_change_laboratory(lab, org)
            lab_queryset = OrganizationStructure.os_manager.organization_tree(
                organization=org_pk
            )
            users = User.objects.filter(
                organizationstructure__pk__in=lab_queryset.values_list("pk", flat=True)
            )
            paginated_query = pagination.paginate_queryset(users.distinct(), request)
            serializer = UsersSerializer(paginated_query, many=True)

        except Exception as i:
            users = User.objects.filter(organizationstructure__pk=org.pk)
            paginated_query = pagination.paginate_queryset(users.distinct(), request)
            serializer = UsersSerializer(paginated_query, many=True)
        return Response(serializer.data)
