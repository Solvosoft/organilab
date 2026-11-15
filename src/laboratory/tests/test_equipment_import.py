"""
Importación de equipos desde Excel (``laboratory/equipment/import_views.py``): subir,
revisar y crear o actualizar. Los libros son los de ``test_equipment_importer_parser``.
"""
import datetime
import json

from django.contrib.auth.models import Permission
from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils.timezone import now
from djgentelella.models import ChunkedUpload

from auth_and_perms.models import Rol
from laboratory.models import (
    EquipmentActivityPlan as Plan,
    Shelf,
    ShelfObjectCalibrate,
    ShelfObjectEquipmentCharacteristics as Characteristics,
    ShelfObjectMaintenance,
    TemporalUploadEquipment,
)
from laboratory.tests.test_cov_api_base import CovApiBase
from laboratory.tests.test_equipment_importer_parser import as_file, inventory_workbook, program_workbook


class ImportacionBase(CovApiBase):

    def setUp(self):
        super().setUp()
        self.shelf = Shelf.objects.filter(furniture__labroom__laboratory=self.lab).first()
        self.user.first_name, self.user.last_name = "Xindy", "Víquez Rojas"
        self.user.save()
        self.url_import = reverse("laboratory:equipment_import", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})

    def subir(self, workbook, nombre="equipos.xlsx"):
        contenido = as_file(workbook).getvalue()
        upload = ChunkedUpload.objects.create(
            file=ContentFile(contenido, name=nombre), filename=nombre, offset=len(contenido),
            completed_on=now(), user=self.user,
        )
        return json.dumps({"token": str(upload.upload_id)})

    def cargar(self, workbook, kind, nombre="equipos.xlsx"):
        return self.client.post(self.url_import, {
            "import-file": self.subir(workbook, nombre), "import-kind": kind, "import-sheet": "",
            "import-shelf": self.shelf.pk,
        })

    def datos_de_revision(self, response, cambios=None):
        """El POST que haría el navegador sin tocar nada (más ``cambios`` por fila)."""
        formset = response.context["formset"]
        data = {key: value for key, value in formset.management_form.initial.items()}
        data = {"form-%s" % key: value for key, value in data.items()}
        for index, form in enumerate(formset):
            for name, field in form.fields.items():
                value = (cambios or {}).get(index, {}).get(name, form[name].value())
                if value in (None, False, ""):
                    continue
                if isinstance(value, datetime.date):
                    value = value.strftime("%d/%m/%Y")
                if hasattr(value, "pk"):
                    value = value.pk
                data["%s-%s" % (form.prefix, name)] = "on" if value is True else value
        return data

    def importar(self, workbook, kind, cambios=None):
        response = self.cargar(workbook, kind)
        self.assertEqual(response.status_code, 302, getattr(response, "context", None) and response.context["form"].errors)
        review = self.client.get(response["Location"])
        self.assertEqual(review.status_code, 200)
        return self.client.post(response["Location"], self.datos_de_revision(review, cambios)), review


class InventarioTest(ImportacionBase):

    def test_crea_equipos_con_su_ficha(self):
        response, review = self.importar(inventory_workbook(), "inventory")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(TemporalUploadEquipment.objects.exists())
        agitador = Characteristics.objects.get(internal_code="LB-002", shelfobject__in_where_laboratory=self.lab)
        self.assertEqual(agitador.brand, "Corning")
        self.assertEqual(agitador.model, "PC-420D")
        self.assertEqual(agitador.physical_location, "Mesa de trabajo")
        self.assertEqual(agitador.shelfobject.shelf, self.shelf)
        self.assertEqual(agitador.shelfobject.object.type, "2")
        self.assertEqual(agitador.custodian, self.user.profile)  # «XVR» -> Xindy Víquez Rojas
        balanza = Characteristics.objects.get(internal_code="LB-010")
        self.assertEqual(balanza.equipment_status, Characteristics.DECOMMISSIONED)
        self.assertTrue(balanza.shelfobject.marked_as_discard)

    def test_reimportar_actualiza_sin_duplicar_ni_borrar(self):
        self.importar(inventory_workbook(), "inventory")
        Characteristics.objects.filter(internal_code="LB-002").update(serial_number="S-MANUAL")
        libro = inventory_workbook()
        libro.active["B2"] = "Corning Inc."
        self.importar(libro, "inventory")
        self.assertEqual(Characteristics.objects.filter(internal_code="LB-002").count(), 1)
        agitador = Characteristics.objects.get(internal_code="LB-002")
        self.assertEqual(agitador.brand, "Corning Inc.")
        self.assertEqual(agitador.serial_number, "S-MANUAL")  # la celda vacía no lo borra

    def test_filas_desmarcadas_no_se_importan(self):
        self.importar(inventory_workbook(), "inventory", cambios={1: {"include": False}})
        self.assertFalse(Characteristics.objects.filter(internal_code="LB-007").exists())
        self.assertTrue(Characteristics.objects.filter(internal_code="LB-002").exists())


