from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from derb.api.serializers import InformSerializer, LaboratorySerializer, ObjectsSerializer, OrganizationStrtSerializer, \
    IncidentReportSerializer
from laboratory.models import Object, Inform, Laboratory, OrganizationStructure, UserOrganization
from risk_management.models import IncidentReport
from auth_and_perms.organization_utils import user_is_allowed_on_organization, organization_can_change_laboratory


class InformView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, org_pk):
        inform_queryset = Inform.objects.filter(created_by=request.user)
        serializer = InformSerializer(inform_queryset, many=True)
        return Response(serializer.data)


class LaboratoryByUserView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, org_pk):
        lab_queryset = OrganizationStructure.os_manager.filter_labs_by_user(request.user)
        serializer = LaboratorySerializer(lab_queryset, many=True)
        return Response(serializer.data)

class LaboratoryByOrgView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, org_pk):
        lab_queryset = OrganizationStructure.os_manager.filter_labs_by_user(request.user, org_pk)
        serializer = LaboratorySerializer(lab_queryset, many=True)
        return Response(serializer.data)


class ObjectsView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, org_pk):
        objects_queryset = Object.objects.filter(organization__pk=org_pk)
        serializer = ObjectsSerializer(objects_queryset, many=True)
        return Response(serializer.data)


class IncidentReportView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, org_pk):
        org = OrganizationStructure.objects.get(pk=org_pk)
        user_is_allowed_on_organization(request.user, org)
        incident_queryset = IncidentReport.objects.filter(created_by=request.user)
        serializer = IncidentReportSerializer(incident_queryset, many=True)
        return Response(serializer.data)

class OrganizationUsersView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, org_pk):
        org = OrganizationStructure.objects.get(pk=org_pk)
        user_is_allowed_on_organization(request.user, org)
        serializer = OrganizationStrtSerializer(org)
        return Response(serializer.data)
