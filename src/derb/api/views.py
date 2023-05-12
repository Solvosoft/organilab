from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.authentication import SessionAuthentication
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from derb.api.serializers import InformSerializer, LaboratorySerializer, ObjectsSerializer, IncidentReportSerializer, \
    UsersSerializer
from laboratory.models import Object, Inform, OrganizationStructure, Laboratory
from risk_management.models import IncidentReport
from auth_and_perms.organization_utils import user_is_allowed_on_organization, organization_can_change_laboratory


class QueryPagination(LimitOffsetPagination):
    default_limit = 10


class InformView(APIView):
    """
    This view gets all informs associated to a user.
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, org_pk):
        org = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
        user_is_allowed_on_organization(request.user, org)
        inform_queryset = Inform.objects.filter(organization=org, created_by=request.user)
        serializer = InformSerializer(inform_queryset, many=True)
        return Response(serializer.data)


class LaboratoryByUserView(APIView):
    """
    This view gets all laboratories associated to a user.
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, org_pk):
        lab_queryset = OrganizationStructure.os_manager.filter_labs_by_user(request.user)
        serializer = LaboratorySerializer(lab_queryset, many=True)
        return Response(serializer.data)


class LaboratoryByOrgView(APIView):
    """
    This view gets all laboratories associated to an organization.
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, org_pk):
        org = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
        user_is_allowed_on_organization(request.user, org)
        lab_queryset = OrganizationStructure.os_manager.filter_labs_by_user(request.user, org_pk).filter()
        serializer = LaboratorySerializer(lab_queryset, many=True)
        return Response(serializer.data)


class ObjectsView(APIView):
    """
    This view gets all objects associated to an organization.
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = QueryPagination()
    def get(self, request, org_pk):
        org = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
        user_is_allowed_on_organization(request.user, org)
        objects_queryset = Object.objects.filter(organization__pk=org_pk)
        pagination = self.pagination_class
        result = pagination.paginate_queryset(objects_queryset, request)
        serializer = ObjectsSerializer(result, many=True)
        return Response(serializer.data)


class IncidentReportView(APIView):
    """
    This view gets all laboratories associated to an organization and a specific user.
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, org_pk):
        org = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
        user_is_allowed_on_organization(request.user, org)
        incident_queryset = IncidentReport.objects.filter(organization=org ,created_by=request.user)
        serializer = IncidentReportSerializer(incident_queryset, many=True)
        return Response(serializer.data)


class OrganizationUsersView(APIView):
    """
    This view gets all users associated to an organization.

    If lab parameter is included in the query, it gets all users that can access a lab
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, org_pk):
        org = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=org_pk)
        user_is_allowed_on_organization(request.user, org)
        try:
            lab_pk = int(request.query_params['lab'][0])
            lab = get_object_or_404(Laboratory, pk=lab_pk)
            organization_can_change_laboratory(lab, org)
            lab_queryset = OrganizationStructure.os_manager.organization_tree(organization=org_pk)
            users = User.objects.filter(organizationstructure__pk__in=lab_queryset.values_list("pk", flat=True)) #OrganizationUsersSerializer(lab_queryset, many=True)
            serializer = UsersSerializer(users.distinct(), many=True)

        except Exception as i:
            users = User.objects.filter(organizationstructure__pk=org.pk)
            serializer = UsersSerializer(users.distinct(), many=True)
        return Response(serializer.data)
