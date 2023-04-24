from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from derb.api.serializers import InformSerializer, LaboratorySerializer, ObjectsSerializer, OrganizationStrtSerializer, \
    IncidentReportSerializer
from laboratory.models import Object, Inform, Laboratory, OrganizationStructure
from risk_management.models import IncidentReport
from auth_and_perms.organization_utils import user_is_allowed_on_organization, organization_can_change_laboratory


class InformView(APIView):
    def get(self, request, org_pk):
        inform_queryset = Inform.objects.filter(organization__pk=org_pk)
        serializer = InformSerializer(inform_queryset, many=True)
        return Response(serializer.data)


class LaboratorytView(APIView):
    def get(self, request, org_pk):
        lab_queryset = Laboratory.objects.filter(organization__id=org_pk)
        serializer = LaboratorySerializer(lab_queryset, many=True)
        return Response(serializer.data)


class ObjectsView(APIView):
    def get(self, request, org_pk):
        objects_queryset = Object.objects.filter(organization__pk=org_pk)
        serializer = ObjectsSerializer(objects_queryset, many=True)
        return Response(serializer.data)


class IncidentReportView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, org_pk):
        print(request.user)
        incident_queryset = IncidentReport.objects.filter(created_by=request.user)
        serializer = IncidentReportSerializer(incident_queryset, many=True)
        return Response(serializer.data)

"""class OrganizationUserstView(APIView):
    def get(self, request, org_pk):
        org_queryset = OrganizationStructure.objects.filter(organization__pk=org_pk)
        serializer = OrganizationStrtSerializer(test, many=True)
        return Response(ser.data)"""