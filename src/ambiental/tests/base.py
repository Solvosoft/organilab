from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from ambiental.ambiental_defaults import (
    KEY_POINT_TYPE,
    KEY_RESOURCE_TYPE,
    RESOURCE_ELECTRICITY,
    RESOURCE_WATER,
)
from ambiental.models import MeasurementPoint
from auth_and_perms.management.commands.update_roles import update_ambiental_roles
from auth_and_perms.models import Profile, ProfilePermission, Rol
from laboratory.models import (
    Catalog,
    Laboratory,
    OrganizationStructure,
    OrganizationStructureRelations,
    UserOrganization,
)
from risk_management.models import Buildings


class AmbientalTestCase(TestCase):
    """Base de las pruebas del módulo: una organización con un usuario **con rol**.

    Las pruebas no usan superusuario a propósito: `ProfileMiddleware` se salta a los
    superusuarios, así que una prueba que corre con uno no prueba ningún permiso. Los
    permisos del rol salen de `update_ambiental_roles()`, la misma función que usa
    `update_roles` en producción.
    """

    rol_name = "Administrador ambiental"

    @classmethod
    def setUpTestData(cls):
        update_ambiental_roles()
        cls.organization = OrganizationStructure.objects.create(name="Universidad")
        cls.other_organization = OrganizationStructure.objects.create(name="Otra")
        cls.user = cls.make_user("ambiental", cls.organization, cls.rol_name)
        cls.laboratory = Laboratory.objects.create(
            name="Laboratorio de Química", organization=cls.organization
        )
        OrganizationStructureRelations.objects.create(
            organization=cls.organization, content_object=cls.laboratory
        )
        cls.building = Buildings.objects.create(
            name="Edificio A", phone="", organization=cls.organization, area=1200
        )
        cls.building.laboratories.add(cls.laboratory)
        cls.other_building = Buildings.objects.create(
            name="Edificio ajeno", phone="", organization=cls.other_organization
        )
        cls.water = Catalog.objects.get(key=KEY_RESOURCE_TYPE, description=RESOURCE_WATER)
        cls.electricity = Catalog.objects.get(
            key=KEY_RESOURCE_TYPE, description=RESOURCE_ELECTRICITY
        )
        cls.meter = Catalog.objects.get(key=KEY_POINT_TYPE, description="Medidor")

    @classmethod
    def make_user(cls, username, organization, rol_name):
        user = User.objects.create_user(username=username, password="pass")
        profile = Profile.objects.create(user=user)
        UserOrganization.objects.create(
            user=user, organization=organization, type_in_organization=3, status=True
        )
        permission = ProfilePermission.objects.create(
            profile=profile,
            organization=organization,
            content_type=ContentType.objects.get_for_model(OrganizationStructure),
            object_id=organization.pk,
        )
        permission.rol.add(Rol.objects.get(name=rol_name))
        return user

    def setUp(self):
        self.client.force_login(self.user)

    def make_point(self, organization=None, building=None, **kwargs):
        defaults = dict(
            organization=organization or self.organization,
            building=building or self.building,
            code="MED-001",
            name="Medidor principal",
            point_type=self.meter,
            resource_type=self.water,
            created_by=self.user,
        )
        defaults.update(kwargs)
        return MeasurementPoint.objects.create(**defaults)
