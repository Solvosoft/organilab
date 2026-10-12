"""
Registros de un equipo en estante: mantenimientos, bitácora, calibraciones,
garantías y capacitaciones (``laboratory/api/shelfobject.py``, viewsets
``ShelfObject*Viewset``) y los serializers que los validan.
"""

from django.contrib.auth.models import User
from django.urls import reverse

from laboratory.models import (
    ShelfObject,
    ShelfObjectMaintenance,
    ShelfObjectLog,
    ShelfObjectCalibrate,
    ShelfObjectGuarantee,
    ShelfObjectTraining,
    ShelfObjectObservation,
    Laboratory,
)
from laboratory.tests.test_cov_api_base import CovApiBase


class RegistrosEquipoBase(CovApiBase):
    equipo_pk = 15  # Condensador con características de equipo, laboratorio 1

    def setUp(self):
        super().setUp()
        self.equipo = ShelfObject.objects.get(pk=self.equipo_pk)
        self.profile = self.user.profile

    def ruta(self, basename, pk=None, shelfobject=None, org=None, lab=None):
        kwargs = {
            "org_pk": (org or self.org).pk,
            "lab_pk": (lab or self.lab).pk,
            "shelfobject": shelfobject or self.equipo.pk,
        }
        if pk is None:
            return reverse("laboratory:%s-list" % basename, kwargs=kwargs)
        kwargs["pk"] = pk
        return reverse("laboratory:%s-detail" % basename, kwargs=kwargs)

    def base_data(self, **extra):
        data = {"organization": self.org.pk, "shelfobject": self.equipo.pk}
        data.update(extra)
        return data

    def post(self, url, data):
        return self.client.post(url, data=data, content_type="application/json")

    def put(self, url, data):
        return self.client.put(url, data=data, content_type="application/json")


