from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from auth_and_perms.api.serializers import RolSerializer
from auth_and_perms.models import Rol
from laboratory.models import OrganizationStructure


class RolAPI(mixins.ListModelMixin,
             mixins.UpdateModelMixin,
             mixins.CreateModelMixin,
             viewsets.GenericViewSet):

    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        self.request=request
        return super().create(request, *args, **kwargs)


    def perform_create(self, serializer):
        super().perform_create(serializer)
        organizationstructure = OrganizationStructure.objects.filter(pk=self.request.data['rol']).first()
        if organizationstructure:
            serializer.instance.organizationstructure_set.add(organizationstructure)
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)