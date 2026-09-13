import json
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from djgentelella.models import ChunkedUpload

from sga.models import (
    DangerIndication,
    SDSTraceability,
    Substance,
    SubstanceCharacteristics,
)
from sga.tasks import extract_sds_for_characteristics

# Un PDF mínimo válido: pdfplumber lo abre sin errores pero no extrae texto útil,
# que es justo el camino que interesa comprobar (la ficha se guarda igual).
MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF\n"
)


def sds_file(name="ficha.pdf"):
    return SimpleUploadedFile(name, MINIMAL_PDF, content_type="application/pdf")


def extraction(fields):
    """Sustituye la lectura del PDF por un resultado controlado.

    La extracción real es heurística sobre el texto del documento y depende del
    fabricante; para fijar la política de escritura interesa el resultado, no
    cómo se obtuvo. Sin `_text` no se recorren los catálogos.
    """
    data = {"_lang": "es"}
    data.update(fields)
    return mock.patch(
        "laboratory.utils_pdf.extract_msds_data", return_value=data
    )


def chunked_token(user, name="ficha.pdf", payload=MINIMAL_PDF):
    """Simula una subida completada por el widget de gentelella.

    El widget sube el PDF por trozos a su propio endpoint y deja en el POST este
    token JSON; es el camino real desde el asistente.
    """
    upload = ChunkedUpload.objects.create(
        user=user, filename=name, offset=len(payload), status=2
    )
    upload.file.save(name, ContentFile(payload), save=True)
    return json.dumps({"token": str(upload.upload_id)})


@override_settings(MEDIA_ROOT="/tmp/organilab-test-media")
class SDSExtractionTest(TestCase):
    fixtures = ["substances.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.client.force_login(self.user)
        self.org_pk = 1
        self.substance = Substance.objects.get(pk=134)
        self.characteristics = SubstanceCharacteristics.objects.get(
            substance=self.substance
        )

    def _attach_sheet(self):
        self.characteristics.security_sheet = sds_file()
        self.characteristics.save(update_fields=["security_sheet"])

    def test_task_creates_traceability(self):
        self._attach_sheet()
        result = extract_sds_for_characteristics(
            self.characteristics.pk, user_pk=self.user.pk
        )

        traces = SDSTraceability.objects.filter(
            sga_substance_characteristics=self.characteristics
        )
        self.assertEqual(traces.count(), 1)
        self.assertEqual(traces.first().source, "manual")
        self.assertEqual(traces.first().created_by, self.user)
        self.assertIn("ok", result)

    def test_task_appends_history_instead_of_overwriting(self):
        """Resubir una ficha añade una traza, no pisa la anterior."""
        self._attach_sheet()
        extract_sds_for_characteristics(self.characteristics.pk, user_pk=self.user.pk)
        self._attach_sheet()
        extract_sds_for_characteristics(self.characteristics.pk, user_pk=self.user.pk)

        self.assertEqual(
            SDSTraceability.objects.filter(
                sga_substance_characteristics=self.characteristics
            ).count(),
            2,
        )

    def test_task_without_sheet_does_not_create_traceability(self):
        result = extract_sds_for_characteristics(self.characteristics.pk)
        self.assertFalse(result["ok"])
        self.assertEqual(SDSTraceability.objects.count(), 0)

    def test_unreadable_pdf_keeps_the_uploaded_sheet(self):
        """Si la extracción falla, la ficha subida no se pierde."""
        self.characteristics.security_sheet = SimpleUploadedFile(
            "roto.pdf", b"esto no es un pdf", content_type="application/pdf"
        )
        self.characteristics.save(update_fields=["security_sheet"])

        result = extract_sds_for_characteristics(self.characteristics.pk)

        self.assertFalse(result["ok"])
        self.characteristics.refresh_from_db()
        self.assertTrue(self.characteristics.security_sheet)

    def test_upload_endpoint_attaches_sheet_and_enqueues(self):
        response = self.client.post(
            reverse(
                "sga:upload_sds_pk", kwargs={"org_pk": self.org_pk, "pk": 134}
            ),
            data={"security_sheet": chunked_token(self.user)},
        )
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["substance_pk"], 134)
        self.assertIn("task_id", payload)

        self.characteristics.refresh_from_db()
        self.assertTrue(self.characteristics.security_sheet)

    def test_upload_endpoint_creates_substance_when_absent(self):
        """Subir la ficha sin sustancia previa la crea: es el nuevo punto de alta."""
        count = Substance.objects.count()
        response = self.client.post(
            reverse("sga:upload_sds", kwargs={"org_pk": self.org_pk}),
            data={"security_sheet": chunked_token(self.user)},
        )
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(Substance.objects.count(), count + 1)

        created = Substance.objects.get(pk=payload["substance_pk"])
        self.assertEqual(created.organization_id, self.org_pk)
        self.assertTrue(
            SubstanceCharacteristics.objects.get(substance=created).security_sheet
        )

    def test_upload_endpoint_requires_a_file(self):
        response = self.client.post(
            reverse("sga:upload_sds", kwargs={"org_pk": self.org_pk}), data={}
        )
        self.assertEqual(response.status_code, 400)

    def test_upload_endpoint_rejects_foreign_substance(self):
        from laboratory.models import OrganizationStructure

        other_org = OrganizationStructure.objects.create(name="Ajena")
        foreign = Substance.objects.create(
            created_by=self.user, organization=other_org, comercial_name="ajena"
        )
        # HandleErrorMiddleware convierte 403/404 en redirección para navegación
        # normal; este endpoint se consume por AJAX, que es como lo llama el JS.
        response = self.client.post(
            reverse(
                "sga:upload_sds_pk",
                kwargs={"org_pk": self.org_pk, "pk": foreign.pk},
            ),
            data={"security_sheet": chunked_token(self.user)},
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 404)

    def test_extracted_cas_is_stored(self):
        """El CAS se extraía del PDF y se descartaba: nunca llegaba a guardarse."""
        self._attach_sheet()
        self.characteristics.cas_id_number = ""
        self.characteristics.save(update_fields=["cas_id_number"])

        with extraction({"cas_id_number": "7681-52-9"}):
            extract_sds_for_characteristics(self.characteristics.pk)

        self.characteristics.refresh_from_db()
        self.assertEqual(self.characteristics.cas_id_number, "7681-52-9")

    def test_task_status_endpoint_reports_state(self):
        response = self.client.get(
            reverse("sga:sds_task_status", kwargs={"org_pk": self.org_pk}),
            data={"task_id": "no-existe"},
        )
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(payload["state"], "PENDING")
        self.assertFalse(payload["end"])


