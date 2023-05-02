from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from derb.api.serializers import InformSerializer, LaboratorySerializer, ObjectsSerializer, OrganizationStrtSerializer, \
    IncidentReportSerializer
from laboratory.models import Object, Inform, OrganizationStructure
from risk_management.models import IncidentReport
from auth_and_perms.organization_utils import user_is_allowed_on_organization


class InformView(APIView):
    """
    This view gets all informs associated to a user.
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, org_pk):
        org = OrganizationStructure.objects.get(pk=org_pk)
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
    def get(self, request, org_pk=None):
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
        org = OrganizationStructure.objects.get(pk=org_pk)
        user_is_allowed_on_organization(request.user, org)
        lab_queryset = OrganizationStructure.os_manager.filter_labs_by_user(request.user, org_pk)
        serializer = LaboratorySerializer(lab_queryset, many=True)
        return Response(serializer.data)


class ObjectsView(APIView):
    """
    This view gets all objects associated to an organization.
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, org_pk):
        org = OrganizationStructure.objects.get(pk=org_pk)
        user_is_allowed_on_organization(request.user, org)
        objects_queryset = Object.objects.filter(organization__pk=org_pk)
        serializer = ObjectsSerializer(objects_queryset, many=True)
        return Response(serializer.data)


class IncidentReportView(APIView):
    """
    This view gets all laboratories associated to an organization and a specific user.
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, org_pk):
        org = OrganizationStructure.objects.get(pk=org_pk)
        user_is_allowed_on_organization(request.user, org)
        incident_queryset = IncidentReport.objects.filter(organization=org ,created_by=request.user)
        serializer = IncidentReportSerializer(incident_queryset, many=True)
        return Response(serializer.data)

class OrganizationUsersView(APIView):
    """
    This view gets all users associated to an organization.
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, org_pk):
        org = OrganizationStructure.objects.get(pk=org_pk)
        user_is_allowed_on_organization(request.user, org)
        serializer = OrganizationStrtSerializer(org)
        return Response(serializer.data)
