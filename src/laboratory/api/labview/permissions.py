"""Autorización de la capa labview.

Dos capas que **no se sustituyen entre sí**: el permiso de Django por acción y
el ámbito multi-tenant (organización + laboratorio).  Varios viewsets del
proyecto declaran ``permission_classes = (PermissionByLaboratoryInOrganization,)``
y con eso pierden ``AllPermissionByAction``, dejando su diccionario ``perms``
inerte; aquí se encadenan las dos a propósito.
"""

from django.conf import settings
from django.shortcuts import get_object_or_404
from djgentelella.permission_management import AllPermissionByAction

from laboratory.models import Laboratory, OrganizationStructure
from laboratory.utils import PermissionByLaboratoryInOrganization

#: Orden: primero el permiso por acción (barato y fail-closed: una acción no
#: mapeada responde 403), después el ámbito, que además deja
#: ``view.organization`` y ``view.laboratory`` listos para los serializers.
LABVIEW_PERMISSIONS = (AllPermissionByAction, PermissionByLaboratoryInOrganization)


class LabviewScopedMixin:
    """Resuelve organización y laboratorio desde la URL, nunca del cuerpo.

    Quién puede nombrar qué laboratorio es una decisión de autorización, y las
    ``permission_classes`` de DRF son por modelo, no por objeto: no distinguen
    un laboratorio de otro.  Por eso el ámbito se toma del prefijo de la ruta.
    """

    authentication_classes = None  # lo fija cada viewset concreto
    permission_classes = LABVIEW_PERMISSIONS

    @property
    def org_pk(self):
        return self.kwargs.get("org_pk")

    @property
    def lab_pk(self):
        return self.kwargs.get("lab_pk")

    def get_organization(self):
        if not hasattr(self, "_organization"):
            self._organization = get_object_or_404(
                OrganizationStructure.objects.using(settings.READONLY_DATABASE),
                pk=self.org_pk,
            )
        return self._organization

    def get_laboratory(self):
        if not hasattr(self, "_laboratory"):
            self._laboratory = get_object_or_404(
                Laboratory.objects.using(settings.READONLY_DATABASE), pk=self.lab_pk
            )
        return self._laboratory

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["org_pk"] = self.org_pk
        context["lab_pk"] = self.lab_pk
        context["laboratory"] = self.get_laboratory()
        context["organization"] = self.get_organization()
        return context
