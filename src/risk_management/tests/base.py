"""Escenario compartido por las pruebas de gestión de riesgo.

Una organización propia con un laboratorio, un edificio y una zona de riesgo, y
una organización ajena con lo mismo, para probar que un pk de otra organización
no se cuela por la URL. El usuario principal es superusuario (tiene todos los
permisos de modelo) **y** tiene un rol en la organización, que es lo que pide
`check_user_access_kwargs_org_lab`; `sin_permisos` está en la organización con
un rol vacío, para las respuestas 403.
"""
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from auth_and_perms.models import Profile, ProfilePermission, Rol
from laboratory.models import (
    Laboratory,
    OrganizationStructure,
    OrganizationStructureRelations,
    UserOrganization,
)
from risk_management.models import Buildings, RiskZone, ZoneType
from sga.models import DangerIndication, WarningWord


def indicacion(code, danger_type=""):
    """Indicación de peligro (código H); la crea si la base de pruebas no la trae."""
    palabra, _ = WarningWord.objects.get_or_create(name="Peligro")
    indicacion, _ = DangerIndication.objects.update_or_create(
        code=code,
        defaults={
            "description": "Indicación %s" % code,
            "warning_words": palabra,
            "danger_type": danger_type,
        },
    )
    return indicacion


def crear_usuario(username, organization, superuser=False, permisos=()):
    """Usuario con perfil, miembro de `organization` y con un rol en ella.

    El rol lleva los `permisos` ("app.codename") pedidos; sin ellos queda vacío.
    Los permisos efectivos salen del rol (`ProfileMiddleware`), no de
    `user_permissions`.
    """
    if superuser:
        user = User.objects.create_superuser(username, "%s@example.com" % username, "pass")
    else:
        user = User.objects.create_user(username=username, password="pass")
    profile = Profile.objects.create(user=user)
    UserOrganization.objects.create(
        user=user, organization=organization, type_in_organization=1, status=True
    )
    permission = ProfilePermission.objects.create(
        profile=profile,
        organization=organization,
        content_type=ContentType.objects.get_for_model(OrganizationStructure),
        object_id=organization.pk,
    )
    rol = Rol.objects.create(name="Rol de %s" % username, color="#FFF")
    for permiso in permisos:
        app_label, codename = permiso.split(".")
        rol.permissions.add(
            Permission.objects.get(content_type__app_label=app_label, codename=codename)
        )
    permission.rol.add(rol)
    return user


class RiskTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organization = OrganizationStructure.objects.create(name="Propia")
        cls.other = OrganizationStructure.objects.create(name="Ajena")
        cls.user = crear_usuario("riesgo_admin", cls.organization, superuser=True)
        cls.sin_permisos = crear_usuario("riesgo_sin_permisos", cls.organization)
        cls.lab = cls.crear_laboratorio("Laboratorio de Química", cls.organization)
        # Como en la aplicación: los formularios y gráficos ofrecen los laboratorios donde
        # el usuario tiene permiso de laboratorio (`get_laboratories_from_organization`).
        ProfilePermission.objects.create(
            profile=cls.user.profile,
            organization=cls.organization,
            content_type=ContentType.objects.get_for_model(Laboratory),
            object_id=cls.lab.pk,
        )
        cls.other_lab = cls.crear_laboratorio("Laboratorio ajeno", cls.other)
        cls.zone_type = ZoneType.objects.create(name="Zona Industrial")
        cls.building = Buildings.objects.create(
            name="Edificio A", phone="", organization=cls.organization
        )
        cls.building.laboratories.add(cls.lab)
        cls.other_building = Buildings.objects.create(
            name="Edificio ajeno", phone="", organization=cls.other
        )
        cls.other_building.laboratories.add(cls.other_lab)
        cls.zone = cls.crear_zona("Zona propia", cls.organization, cls.lab, cls.building)
        cls.other_zone = cls.crear_zona(
            "Zona ajena", cls.other, cls.other_lab, cls.other_building
        )

    @classmethod
    def crear_laboratorio(cls, name, organization):
        lab = Laboratory.objects.create(name=name, organization=organization)
        OrganizationStructureRelations.objects.create(
            organization=organization, content_object=lab
        )
        return lab

    @classmethod
    def crear_zona(cls, name, organization, lab, building):
        zone = RiskZone.objects.create(
            name=name, organization=organization, num_workers=3, zone_type=cls.zone_type
        )
        zone.laboratories.add(lab)
        zone.buildings.add(building)
        return zone

    def setUp(self):
        self.client.force_login(self.user)
