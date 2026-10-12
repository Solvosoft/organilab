from datetime import timedelta

from django.contrib.auth.models import User, Permission
from django.test import TestCase
from django.utils import timezone

from laboratory.models import (
    Catalog,
    BaseUnitValues,
    Laboratory,
    Object,
    OrganizationStructure,
    Shelf,
    ShelfObject,
)
from reservations_management.models import Reservations, ReservedProducts, BORROWED


class ReservationsBaseTest(TestCase):
    """Base común: la organización 1 del fixture, su laboratorio 1 y el estante 1.

    Los productos y objetos se crean sobre un `Object` distinto de los que usa el
    fixture (13 y 75), así las reservas viejas del fixture no se cruzan con los
    cálculos de disponibilidad de cada prueba.
    """

    fixtures = ["object.json", "reservations.json"]
    permisos = [
        "view_reservations",
        "change_reservations",
        "change_reservedproducts",
        "change_shelfobject",
    ]

    def setUp(self):
        self.user = User.objects.get(pk=1)
        for codename in self.permisos:
            self.user.user_permissions.add(Permission.objects.get(codename=codename))
        self.org = OrganizationStructure.objects.get(pk=1)
        self.otra_org = OrganizationStructure.objects.create(name="Organización ajena")
        self.lab = Laboratory.objects.get(pk=1)
        self.shelf = Shelf.objects.get(pk=1)
        self.unidad = Catalog.objects.get(pk=64)
        self.objeto = Object.objects.exclude(pk__in=[13, 75]).first()
        self.reservacion = Reservations.objects.create(user=self.user, status=0)
        self.ahora = timezone.now()
        self.client.force_login(self.user)

    def crear_objeto_estante(self, quantity=100, **kwargs):
        datos = dict(
            shelf=self.shelf,
            object=self.objeto,
            quantity=quantity,
            limit_quantity=0,
            measurement_unit=self.unidad,
            in_where_laboratory=self.lab,
        )
        datos.update(kwargs)
        return ShelfObject.objects.create(**datos)

    def crear_caja(self, cajas=None, **kwargs):
        if cajas is None:
            cajas = [("b-1", 10), ("b-2", 10)]
        return self.crear_objeto_estante(
            quantity=1,
            is_box=True,
            units_per_box=10,
            quantity_units=[
                {"code": code, "units": units, "quantity": units} for code, units in cajas
            ],
            **kwargs
        )

    def crear_producto(self, shelf_object, amount=10, inicio=1, fin=5, status=BORROWED, **kwargs):
        datos = dict(
            organization=self.org,
            shelf_object=shelf_object,
            user=self.user,
            reservation=self.reservacion,
            amount_required=amount,
            initial_date=self.ahora + timedelta(days=inicio),
            final_date=self.ahora + timedelta(days=fin),
            status=status,
            laboratory=self.lab,
        )
        datos.update(kwargs)
        return ReservedProducts.objects.create(**datos)

    def usar_unidad_en_estante(self):
        """El estante declara unidad de medida y existe su valor base, para que la
        conversión entre la unidad del estante y la del objeto sea la identidad."""
        BaseUnitValues.objects.get_or_create(
            measurement_unit=self.unidad, defaults={"si_value": 1}
        )
        self.shelf.measurement_unit = self.unidad
        self.shelf.save()
