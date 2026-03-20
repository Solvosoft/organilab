from django.views.generic.base import TemplateView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auth_and_perms.api.serializers import AuthenticateDataRequestSerializer
from auth_and_perms.models import AuthenticateDataRequest


class PermissionDeniedView(TemplateView):
    template_name = "laboratory/permission_denied.html"


# TODO: migrate to djgentelella.async_notification.registry.register_context
# context = [("data.name", "name"), ("data.business_email", "Business email"), ...]
# update_template_context("Request demo", "New demo request", context, message=...)


class SignDataRequestViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        instance = AuthenticateDataRequest.objects.filter(
            id_transaction=request.data["data"]["id_transaction"]
        ).first()
        if instance:
            data = request.data.get("data")
            if data:
                serializer = AuthenticateDataRequestSerializer(instance, data=data)
                if serializer.is_valid():
                    serializer.save()
            return Response({"data": True})
        return Response({"data": None})
