from django.conf import settings
from django.http import JsonResponse
from django.contrib.admin.models import ADDITION, DELETION, CHANGE
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets, status
from rest_framework.authentication import SessionAuthentication, BaseAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from rest_framework.filters import SearchFilter, OrderingFilter

from sga.api.filterset import RecipientsFilterSet
from sga.api.serializers import RecipientSizeSerializer, \
    RecipientSizeDataTableSerializer, RecipientSizeDeleteSerializer
from laboratory.models import OrganizationStructure
from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.utils import organilab_logentry
from sga.forms import RecipientSizeForm
from sga.models import RecipientSize, DisplayLabel, TemplateSGA


class RecipientSizeAPI(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication, BaseAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = RecipientSize.objects.all()
    serializer_class = RecipientSizeDataTableSerializer
    permissions_by_endpoint = {
        "create": ["sga.view_recipientsize", "sga.add_recipientsize"],
        "list": ["sga.view_recipientsize"],
        "update": ["sga.view_recipientsize", "sga.change_recipientsize"],
        "delete": ["sga.view_recipientsize", "sga.delete_recipientsize"]
    }
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['name', 'width', 'height','width_unit','height_unit']
    filterset_class = RecipientsFilterSet
    ordering_fields = ['name','width','height']
    ordering = ('-name','-width','height')

    def _check_permission_on_organization(self, request, org_pk, method_name):
        if request.user.has_perms(self.permissions_by_endpoint[method_name]):
            self.organization = get_object_or_404(
                OrganizationStructure.objects.using(settings.READONLY_DATABASE),
                pk=org_pk
            )
            user_is_allowed_on_organization(request.user, self.organization)
        else:
            raise PermissionDenied()
    @action(detail=True, methods=['get'])
    def get_recipient(self, request, org_pk, pk=None, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, 'list')
        if pk:
            recipient = get_object_or_404(RecipientSize, pk=pk)
            serializer = RecipientSizeSerializer(recipient)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def create_recipient(self, request, org_pk, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, 'create')
        serializer = RecipientSizeSerializer(data= request.data)

        if serializer.is_valid():

            recipient = serializer.save()
            organilab_logentry(request.user, recipient, ADDITION,
                               'recipient size', relobj=[self.organization],
                               changed_data=["name","heigth","height_unit",
                                             "width","width_unit"])

            return JsonResponse({'detail': _("Item created successfully.")},
                                status=status.HTTP_201_CREATED)
        return JsonResponse({"errors":serializer.errors},status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, org_pk, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, 'list')
        recordsTotal = self.get_queryset().count()
        queryset = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(queryset)
        response = {'data': data,
                    'recordsTotal': recordsTotal,
                    'recordsFiltered': queryset.count(),
                    'draw': self.request.GET.get('draw', 1)}

        return Response(self.get_serializer(response).data)

    @action(detail=True, methods=['put'])
    def update_recipient(self, request, org_pk, pk=None, *args, **kwargs):
        self._check_permission_on_organization(request, org_pk, 'update')

        if pk:
            recipient = get_object_or_404(RecipientSize, pk=pk)
            form = RecipientSizeForm(data=request.data,instance=recipient)
            serializer = RecipientSizeSerializer(data=request.data, instance=recipient)

            if serializer.is_valid() and form.is_valid():
                recipient = serializer.save()
                organilab_logentry(request.user, recipient, CHANGE,
                                   'recipient size', relobj=[self.organization],
                                   changed_data=form.changed_data)

                return JsonResponse({'detail':  _("Item updated successfully.")},
                                    status=status.HTTP_200_OK)
            else:
                return Response({'errors':serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['delete'])
    def delete_recipient(self, request, org_pk):
        self._check_permission_on_organization(request, org_pk, 'delete')
        serializer = RecipientSizeDeleteSerializer(data=request.data)

        if serializer.is_valid():
            recipient = serializer.validated_data['pk']
            diplays= DisplayLabel.objects.filter(recipient_size=recipient)
            templatesga = TemplateSGA.objects.filter(recipient_size=recipient)
            if not diplays.exists() and not templatesga.exists():

                organilab_logentry(request.user, recipient, DELETION,
                                   'recipient size', relobj=[self.organization])
                recipient.delete()

                return JsonResponse({'detail': _('Item deleted successfully.')},
                                    status=status.HTTP_200_OK)
            else:
               return Response({"errors": _("The container cannot be deleted of because it is being used.")},status=status.HTTP_409_CONFLICT)

        return Response(status=status.HTTP_400_BAD_REQUEST)
