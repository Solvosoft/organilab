from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from auth_and_perms.models import Profile, Rol
from laboratory.models import Laboratory, OrganizationStructure, UserOrganization
from presentation.models import AbstractRegistry
from risk_management.models import RiskZone, Regent, Buildings


class PendingTask(AbstractRegistry):
    PENDING = 0
    IN_PROCESS = 1
    FINISHED = 2

    STATUS = (
        (PENDING, _("Pending")),
        (IN_PROCESS, _("In process")),
        (FINISHED, _("Finished")),
    )
    AREA_CHOICES = (
        ("laboratory", _("Laboratory")),
        ("organization", _("Organization")),
        ("risk_zones", _("Risk Zones")),
        ("roles", _("Roles")),
    )
    name = models.CharField(_("Name"), max_length=255)
    description = models.TextField(_("Description"))
    status = models.IntegerField(_("Status"), choices=STATUS, default=PENDING)
    profile = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Profile"),
    )
    rols = models.ManyToManyField(Rol, verbose_name=_("Roles"), blank=True)
    link = models.URLField(_("Link"), null=True, blank=True)
    is_archived = models.BooleanField(_("Is archived"), default=False)

    class Meta:
        verbose_name = _("Pending task")
        verbose_name_plural = _("Pending tasks")
        ordering = ["-creation_date"]

    def __str__(self):
        return f"{self.name}"


class PendingTaskManager(models.Model):
    content_type = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    task = models.ForeignKey(PendingTask, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Pending task manager")
        verbose_name_plural = _("Pending task managers")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def get_regents_by_laboratory(self):
        # Retorna los regentes de un laboratorio en especifico
        """
        object_id: Identificador del laboratorio
        """
        regents = Regent.objects.filter(laboratory=self.object_id)
        return regents

    def get_laboratory_reponsible_by_risk_zones(self):
        # Retorna los usuarios responsables de los laboratorios asociados a un zona de riesgo y sus edificios
        """
        object_id: Identificador de la zona de riesgo.
        risk_zone: Retorna las zonas de riesgo.
        laboratory_risk: Retorna los laboratorios asociados a la zona de riesgo.
        buildings_laboratory: Retorna los laboratorios asociados a los edificios de la zona de riesgo.
        responsibles: Retorna los responsables de los laboratorios asociados a la zona de riesgo y edificios de la zona de riesgo.
        """
        risk_zone = RiskZone.objects.filter(pk=self.object_id)
        laboratory_risk = set(risk_zone.values_list("laboratory", flat=True))
        buildings_laboratory = set(
            risk_zone.values_list("buildings__laboratories", flat=True)
        )
        responsibles = (
            Laboratory.objects.filter(
                pk__in=laboratory_risk.union(buildings_laboratory),
                responsible__isnull=False,
            )
            .distinct()
            .values_list("responsible", flat=True)
        )
        return User.objects.filter(pk__in=responsibles)

    def get_responsible_laboratory(self):
        # Retorna el responsable de un laboratorio en especifico
        """
        object_id: Identificador del laboratorio
        """
        laboratory = Laboratory.objects.filter(pk=self.object_id).first()
        if laboratory:
            return laboratory.responsible
        return None

    def get_laboratory_responsibles_by_organization(self):
        # Retorna los responsables de los laboratorios de una organización en especifico
        """
        object_id: Identificador de la organización
        """
        organization = OrganizationStructure.objects.filter(pk=self.object_id).first()
        if organization:
            laboratories = organization.get_my_laboratories
            responsibles = set(
                Laboratory.objects.filter(pk__in=laboratories).values_list(
                    "responsible", flat=True
                )
            )
            return User.objects.filter(pk__in=responsibles)
        return None

    def get_reponsible_by_building(self):
        # Retorna los responsables de un edificio en especifico
        """
        object_id: Identificador del edificio
        """
        building = Buildings.objects.filter(pk=self.object_id).first()
        if building:
            responsible = building.laboratories.filter(
                responsible__isnull=False
            ).values_list("responsible", flat=True)
            return User.objects.filter(pk__in=responsible)
        return None

    def get_users_by_role(self):
        # Retorna los usuarios que tienen un rol en especifico
        """
        object_id: Identificador del rol
        """
        profile = Profile.objects.filter(
            profilepermission__rol=self.object_id
        ).distinct()
        return User.objects.filter(profile__in=profile).distinct()

    def get_users_by_laboratory(self):
        # Retorna los usuarios que estan asociados a un laboratorio en especifico
        """
        object_id: Identificador del rol
        """

        cc = ContentType.objects.get_for_model(Laboratory)
        profiles = Profile.objects.filter(
            profilepermission__content_type=cc,
            profilepermission__object_id=self.object_id,
        )
        return User.objects.filter(profile__in=profiles).distinct()

    def get_users_by_organization(self, extra_filters={}):
        # Retorna los usuarios que estan asociados a una organización en especifico
        """
        object_id: Identificador de la organización
        extra_filters: Filtros adicionales ejemplo: {'type_in_organization__in': [UserOrganization.ADMINISTRATOR, UserOrganization.LABORATORY_MANAGER]}
        limita el tipo de usuarios como en el modulo de administración de organizaciones
        """
        users = (
            UserOrganization.objects.filter(
                organization__pk=self.object_id,
                user__isnull=False,
                status=True,
                **extra_filters,
            )
            .values_list("user", flat=True)
            .distinct()
        )

        return User.objects.filter(pk__in=users)