@override_settings(MEDIA_ROOT="/tmp/organilab-test-media")
class SDSExtractionWritePolicyTest(TestCase):
    """Qué puede y qué no puede pisar la extracción.

    El asistente la usa como propuesta —solo rellena huecos— mientras que el
    proceso masivo `update_sds_and_extract_data` sí reemplaza a propósito. La
    excepción son los booleanos que el extractor no sabe negar.
    """

    fixtures = ["substances.json"]

    def setUp(self):
        self.characteristics = SubstanceCharacteristics.objects.get(
            substance=Substance.objects.get(pk=134)
        )
        self.characteristics.security_sheet = sds_file()
        self.characteristics.save(update_fields=["security_sheet"])

    def update(self, fields, **kwargs):
        from laboratory.tasks import _update_substance_from_pdf

        with extraction(fields):
            return _update_substance_from_pdf(self.characteristics, **kwargs)

    def test_wizard_does_not_overwrite_what_is_already_there(self):
        self.characteristics.molecular_formula = "NaCl"
        self.characteristics.cas_id_number = "7647-14-5"
        self.characteristics.save()

        self.update(
            {"molecular_formula": "H2O", "cas_id_number": "7732-18-5"},
            overwrite=False,
        )

        self.characteristics.refresh_from_db()
        self.assertEqual(self.characteristics.molecular_formula, "NaCl")
        self.assertEqual(self.characteristics.cas_id_number, "7647-14-5")

    def test_wizard_fills_empty_fields(self):
        self.characteristics.molecular_formula = ""
        self.characteristics.save(update_fields=["molecular_formula"])

        self.update({"molecular_formula": "H2O"}, overwrite=False)

        self.characteristics.refresh_from_db()
        self.assertEqual(self.characteristics.molecular_formula, "H2O")

    def test_wizard_keeps_existing_h_codes(self):
        codes = list(DangerIndication.objects.all()[:2])
        if len(codes) < 2:
            self.skipTest("la fixture no trae suficientes códigos H")
        self.characteristics.h_code.set(codes[:1])

        self.update({"h_codes": [codes[1].code]}, overwrite=False)

        self.assertEqual(list(self.characteristics.h_code.all()), codes[:1])

    def test_bulk_replaces_h_codes(self):
        """El proceso masivo sí reemplaza: es lo que documenta y lo que busca."""
        codes = list(DangerIndication.objects.all()[:2])
        if len(codes) < 2:
            self.skipTest("la fixture no trae suficientes códigos H")
        self.characteristics.h_code.set(codes[:1])

        self.update({"h_codes": [codes[1].code]}, overwrite=True)

        self.assertEqual(list(self.characteristics.h_code.all()), codes[1:2])

    def test_extraction_never_unmarks_a_precursor(self):
        """`_extract_precursor` devuelve False también cuando no encuentra nada.

        Escribir ese False borraba una marca puesta a mano, y el reporte
        regulatorio de precursores se alimenta justo de ese campo.
        """
        self.characteristics.is_precursor = True
        self.characteristics.seveso_list = True
        self.characteristics.save()

        self.update({"is_precursor": False, "seveso_list": False}, overwrite=True)

        self.characteristics.refresh_from_db()
        self.assertTrue(self.characteristics.is_precursor)
        self.assertTrue(self.characteristics.seveso_list)

    def test_extraction_can_still_mark_a_precursor(self):
        self.characteristics.is_precursor = False
        self.characteristics.save(update_fields=["is_precursor"])

        self.update({"is_precursor": True}, overwrite=False)

        self.characteristics.refresh_from_db()
        self.assertTrue(self.characteristics.is_precursor)

    def test_bulk_never_overwrites_the_cas(self):
        """El CAS es la llave con la que el masivo busca la ficha."""
        self.characteristics.cas_id_number = "7647-14-5"
        self.characteristics.save(update_fields=["cas_id_number"])

        self.update({"cas_id_number": "7732-18-5"}, overwrite=True)

        self.characteristics.refresh_from_db()
        self.assertEqual(self.characteristics.cas_id_number, "7647-14-5")
