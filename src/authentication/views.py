from urllib.parse import urlencode

from djgentelella.async_notification.registry import register_context
from django.conf import settings
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auth_and_perms.api.serializers import AuthenticateDataRequestSerializer
from auth_and_perms.models import AuthenticateDataRequest


class PermissionDeniedView(TemplateView):
    template_name = "laboratory/permission_denied.html"


register_context(
    code="request-demo",
    subject="New demo request",
    models={},
    extra_variables={
        "data.name": "Name",
        "data.business_email": "Business email",
        "data.company_name": "Company name",
        "data.country": "Country",
        "data.phone_number": "Phone number",
    },
)


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


def oidc_logout_url(request):
    login_url = str(reverse_lazy("login"))
    id_token = request.session.get("oidc_id_token")
    if not id_token:
        return login_url

    logout_endpoint = getattr(settings, "OIDC_OP_LOGOUT_ENDPOINT", "")
    if not logout_endpoint:
        return login_url

    params = {"id_token_hint": id_token}
    post_logout_uri = getattr(settings, "OIDC_POST_LOGOUT_REDIRECT_URL", "")
    if post_logout_uri:
        params["post_logout_redirect_uri"] = post_logout_uri
    return f"{logout_endpoint}?{urlencode(params)}"
