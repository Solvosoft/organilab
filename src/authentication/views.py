from async_notifications.register import update_template_context
from django.views.generic.base import TemplateView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auth_and_perms.api.serializers import AuthenticateDataRequestSerializer
from auth_and_perms.models import AuthenticateDataRequest


class PermissionDeniedView(TemplateView):
    template_name = 'laboratory/permission_denied.html'



context = [
    ('data.name', 'name'),
    ('data.business_email', 'Business email'),
    ('data.company_name', 'Company name'),
    ('data.country', 'Country'),
    ('data.phone_number', 'Phone number'),
]
update_template_context("Request demo",  "New demo request", context,
                        message="""User information:<br>
                        {{data.name}}<br>
                        {{data.business_email}}<br>
                        {{data.company_name}}<br>
                        {{data.country}}<br>
                        {{data.phone_number}}
                        """)


class SignDataRequestViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        instance = AuthenticateDataRequest.objects.filter(id_transaction=request.data['data']['id_transaction']).first()
        if instance:
            data = request.data.get('data')
            if data:
                serializer = AuthenticateDataRequestSerializer(instance, data=data)
                if serializer.is_valid():
                    serializer.save()
            return Response({'data': True})
        return Response({'data': None})

#