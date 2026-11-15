"""
API de los registros ISO/IEC 17025 del equipo (``laboratory/equipment/api.py``):
programa, verificaciones intermedias, fallas y documentos.
"""
import datetime

from django.urls import reverse

from laboratory.models import (
    EquipmentActivityPlan,
    EquipmentDocument,
    ShelfObjectEquipmentCharacteristics as Characteristics,
    ShelfObjectFailure,
    ShelfObjectObservation,
    ShelfObjectVerification,
    Catalog,
)
from laboratory.tests.test_cov_api_equipment_records import RegistrosEquipoBase


class RegistroIsoBase(RegistrosEquipoBase):
    basename = ""

    def url(self, pk=None, action=None, org=None, lab=None, shelfobject=None):
        kwargs = {
            "org_pk": (org or self.org).pk,
            "lab_pk": (lab or self.lab).pk,
            "shelfobject": shelfobject or self.equipo.pk,
        }
        if pk is None:
            return reverse("laboratory:%s-list" % self.basename, kwargs=kwargs)
        kwargs["pk"] = pk
        name = "%s-%s" % (self.basename, action or "detail")
        return reverse("laboratory:%s" % name, kwargs=kwargs)


class ProgramaApiTest(RegistroIsoBase):
    basename = "api-equipment-plan"

    def datos(self, **extra):
        data = {
            "activity_kind": EquipmentActivityPlan.CALIBRATION,
            "interval_value": 12,
            "interval_unit": EquipmentActivityPlan.MONTHS,
            "start_date": "10/04/2027",
            "reminder_days_before": 30,
            "responsible": self.profile.pk,
            "is_active": True,
        }
        data.update(extra)
        return data

    def test_crea_lista_y_deja_observacion(self):
        response = self.post(self.url(), self.datos())
        self.assertEqual(response.status_code, 201, response.content)
        plan = EquipmentActivityPlan.objects.get(shelfobject=self.equipo)
        self.assertEqual(plan.organization, self.org)
        self.assertEqual(plan.start_date, datetime.date(2027, 4, 10))
        self.assertTrue(
            ShelfObjectObservation.objects.filter(shelf_object=self.equipo, action_taken="Program created").exists()
        )
        fila = self.client.get(self.url()).json()["data"][0]
        self.assertEqual(fila["next_due"], "10/04/2027")
        self.assertIn(fila["due_status"]["code"], ("valid", "due_soon", "expired"))

    def test_la_url_manda_sobre_el_cuerpo(self):
        otro_equipo = 13
        response = self.post(self.url(), self.datos(shelfobject=otro_equipo, organization=99))
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(EquipmentActivityPlan.objects.get().shelfobject_id, self.equipo.pk)

    def test_intervalo_cero_se_rechaza(self):
        response = self.post(self.url(), self.datos(interval_value=0))
        self.assertEqual(response.status_code, 400)

    def test_valores_para_editar_y_actualizar(self):
        self.post(self.url(), self.datos())
        plan = EquipmentActivityPlan.objects.get()
        valores = self.client.get(self.url(plan.pk, "get-values-for-update")).json()
        self.assertEqual(valores["start_date"], "10/04/2027")
        response = self.put(self.url(plan.pk), self.datos(interval_value=6))
        self.assertEqual(response.status_code, 200, response.content)
        plan.refresh_from_db()
        self.assertEqual(plan.interval_value, 6)

    def test_responsable_de_otra_organizacion_se_rechaza(self):
        ajeno, _org = self.crear_usuario_ajeno()
        response = self.post(self.url(), self.datos(responsible=ajeno.profile.pk))
        self.assertEqual(response.status_code, 400)
        self.assertIn("responsible", response.json())

    def test_otro_laboratorio_no_ve_ni_borra(self):
        self.post(self.url(), self.datos())
        plan = EquipmentActivityPlan.objects.get()
        from laboratory.models import Laboratory

        lab2 = Laboratory.objects.get(pk=2)
        self.assertEqual(self.client.delete(self.url(plan.pk, lab=lab2)).status_code, 404)
        self.assertTrue(EquipmentActivityPlan.objects.filter(pk=plan.pk).exists())


