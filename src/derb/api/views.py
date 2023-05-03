from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from derb.api.serializers import InformSerializer, LaboratorySerializer, ObjectsSerializer, IncidentReportSerializer, \
    OrganizationUsersSerializer
from laboratory.models import Object, Inform, OrganizationStructure, Laboratory
from risk_management.models import IncidentReport
from auth_and_perms.organization_utils import user_is_allowed_on_organization, organization_can_change_laboratory


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
        org = OrganizationStructure.objects.get(pk=org_pk)
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

    If lab parameter is included in the query, it gets all users that can access a lab
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, org_pk):
        org = get_object_or_404(OrganizationStructure, pk=org_pk) # OrganizationStructure.objects.get(pk=org_pk)
        user_is_allowed_on_organization(request.user, org)
        try:
            lab_pk = int(request.query_params['lab'][0])
            lab = get_object_or_404(Laboratory, pk=lab_pk)
            organization_can_change_laboratory(lab, org)
            lab_queryset = OrganizationStructure.os_manager.organization_tree(organization=org_pk)
            serializer = OrganizationUsersSerializer(lab_queryset, many=True)
            user_data = self.extract_users_from_lab(serializer.data)
        except:
            serializer = OrganizationUsersSerializer(org)
            user_data = self.extract_users_from_organization(serializer.data)
        return Response(user_data)

    def extract_users_from_organization(self, data):
        response_data = []
        used_ids = []
        for id in data['users']:
            if not(id in used_ids):
                val = {'key': id, 'value':User.objects.get(pk=id).username}
                response_data.append(val)
                used_ids.append(id)
        return response_data

    def extract_users_from_lab(self, data):
        response_data = []
        used_ids = []
        for values in data:
            for id in values['users']:
                if not(id in used_ids):
                    val = {'key': id, 'value':User.objects.get(pk=id).username}
                    response_data.append(val)
                    used_ids.append(id)
        return response_data

"""class LaboratoryUsersView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, org_pk, lab_pk):
        org = OrganizationStructure.objects.get(pk=org_pk)
        lab = Laboratory.objects.get(pk=lab_pk)
        user_is_allowed_on_organization(request.user, org)
        organization_can_change_laboratory(lab, org)
        # lab_queryset = OrganizationStructure.os_manager.filter_labs_by_user(request.user)
        lab_queryset = OrganizationStructure.os_manager.organization_tree(organization=org_pk)
        serializer = OrganizationUsersSerializer(lab.organization, many=True)
        user_data = self.extract_users_from_organization(serializer.data)
        return Response(user_data)

    def extract_users_from_lab(self, data):
        response_data = []
        used_ids = []
        for values in data:
            for id in values['users']:
                if not(id in used_ids):
                    val = {'key': id, 'value':User.objects.get(pk=id).username}
                    response_data.append(val)
                    used_ids.append(id)
        return response_data
"""