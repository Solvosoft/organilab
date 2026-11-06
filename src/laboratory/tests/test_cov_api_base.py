"""
Base común para las pruebas de cobertura de la API de objetos en estante
(``laboratory/api/*`` y ``laboratory/shelfobject/*``).

El usuario ``admin`` de ``laboratory_data.json`` recibe en la organización 1 un
rol con todos los permisos, así cada prueba se concentra en la validación y en
el aislamiento por organización/laboratorio y no en la matriz de permisos.
"""

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

from auth_and_perms.models import Rol, ProfilePermission, Profile
from laboratory.models import (
    OrganizationStructure,
    Laboratory,
    ShelfObject,
    Shelf,
    Catalog,
    UserOrganization,
)

UNIDADES = 64
MILILITROS = 63
LITROS = 62
METROS = 59
ESTADO_EXCELENTE = 158


class CovApiBase(TestCase):
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        super().setUp()
        self.user = User.objects.get(username="admin")
        self.org = OrganizationStructure.objects.get(pk=1)
        self.lab = Laboratory.objects.get(pk=1)
        self.rol_total = Rol.objects.create(name="Cobertura API total", color="#FFF")
        self.rol_total.permissions.add(*Permission.objects.all())
        self.dar_rol(self.user, self.org)
        self.client.force_login(self.user)

    def dar_rol(self, user, org, rol=None):
        profile_permission = ProfilePermission.objects.create(
            profile=user.profile,
            object_id=org.pk,
            content_type=ContentType.objects.get_for_model(OrganizationStructure),
        )
        profile_permission.rol.add(rol or self.rol_total)
        return profile_permission

    def crear_usuario_ajeno(self, username="ajeno"):
        """Usuario con todos los permisos pero en una organización sin relación con el laboratorio 1."""
        ajeno = User.objects.create_user(username=username, password="x")
        Profile.objects.create(user=ajeno)
        org_ajena = OrganizationStructure.objects.create(name="Org ajena %s" % username)
        org_ajena.users.add(ajeno)
        UserOrganization.objects.create(
            organization=org_ajena, user=ajeno, type_in_organization=1
        )
        self.dar_rol(ajeno, org_ajena)
        return ajeno, org_ajena

    def url(self, name, lab=None, org=None, **kwargs):
        kwargs.setdefault("org_pk", (org or self.org).pk)
        kwargs.setdefault("lab_pk", (lab or self.lab).pk)
        return reverse("laboratory:%s" % name, kwargs=kwargs)

    def crear_caja(
        self, shelf_id=2, cajas=3, unidades=10, quantity=2.0, unit=UNIDADES, lab=None, units_list=None
    ):
        units_list = units_list or [unidades] * cajas
        return ShelfObject.objects.create(
            shelf=Shelf.objects.get(pk=shelf_id),
            object_id=6,
            quantity=quantity,
            measurement_unit=Catalog.objects.get(pk=unit),
            in_where_laboratory=lab or self.lab,
            status=Catalog.objects.get(pk=ESTADO_EXCELENTE),
            is_box=True,
            units_per_box=unidades,
            quantity_units=[
                {"code": "b-%d" % i, "units": u, "quantity": quantity * u}
                for i, u in enumerate(units_list)
            ],
            created_by=self.user,
        )

    @staticmethod
    def fechas_futuras(dias_inicio=10, dias_fin=20):
        formato = "%Y-%m-%d %H:%M"
        return (
            (now() + relativedelta(days=dias_inicio)).strftime(formato),
            (now() + relativedelta(days=dias_fin)).strftime(formato),
        )