class ConflictoDeCodigoTest(ImportacionBase):

    def test_avisa_si_el_codigo_es_de_otro_equipo(self):
        libro = program_workbook()
        self.importar(inventory_workbook(), "inventory")  # LB-002 es un «Agitador»
        libro.active["B13"] = "LB-002"  # en el programa, LB-002 sería la balanza
        response = self.cargar(libro, "program")
        review = self.client.get(response["Location"])
        balanza = review.context["formset"].forms[0]
        self.assertEqual(balanza.existing_name, "Agitador")
        self.assertContains(review, "Agitador")
        self.assertEqual(review.context["formset"].forms[1].existing_name, "")


class ProgramaTest(ImportacionBase):

    def test_calibracion_y_programas(self):
        response, _review = self.importar(program_workbook(), "program")
        self.assertEqual(response.status_code, 302)
        balanza = Characteristics.objects.get(internal_code="LB-123")
        self.assertEqual(balanza.magnitude.description, "Masa")
        self.assertEqual(balanza.resolution, "0.01")
        calibracion = ShelfObjectCalibrate.objects.get(shelfobject=balanza.shelfobject)
        self.assertEqual(calibracion.calibration_date, datetime.date(2026, 4, 10))
        self.assertEqual(calibracion.next_calibration_date, datetime.date(2027, 4, 10))
        self.assertEqual(calibracion.conformity, "conforming")
        plan = Plan.objects.get(shelfobject=balanza.shelfobject, activity_kind=Plan.CALIBRATION)
        self.assertEqual(plan.interval_value, 12)
        self.assertEqual(plan.next_due(), datetime.date(2027, 4, 10))
        mantenimiento = Plan.objects.get(shelfobject=balanza.shelfobject, activity_kind=Plan.PREVENTIVE_MAINTENANCE)
        self.assertEqual(mantenimiento.start_date, datetime.date(2026, 12, 31))
        self.assertIn("Inspección visual", mantenimiento.notes)
        # Sin fecha de ejecución en la revisión: solo el programa.
        self.assertFalse(ShelfObjectMaintenance.objects.filter(shelfobject=balanza.shelfobject).exists())

    def test_fecha_de_ejecucion_crea_el_mantenimiento(self):
        self.importar(program_workbook(), "program", cambios={0: {"maintenance_date": datetime.date(2026, 3, 2)}})
        balanza = Characteristics.objects.get(internal_code="LB-123")
        mantenimiento = ShelfObjectMaintenance.objects.get(shelfobject=balanza.shelfobject)
        self.assertEqual(mantenimiento.maintenance_date, datetime.date(2026, 3, 2))
        self.assertEqual(mantenimiento.maintenance_type, "preventive")
        self.assertEqual(
            sorted(mantenimiento.activities.values_list("description", flat=True)), ["Inspección visual", "Limpieza"]
        )

    def test_fecha_de_ejecucion_sin_mantenimiento_en_el_excel(self):
        response, _review = self.importar(
            program_workbook(), "program", cambios={1: {"maintenance_date": datetime.date(2026, 3, 2)}}
        )
        self.assertEqual(response.status_code, 200)  # la revisión vuelve con el error
        self.assertTrue(response.context["formset"].forms[1].errors["maintenance_date"])
        self.assertFalse(Characteristics.objects.filter(internal_code="LB-123").exists())


