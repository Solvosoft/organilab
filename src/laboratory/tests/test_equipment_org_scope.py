"""
Registros de equipo desde una organización que **comparte** el laboratorio.

El laboratorio 1 pertenece a la organización 1 y se comparte con la 2 mediante
``OrganizationStructureRelations``. Quien trabaja en la organización 2 tiene que poder
registrar mantenimientos, calibraciones y bitácora del equipo, y elegir los
proveedores registrados en ese laboratorio.
"""

from laboratory.models import (
    OrganizationStructure,
    ShelfObjectMaintenance,
    ShelfObjectCalibrate,
    ShelfObjectLog,
    UserOrganization,
)
from laboratory.tests.test_cov_api_equipment_records import RegistrosEquipoBase


class LaboratorioCompartidoTest(RegistrosEquipoBase):

    def setUp(self):
        super().setUp()
        self.org_compartida = OrganizationStructure.objects.get(pk=2)
        self.org_compartida.users.add(self.user)
        UserOrganization.objects.get_or_create(
            organization=self.org_compartida, user=self.user, defaults={"type_in_organization": 1}
        )
        self.dar_rol(self.user, self.org_compartida)

    def datos(self, **extra):
        data = {"organization": self.org_compartida.pk, "shelfobject": self.equipo.pk}
        data.update(extra)
        return data

    def test_mantenimiento_con_proveedor_del_laboratorio(self):
        url = self.ruta("api-shelfobject-maintenance", org=self.org_compartida)
        data = self.datos(
            maintenance_date="10/01/2030",
            provider_of_maintenance=1,  # proveedor registrado en el laboratorio 1
            validator=self.profile.pk,
            maintenance_observation="Desde la organización que comparte",
        )
        response = self.post(url, data)
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(
            ShelfObjectMaintenance.objects.filter(
                maintenance_observation="Desde la organización que comparte"
            ).exists()
        )

    def test_calibracion(self):
        url = self.ruta("api-shelfobject-calibrate", org=self.org_compartida)
        data = self.datos(
            calibrate_name="Metrología SA",
            calibration_date="10/01/2030",
            validator=self.profile.pk,
            observation="Desde la organización que comparte",
        )
        response = self.post(url, data)
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(ShelfObjectCalibrate.objects.filter(calibrate_name="Metrología SA").exists())

    def test_bitacora(self):
        url = self.ruta("api-shelfobject-log", org=self.org_compartida)
        response = self.post(url, self.datos(description="Uso compartido"))
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(ShelfObjectLog.objects.filter(description="Uso compartido").exists())

    def test_organizacion_sin_relacion_sigue_rechazada(self):
        ajeno, org_ajena = self.crear_usuario_ajeno()
        self.client.force_login(ajeno)
        url = self.ruta("api-shelfobject-log", org=org_ajena)
        data = {"organization": org_ajena.pk, "shelfobject": self.equipo.pk, "description": "x"}
        response = self.post(url, data)
        self.assertEqual(response.status_code, 403)


class PermisosPorAccionTest(RegistrosEquipoBase):
    """Los ``perms`` de los registros de equipo se aplican (antes quedaban inertes)."""

    def solo_con(self, *codenames):
        from django.contrib.auth.models import Permission
        from auth_and_perms.models import Rol

        for rol in Rol.objects.all():
            rol.permissions.clear()
        rol = Rol.objects.create(name="Solo algunos", color="#000")
        rol.permissions.add(*Permission.objects.filter(codename__in=codenames))
        self.dar_rol(self.user, self.org, rol)

    def test_sin_permiso_de_agregar_mantenimiento(self):
        self.solo_con("view_shelfobjectmaintenance")
        data = self.base_data(
            maintenance_date="10/01/2030", provider_of_maintenance=1, validator=self.profile.pk
        )
        response = self.post(self.ruta("api-shelfobject-maintenance"), data)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(ShelfObjectMaintenance.objects.exists())

    def test_con_permiso_de_ver_lista(self):
        self.solo_con("view_shelfobjectmaintenance")
        response = self.client.get(self.ruta("api-shelfobject-maintenance"))
        self.assertEqual(response.status_code, 200)

    def test_sin_permiso_de_ver_lista(self):
        self.solo_con("view_shelfobjectlog")
        response = self.client.get(self.ruta("api-shelfobject-maintenance"))
        self.assertEqual(response.status_code, 403)

    def test_lista_no_muestra_equipo_de_otro_laboratorio(self):
        from laboratory.models import Laboratory

        ShelfObjectLog.objects.create(
            shelfobject=self.equipo, description="Secreto", organization=self.org
        )
        otro_lab = Laboratory.objects.get(pk=2)
        response = self.client.get(self.ruta("api-shelfobject-log", lab=otro_lab))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], [])
