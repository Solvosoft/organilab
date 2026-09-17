from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.shortcuts import get_object_or_404
from djgentelella.history.utils import add_log
from djgentelella.permission_management import AllPermissionByAction
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import OrganizationStructure

__all__ = ["ADDITION", "CHANGE", "DELETION", "RegistryViewSet"]


class RegistryViewSet(viewsets.ViewSet):
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