class VerificacionApiTest(RegistroIsoBase):
    basename = "api-equipment-verification"

    def test_crea_enlazada_al_programa_y_mueve_la_proxima_fecha(self):
        plan = EquipmentActivityPlan.objects.create(
            shelfobject=self.equipo, activity_kind=EquipmentActivityPlan.VERIFICATION,
            interval_value=1, organization=self.org,
        )
        data = {
            "plan": plan.pk,
            "verification_date": "01/11/2026",
            "verification_type": "Pesas patrón",
            "result": "Dentro de tolerancia",
            "conformity": "conforming",
            "responsible": self.profile.pk,
        }
        response = self.post(self.url(), data)
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(plan.next_due(), datetime.date(2026, 12, 1))
        fila = self.client.get(self.url()).json()["data"][0]
        self.assertEqual(fila["conformity"], "Conforming")

    def test_programa_de_otro_equipo_se_rechaza(self):
        ajeno = EquipmentActivityPlan.objects.create(
            shelfobject_id=13, activity_kind=EquipmentActivityPlan.VERIFICATION, interval_value=1
        )
        data = {"plan": ajeno.pk, "verification_date": "01/11/2026"}
        response = self.post(self.url(), data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("plan", response.json())

    def test_sin_permiso_de_borrar(self):
        verificacion = ShelfObjectVerification.objects.create(
            shelfobject=self.equipo, verification_date=datetime.date(2026, 11, 1)
        )
        from django.contrib.auth.models import Permission
        from auth_and_perms.models import Rol

        for rol in Rol.objects.all():
            rol.permissions.clear()
        solo_ver = Rol.objects.create(name="Solo ver", color="#000")
        solo_ver.permissions.add(*Permission.objects.filter(codename="view_shelfobjectverification"))
        self.dar_rol(self.user, self.org, solo_ver)
        self.assertEqual(self.client.delete(self.url(verificacion.pk)).status_code, 403)
        self.assertEqual(self.client.get(self.url()).status_code, 200)


class FallaApiTest(RegistroIsoBase):
    basename = "api-equipment-failure"

    def test_falla_saca_de_servicio_y_el_retorno_lo_devuelve(self):
        data = {"failure_date": "05/11/2026", "description": "No calibra", "blocked": True, "provider": 1}
        response = self.post(self.url(), data)
        self.assertEqual(response.status_code, 201, response.content)
        ficha = Characteristics.objects.get(shelfobject=self.equipo)
        self.assertEqual(ficha.equipment_status, Characteristics.OUT_OF_SERVICE)
        falla = ShelfObjectFailure.objects.get()
        data.update(return_to_service_date="10/11/2026", impact_assessment="Sin impacto")
        response = self.put(self.url(falla.pk), data)
        self.assertEqual(response.status_code, 200, response.content)
        ficha.refresh_from_db()
        self.assertEqual(ficha.equipment_status, Characteristics.IN_SERVICE)

    def test_retorno_anterior_a_la_falla(self):
        data = {"failure_date": "05/11/2026", "description": "x", "return_to_service_date": "01/11/2026"}
        response = self.post(self.url(), data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("return_to_service_date", response.json())


class DocumentoApiTest(RegistroIsoBase):
    basename = "api-equipment-document"

    def test_archivo_es_obligatorio_al_crear(self):
        tipo = Catalog.objects.get(key="equipment_document_type", description="Certificado")
        response = self.post(self.url(), {"document_type": tipo.pk, "title": "Certificado 2026"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.json())

    def test_lista_y_borra(self):
        from django.core.files.base import ContentFile

        documento = EquipmentDocument(shelfobject=self.equipo, title="Manual", organization=self.org)
        documento.file.save("manual.pdf", ContentFile(b"%PDF-1.4"), save=True)
        fila = self.client.get(self.url()).json()["data"][0]
        self.assertEqual(fila["title"], "Manual")
        self.assertTrue(fila["file"]["url"])
        self.assertEqual(self.client.delete(self.url(documento.pk)).status_code, 204)
        self.assertFalse(EquipmentDocument.objects.exists())


class PaginaDelEquipoTest(RegistroIsoBase):

    def test_renderiza_pestanas_y_estado(self):
        EquipmentActivityPlan.objects.create(
            shelfobject=self.equipo, activity_kind=EquipmentActivityPlan.CALIBRATION, interval_value=12,
            start_date=datetime.date(2020, 1, 1), organization=self.org,
        )
        url = reverse(
            "laboratory:equipment_shelfobject_detail",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": self.equipo.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        for pane in ("plan", "calibrate", "verification", "failure", "document"):
            self.assertIn('id="pane-%s"' % pane, html)
            self.assertIn('id="create_%s_modal"' % pane if pane != "calibrate" else 'id="create_calibrate_modal"', html)
        self.assertEqual(response.context["calibration_status"], EquipmentActivityPlan.EXPIRED)
        self.assertIn("bg-danger", html)


class TecnicoDeLaboratorioTest(RegistroIsoBase):
    """Con el rol canónico (roles.py), no con un rol de todos los permisos."""

    def setUp(self):
        super().setUp()
        from auth_and_perms.management.commands.update_roles import sync_roles
        from auth_and_perms.roles import ROLES
        from presentation.tests.test_platform_parameters import make_role_user

        sync_roles(["tecnico_laboratorio"])
        self.tecnico = make_role_user("tecnico", self.org, ROLES["tecnico_laboratorio"])
        self.client.force_login(self.tecnico)

    def test_abre_la_ficha_y_registra_mantenimiento(self):
        url = reverse(
            "laboratory:equipment_shelfobject_detail",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": self.equipo.pk},
        )
        self.assertEqual(self.client.get(url).status_code, 200)
        mantenimientos = reverse(
            "laboratory:api-shelfobject-maintenance-list",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "shelfobject": self.equipo.pk},
        )
        self.assertEqual(self.client.get(mantenimientos).status_code, 200)
        data = self.base_data(
            maintenance_date="10/11/2026", provider_of_maintenance=1,
            validator=self.tecnico.profile.pk, maintenance_type="cleaning",
        )
        self.assertEqual(self.post(mantenimientos, data).status_code, 201)

    def test_no_borra_calibraciones(self):
        from laboratory.models import ShelfObjectCalibrate

        calibracion = ShelfObjectCalibrate.objects.create(
            shelfobject=self.equipo, calibration_date=datetime.date(2026, 1, 1), calibrate_name="x"
        )
        url = reverse(
            "laboratory:api-shelfobject-calibrate-detail",
            kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "shelfobject": self.equipo.pk,
                    "pk": calibracion.pk},
        )
        self.assertEqual(self.client.delete(url).status_code, 403)
