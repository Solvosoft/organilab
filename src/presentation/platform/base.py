from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from djgentelella.history.utils import add_log
from djgentelella.permission_management import AllPermissionByAction
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

from auth_and_perms.organization_utils import organization_permissions, user_is_allowed_on_organization
from laboratory.models import OrganizationStructure

__all__ = ["ADDITION", "CHANGE", "DELETION", "OrganizationPermissionMixin", "RegistryViewSet"]


class OrganizationPermissionMixin:
    """Exige que los permisos de la acción vengan de un rol **de la organización**.

    ``ProfileMiddleware`` también suma roles de laboratorio y de edificio; con ellos se
    entra a las pantallas de un edificio, pero no se cambia la configuración de toda la
    organización (parámetros, correos, reglas de alerta).
    """

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        perms = (getattr(self, "perms", {}) or {}).get(self.action) or []
        organization = self.get_organization()
        available = organization_permissions(request.user, organization)
        if any(perm not in available for perm in perms):
            raise PermissionDenied


class RegistryViewSet(OrganizationPermissionMixin, viewsets.ViewSet):
    """Base de las APIs cuyas filas salen de un registro en código, no de una tabla.

    Parámetros y notificaciones listan lo que el código declara (``PARAMETERS``, los
    contextos de correo registrados) y guardan en base solo lo que la organización
    cambió. Las filas se identifican por su clave, que es lo que ``ObjectCRUD`` pone en
    la URL en lugar del pk.
    """

    authentication_classes = (SessionAuthentication, TokenAuthentication)
    permission_classes = (AllPermissionByAction,)
    lookup_value_regex = r"[\w.\-]+"
    perms = {}

    def get_organization(self):
        if not hasattr(self, "_organization"):
            organization = get_object_or_404(OrganizationStructure, pk=self.kwargs.get("org_pk"))
            user_is_allowed_on_organization(self.request.user, organization)
            self._organization = organization
        return self._organization

    def datatable(self, rows):
        term = (self.request.query_params.get("search") or "").lower()
        filtered = [row for row in rows if not term or term in " ".join(str(v) for v in row.values()).lower()]
        offset = int(self.request.query_params.get("offset") or 0)
        limit = int(self.request.query_params.get("limit") or len(filtered) or 1)
        return {
            "data": filtered[offset:offset + limit],
            "recordsTotal": len(rows),
            "recordsFiltered": len(filtered),
            "draw": int(self.request.query_params.get("draw") or 1),
        }

    def log(self, instance, flag, message, changed=None):
        add_log(
            self.request.user,
            instance,
            flag,
            instance._meta.verbose_name.title().lower(),
            changed or [],
            change_message=message,
            related_objects=[self.get_organization()],
        )