class CargaTest(ImportacionBase):

    def test_formato_equivocado(self):
        response = self.cargar(inventory_workbook(), "program")
        self.assertEqual(response.status_code, 200)
        self.assertIn("file", response.context["form"].errors)

    def test_extension_no_permitida(self):
        response = self.cargar(inventory_workbook(), "inventory", nombre="equipos.csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn("file", response.context["form"].errors)

    def test_estante_de_otro_laboratorio(self):
        from laboratory.models import Catalog, Furniture, Laboratory, LaboratoryRoom

        sala = LaboratoryRoom.objects.create(laboratory=Laboratory.objects.get(pk=2), name="Sala ajena")
        mueble = Furniture.objects.create(labroom=sala, name="Mueble", type=Catalog.objects.filter(key="furniture_type").first())
        otro = Shelf.objects.create(furniture=mueble, name="Ajeno", type=Catalog.objects.filter(key="container_type").first())
        response = self.client.post(self.url_import, {
            "import-file": self.subir(inventory_workbook()), "import-kind": "inventory", "import-shelf": otro.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("shelf", response.context["form"].errors)

    def test_revision_de_otro_laboratorio(self):
        response = self.cargar(inventory_workbook(), "inventory")
        temp = TemporalUploadEquipment.objects.get()
        url = reverse("laboratory:equipment_import_review", kwargs={"org_pk": self.org.pk, "lab_pk": 2, "key": temp.key})
        self.assertEqual(self.client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest").status_code, 404)
        self.assertEqual(response.status_code, 302)

    def test_plantilla(self):
        url = reverse("laboratory:equipment_import_template", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        from laboratory.equipment import importer

        _title, rows = importer.read_workbook(as_file_bytes(response.content), importer.INVENTORY)
        self.assertEqual(rows[0]["internal_code"], "LB-127")

    def test_sin_permiso_de_agregar_objetos(self):
        for rol in Rol.objects.all():
            rol.permissions.clear()
        solo = Rol.objects.create(name="Solo estantes", color="#000")
        solo.permissions.add(*Permission.objects.filter(codename="add_shelfobject"))
        self.dar_rol(self.user, self.org, solo)
        response = self.client.get(self.url_import, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 403)


def as_file_bytes(content):
    import io

    return io.BytesIO(content)


class TecnicoImportaYExportaTest(ImportacionBase):
    """Con el rol canónico Técnico de laboratorio (roles.py)."""

    def setUp(self):
        super().setUp()
        from auth_and_perms.management.commands.update_roles import sync_roles
        from auth_and_perms.roles import ROLES
        from presentation.tests.test_platform_parameters import make_role_user

        sync_roles(["tecnico_laboratorio"])
        self.tecnico = make_role_user("tecnico", self.org, ROLES["tecnico_laboratorio"])
        self.client.force_login(self.tecnico)

    def test_importa_el_inventario(self):
        self.assertEqual(self.client.get(self.url_import).status_code, 200)
        plantilla = reverse("laboratory:equipment_import_template", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(self.client.get(plantilla).status_code, 200)
        response, _review = self.importar(inventory_workbook(), "inventory")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Characteristics.objects.filter(internal_code="LB-002").exists())

    def test_exporta_programa_y_hoja_de_vida(self):
        self.importar(inventory_workbook(), "inventory")
        equipo = Characteristics.objects.get(internal_code="LB-002").shelfobject
        programa = reverse("laboratory:equipment_program_export", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(self.client.get(programa).status_code, 200)
        hoja = reverse("laboratory:equipment_life_record_pdf",
                       kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": equipo.pk})
        self.assertEqual(self.client.get(hoja).status_code, 200)
