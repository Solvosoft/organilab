from django.contrib.contenttypes.models import ContentType
from djgentelella.views.select2autocomplete import BaseSelect2View
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from djgentelella.groute import register_lookups

from academic.api.serializers import ValidateUserAccessOrgSerializer
from academic.models import Procedure
from api.utils import AllPermissionOrganization
from laboratory.utils import get_pk_org_ancestors


@register_lookups(
    prefix="custom_procedure_template", basename="custom_procedure_template"
)
class ProcedureGModelLookup(BaseSelect2View):
    model = Procedure
    fields = ["title"]
    org_pk = None
    serializer = None
    authentication_classes = [SessionAuthentication]
    permission_classes = [
        IsAuthenticated,
        AllPermissionOrganization(
            perms=["academic.view_procedure"],
            as_param_method="GET",
            lookup_keyword="organization",
        ),
    ]

    def get_queryset(self):

        queryset = super().get_queryset()
        if self.org_pk:
            organizations = get_pk_org_ancestors(self.org_pk.pk)
            content_type = ContentType.objects.get(
                app_label="laboratory", model="organizationstructure"
            )
            queryset = queryset.filter(
                object_id__in=organizations, content_type=content_type
            )
        else:
            queryset = queryset.none()
        return queryset

    def list(self, request, *args, **kwargs):

        self.serializer = ValidateUserAccessOrgSerializer(
            data=request.GET, context={"user": request.user}
        )
        if self.serializer.is_valid():
            self.org_pk = self.serializer.validated_data["organization"]
            return super().list(request, *args, **kwargs)
        return Response(
            {
                "status": "Bad request",
                "errors": self.serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