class MantenimientoApiTest(RegistrosEquipoBase):
    basename = "api-shelfobject-maintenance"

    def crear(self, **extra):
        return ShelfObjectMaintenance.objects.create(
            shelfobject=self.equipo,
            maintenance_date="2030-01-10",
            provider_of_maintenance_id=1,
            validator=self.profile,
            maintenance_observation="Cambio de filtros",
            organization=self.org,
            created_by=self.user,
            **extra,
        )

    def test_crea_mantenimiento_y_deja_observacion(self):
        data = self.base_data(
            maintenance_date="10/01/2030",
            provider_of_maintenance=1,
            validator=self.profile.pk,
            maintenance_observation="Revisión anual",
        )
        response = self.post(self.ruta(self.basename), data)
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(
            ShelfObjectMaintenance.objects.filter(
                shelfobject=self.equipo, maintenance_observation="Revisión anual"
            ).exists()
        )
        self.assertTrue(
            ShelfObjectObservation.objects.filter(
                shelf_object=self.equipo, description="Revisión anual"
            ).exists()
        )

    def test_proveedor_de_otra_organizacion_se_rechaza(self):
        data = self.base_data(provider_of_maintenance=999, validator=self.profile.pk)
        response = self.post(self.ruta(self.basename), data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("provider_of_maintenance", response.json())

    def test_lista_con_acciones_por_permisos(self):
        self.crear()
        response = self.client.get(self.ruta(self.basename))
        self.assertEqual(response.status_code, 200)
        fila = response.json()["data"][0]
        self.assertEqual(fila["maintenance_observation"], "Cambio de filtros")
        self.assertEqual(
            fila["actions"],
            {"create": True, "update": True, "destroy": True, "detail": True},
        )

    def test_actualiza_mantenimiento(self):
        mantenimiento = self.crear()
        data = self.base_data(
            maintenance_date="11/01/2030",
            provider_of_maintenance=2,
            maintenance_observation="Revisado otra vez",
        )
        response = self.put(self.ruta(self.basename, pk=mantenimiento.pk), data)
        self.assertEqual(response.status_code, 200, response.content)
        mantenimiento.refresh_from_db()
        self.assertEqual(mantenimiento.provider_of_maintenance_id, 2)
        self.assertEqual(mantenimiento.maintenance_observation, "Revisado otra vez")

    def test_actualizacion_invalida(self):
        mantenimiento = self.crear()
        data = self.base_data(provider_of_maintenance=2)
        response = self.put(self.ruta(self.basename, pk=mantenimiento.pk), data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("maintenance_date", response.json())

    def test_elimina_mantenimiento(self):
        mantenimiento = self.crear()
        response = self.client.delete(self.ruta(self.basename, pk=mantenimiento.pk))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ShelfObjectMaintenance.objects.filter(pk=mantenimiento.pk).exists())

    def test_usuario_de_otra_organizacion_no_puede_eliminar(self):
        mantenimiento = self.crear()
        ajeno, _org = self.crear_usuario_ajeno()
        self.client.force_login(ajeno)
        response = self.client.delete(self.ruta(self.basename, pk=mantenimiento.pk))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(ShelfObjectMaintenance.objects.filter(pk=mantenimiento.pk).exists())


class BitacoraApiTest(RegistrosEquipoBase):
    basename = "api-shelfobject-log"

    def crear(self):
        return ShelfObjectLog.objects.create(
            shelfobject=self.equipo,
            description="Encendido",
            organization=self.org,
            created_by=self.user,
        )

    def test_crea_entrada(self):
        response = self.post(self.ruta(self.basename), self.base_data(description="Uso en práctica"))
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(ShelfObjectLog.objects.filter(description="Uso en práctica").exists())

    def test_entrada_de_otra_organizacion_se_rechaza(self):
        response = self.post(
            self.ruta(self.basename), self.base_data(description="x", organization=2)
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("organization", response.json())

    def test_lista_muestra_creador(self):
        self.crear()
        response = self.client.get(self.ruta(self.basename))
        self.assertEqual(response.status_code, 200)
        fila = response.json()["data"][0]
        self.assertEqual(fila["description"], "Encendido")
        self.assertTrue(fila["actions"]["destroy"])

    def test_actualiza_y_elimina_entrada(self):
        log = self.crear()
        response = self.put(self.ruta(self.basename, pk=log.pk), self.base_data(description="Apagado"))
        self.assertEqual(response.status_code, 200, response.content)
        log.refresh_from_db()
        self.assertEqual(log.description, "Apagado")
        response = self.client.delete(self.ruta(self.basename, pk=log.pk))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ShelfObjectLog.objects.filter(pk=log.pk).exists())

    def test_actualizacion_con_objeto_distinto_al_de_la_ruta(self):
        log = self.crear()
        response = self.put(
            self.ruta(self.basename, pk=log.pk), self.base_data(description="x", shelfobject=13)
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("shelfobject", response.json())


class CalibracionApiTest(RegistrosEquipoBase):
    basename = "api-shelfobject-calibrate"

    def crear(self):
        return ShelfObjectCalibrate.objects.create(
            shelfobject=self.equipo,
            calibrate_name="Patrón 1",
            calibration_date="2030-02-01",
            validator=self.profile,
            observation="Dentro de tolerancia",
            organization=self.org,
            created_by=self.user,
        )

    def test_crea_calibracion(self):
        data = self.base_data(
            calibrate_name="Patrón A",
            calibration_date="01/02/2030",
            validator=self.profile.pk,
            observation="Ajustada",
        )
        response = self.post(self.ruta(self.basename), data)
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(ShelfObjectCalibrate.objects.filter(calibrate_name="Patrón A").exists())

    def test_calibracion_sin_nombre(self):
        data = self.base_data(calibration_date="01/02/2030", validator=self.profile.pk)
        response = self.post(self.ruta(self.basename), data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("calibrate_name", response.json())

    def test_lista_actualiza_y_elimina(self):
        calibracion = self.crear()
        response = self.client.get(self.ruta(self.basename))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"][0]["calibrate_name"], "Patrón 1")

        data = self.base_data(calibrate_name="Patrón 2", calibration_date="02/02/2030")
        response = self.put(self.ruta(self.basename, pk=calibracion.pk), data)
        self.assertEqual(response.status_code, 200, response.content)
        calibracion.refresh_from_db()
        self.assertEqual(calibracion.calibrate_name, "Patrón 2")

        response = self.client.delete(self.ruta(self.basename, pk=calibracion.pk))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ShelfObjectCalibrate.objects.filter(pk=calibracion.pk).exists())

    def test_actualizacion_invalida(self):
        calibracion = self.crear()
        response = self.put(self.ruta(self.basename, pk=calibracion.pk), self.base_data())
        self.assertEqual(response.status_code, 400)
        self.assertIn("calibrate_name", response.json())


class GarantiaApiTest(RegistrosEquipoBase):
    basename = "api-shelfobject-guarantee"

    def crear(self):
        return ShelfObjectGuarantee.objects.create(
            shelfobject=self.equipo,
            guarantee_initial_date="2030-01-01",
            guarantee_final_date="2031-01-01",
            organization=self.org,
            created_by=self.user,
        )

    def test_crea_garantia(self):
        data = self.base_data(guarantee_initial_date="01/01/2030", guarantee_final_date="01/01/2031")
        response = self.post(self.ruta(self.basename), data)
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(ShelfObjectGuarantee.objects.filter(shelfobject=self.equipo).exists())

    def test_fecha_inicial_mayor_que_final(self):
        data = self.base_data(guarantee_initial_date="01/01/2031", guarantee_final_date="01/01/2030")
        response = self.post(self.ruta(self.basename), data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("guarantee_initial_date", response.json())

    def test_lista_actualiza_y_elimina(self):
        garantia = self.crear()
        response = self.client.get(self.ruta(self.basename))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["data"][0]["actions"]["update"])

        data = self.base_data(guarantee_initial_date="01/01/2030", guarantee_final_date="01/06/2031")
        response = self.put(self.ruta(self.basename, pk=garantia.pk), data)
        self.assertEqual(response.status_code, 200, response.content)
        garantia.refresh_from_db()
        self.assertEqual(str(garantia.guarantee_final_date), "2031-06-01")

        response = self.client.delete(self.ruta(self.basename, pk=garantia.pk))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ShelfObjectGuarantee.objects.filter(pk=garantia.pk).exists())

    def test_actualizacion_invalida(self):
        garantia = self.crear()
        response = self.put(self.ruta(self.basename, pk=garantia.pk), self.base_data())
        self.assertEqual(response.status_code, 400)
        self.assertIn("guarantee_initial_date", response.json())


class CapacitacionApiTest(RegistrosEquipoBase):
    basename = "api-shelfobject-training"

    def crear(self):
        capacitacion = ShelfObjectTraining.objects.create(
            shelfobject=self.equipo,
            training_initial_date="2030-03-01",
            training_final_date="2030-03-02",
            number_of_hours=4,
            place="Aula 1",
            organization=self.org,
            created_by=self.user,
        )
        capacitacion.intern_people_receive_training.add(self.profile)
        return capacitacion

    def datos(self, **extra):
        data = self.base_data(
            training_initial_date="01/03/2030",
            training_final_date="02/03/2030",
            number_of_hours=6,
            intern_people_receive_training=[self.profile.pk],
            place="Laboratorio",
        )
        data.update(extra)
        return data

    def test_crea_capacitacion(self):
        response = self.post(self.ruta(self.basename), self.datos())
        self.assertEqual(response.status_code, 201, response.content)
        capacitacion = ShelfObjectTraining.objects.get(place="Laboratorio")
        self.assertEqual(list(capacitacion.intern_people_receive_training.all()), [self.profile])

    def test_fecha_inicial_mayor_que_final(self):
        response = self.post(
            self.ruta(self.basename), self.datos(training_initial_date="05/03/2030")
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("training_initial_date", response.json())

    def test_lista_actualiza_y_elimina(self):
        capacitacion = self.crear()
        response = self.client.get(self.ruta(self.basename))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"][0]["place"], "Aula 1")

        response = self.put(self.ruta(self.basename, pk=capacitacion.pk), self.datos(place="Aula 2"))
        self.assertEqual(response.status_code, 200, response.content)
        capacitacion.refresh_from_db()
        self.assertEqual(capacitacion.place, "Aula 2")

        response = self.client.delete(self.ruta(self.basename, pk=capacitacion.pk))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ShelfObjectTraining.objects.filter(pk=capacitacion.pk).exists())

    def test_actualizacion_invalida(self):
        capacitacion = self.crear()
        response = self.put(self.ruta(self.basename, pk=capacitacion.pk), self.datos(number_of_hours=-1))
        self.assertEqual(response.status_code, 400)
        self.assertIn("number_of_hours", response.json())


class ValidacionRegistrosEquipoTest(RegistrosEquipoBase):
    """Validaciones de ``ValidateShelfobjectEditSerializer`` que la vista no alcanza por sí sola."""

    def validar(self, data, **context):
        from laboratory.shelfobject.serializers import ValidateShelfobjectEditSerializer

        ctx = {"org_pk": self.org.pk, "lab_pk": self.lab.pk, "shelfobject": self.equipo.pk}
        ctx.update(context)
        serializer = ValidateShelfobjectEditSerializer(data=data, context=ctx)
        serializer.is_valid()
        return serializer

    def test_datos_validos(self):
        self.assertTrue(self.validar(self.base_data()).is_valid())

    def test_objeto_de_otro_laboratorio(self):
        serializer = self.validar(self.base_data(), lab_pk=2)
        self.assertIn("shelfobject", serializer.errors)

    def test_objeto_de_otra_organizacion(self):
        ShelfObject.objects.filter(pk=self.equipo.pk).update(in_where_laboratory_id=2)
        Laboratory.objects.filter(pk=2).update(organization_id=3)
        serializer = self.validar(self.base_data(), lab_pk=2)
        self.assertIn("shelfobject", serializer.errors)
