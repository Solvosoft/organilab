from django.contrib.admin.models import ADDITION, DELETION
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from djgentelella.history.api import BaseViewSetWithLogs

from auth_and_perms.organization_utils import user_is_allowed_on_organization
from laboratory.models import OrganizationStructure


class AmbientalViewSet(BaseViewSetWithLogs):
    """Base de las APIs del módulo ambiental.

    Reúne lo que ``BaseViewSetWithLogs`` no resuelve por sí solo en Organilab:

    * **Organización**: el ``org_pk`` de la URL acota el queryset, se asigna al
      crear y se comprueba que el usuario pertenezca a ella.
    * **Bitácora**: cada entrada se relaciona con la organización (y con lo que
      devuelva ``get_related_objects``), que es lo que acota la pantalla de
      bitácora de la organización.
    * **Papelera**: el ``perform_destroy`` de la librería llama a
      ``instance.delete(user=...)`` sin ``related_objects``, así que el objeto
      borrado no aparecería en la papelera de la organización. Aquí se pasan.
    """

    def get_organization(self):
        if not hasattr(self, "_organization"):
            organization = get_object_or_404(
                OrganizationStructure, pk=self.kwargs.get("org_pk")
            )
            user_is_allowed_on_organization(self.request.user, organization)
            self._organization = organization
        return self._organization

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.get_organization())

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if "org_pk" in self.kwargs:
            context["organization"] = self.get_organization()
        return context

    def get_related_objects(self, instance):
        """Objetos, además de la organización, con los que se relaciona el cambio."""
        return []

    def get_log_related_objects(self, instance):
        related = [self.get_organization()] + list(self.get_related_objects(instance))
        return [obj for obj in related if obj is not None]

    def perform_create(self, serializer):
        serializer.save(
            organization=self.get_organization(), created_by=self.request.user
        )
        if self.should_log(serializer.instance):
            self._add_log(serializer.instance, ADDITION, [], _("Created"))

    def perform_destroy(self, instance):
        if self.should_log(instance):
            self._add_log(instance, DELETION, None, _("Deleted"))
        instance.delete(
            user=self.request.user,
            related_objects=self.get_log_related_objects(instance),
        )
