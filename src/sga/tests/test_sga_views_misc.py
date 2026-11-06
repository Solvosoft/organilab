"""Vistas de sustancias, admin, lookups y utilidades de ``sga`` que no tienen
casa propia en las otras suites: ficha en PDF, generación de etiquetas, estado
de la extracción, representación de los modelos y helpers del blueprint.
"""
import json
from types import SimpleNamespace
from unittest import mock

from django.contrib.auth.models import Permission, User
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.test import Client, RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django_celery_results.models import TaskResult
from djgentelella.models import ChunkedUpload

from auth_and_perms.models import Profile
from laboratory.models import Laboratory, Object, OrganizationStructure, UserOrganization
from sga import label_phrases
from sga.forms import SGALabelComplementsForm
from sga.gtselects import get_user_laboratories_queryset, get_user_organizations_queryset
from sga.label_blueprint import (
    _shelf_color,
    _shelfobject_capacity_ml,
    _unit_name,
    blueprint_from_displaylabel,
    blueprint_from_shelfobject,
    blueprint_from_substance,
    capacity_to_ml,
)
from sga.label_engine import LabelBlueprint
from sga.label_render import render_label
from sga.models import (
    BuilderInformation,
    Component,
    DangerIndication,
    DangerSubstance,
    DangerSubstanceCategory,
    DisplayLabel,
    HCodeCategory,
    Label,
    Pictogram,
    PrudenceAdvice,
    Provider,
    RecipientSize,
    ReviewSubstance,
    SDSTraceability,
    SecurityLeaf,
    SGAComplement,
    Substance,
    SubstanceCharacteristics,
    SubstanceLaboratory,
    SubstanceObservation,
    TemplateSGA,
    WarningWord,
)
from sga.substance_codes import build_substance_code, suggest_code, SUFFIXES
from sga.tasks import extract_sds_for_characteristics
from sga.utils import _send
from sga.views.substance.views import add_sga_complements

MINIMAL_PDF = b"%PDF-1.4\ntrailer<</Root 1 0 R>>\n%%EOF\n"


@override_settings(MEDIA_ROOT="/tmp/organilab-test-media")
class SubstanceViewsBase(TestCase):
    fixtures = ["substances.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.client.force_login(self.user)
        self.org = OrganizationStructure.objects.get(pk=1)
        self.substance = Substance.objects.get(pk=134)

    def url(self, name, **kwargs):
        return reverse(f"sga:{name}", kwargs={"org_pk": self.org.pk, **kwargs})


class SecurityLeafPdfTest(SubstanceViewsBase):
    def test_genera_pdf_de_la_ficha(self):
        SecurityLeaf.objects.create(substance=self.substance, register_number="R-1")
        response = self.client.get(self.url("security_leaf_pdf", substance=self.substance.pk))
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_sin_ficha_es_404(self):
        response = self.client.get(self.url("security_leaf_pdf", substance=self.substance.pk))
        self.assertIn("status=404", response["Location"])


class SgaComplementsViewsTest(SubstanceViewsBase):
    def test_permiso_del_elemento_concreto(self):
        """Tener permiso para crear palabras no autoriza a crear indicaciones."""
        user = User.objects.create_user("editor_palabras", "p@test.org", "x")
        user.user_permissions.add(Permission.objects.get(codename="add_warningword"))
        UserOrganization.objects.create(user=user, organization=self.org, type_in_organization=1)
        request = RequestFactory().get("/")
        request.user = User.objects.get(pk=user.pk)
        with self.assertRaises(PermissionDenied):
            add_sga_complements(request, org_pk=self.org.pk, element="danger")

    def test_palabra_de_advertencia_duplicada(self):
        WarningWord.objects.create(name="Peligro extremo", weigth=7)
        total = WarningWord.objects.count()
        response = self.client.post(self.url("add_warning_word"), {"name": "Peligro extremo", "weigth": 7})
        self.assertEqual(response.status_code, 200)
        self.assertIn("A warning word with this name and weight already exists.", response.context["form"].non_field_errors())
        self.assertEqual(WarningWord.objects.count(), total)

    def test_actualizar_consejo_de_prudencia(self):
        advice = PrudenceAdvice.objects.create(code="P998", name="Viejo")
        response = self.client.post(
            self.url("update_prudence_advice", pk=advice.pk), {"code": "P998", "name": "Nuevo"}
        )
        self.assertRedirects(response, self.url("prudence_advices"), fetch_redirect_response=False)
        advice.refresh_from_db()
        self.assertEqual(advice.name, "Nuevo")

    def test_observacion_invalida(self):
        response = self.client.post(self.url("add_observation", substance=self.substance.pk), {"description": ""})
        self.assertRedirects(response, self.url("detail_substance", pk=self.substance.pk), fetch_redirect_response=False)
        self.assertFalse(SubstanceObservation.objects.filter(substance=self.substance).exists())

    def test_observacion_de_otra_organizacion(self):
        otra = OrganizationStructure.objects.create(name="Otra")
        ajena = Substance.objects.create(comercial_name="Ajena", organization=otra)
        obs = SubstanceObservation.objects.create(substance=ajena, description="Original")
        response = self.client.post(self.url("update_observation"), {"pk": obs.pk, "description": "Cambiada"})
        self.assertEqual(response.json(), {"status": False})
        obs.refresh_from_db()
        self.assertEqual(obs.description, "Original")


class SdsUploadTest(SubstanceViewsBase):
    def test_metodo_no_permitido(self):
        response = self.client.get(self.url("upload_sds"))
        self.assertEqual(response.status_code, 405)
        self.assertFalse(response.json()["ok"])

    def test_token_directo_sin_json(self):
        upload = ChunkedUpload.objects.create(user=self.user, filename="ficha.pdf", offset=len(MINIMAL_PDF), status=2)
        upload.file.save("ficha.pdf", ContentFile(MINIMAL_PDF), save=True)
        with mock.patch("sga.views.substance.views.extract_sds_for_characteristics") as task:
            task.delay.return_value = SimpleNamespace(task_id="t-1")
            response = self.client.post(
                self.url("upload_sds_pk", pk=self.substance.pk), {"token": upload.upload_id}
            )
        self.assertEqual(response.json()["task_id"], "t-1")
        self.assertFalse(ChunkedUpload.objects.filter(pk=upload.pk).exists())
        self.assertTrue(SubstanceCharacteristics.objects.get(substance=self.substance).security_sheet)

    def test_estado_de_la_tarea(self):
        url = self.url("sds_task_status")
        self.assertEqual(self.client.get(url).json(), {"state": "PENDING", "end": False})
        TaskResult.objects.create(task_id="ok", status="SUCCESS", result=json.dumps({"ok": True}))
        TaskResult.objects.create(task_id="raro", status="SUCCESS", result="no es json")
        self.assertEqual(self.client.get(url, {"task_id": "ok"}).json()["result"], {"ok": True})
        raro = self.client.get(url, {"task_id": "raro"}).json()
        self.assertEqual((raro["end"], raro["result"]), (True, None))


class GenerateLabelTest(SubstanceViewsBase):
    def test_dimensiones_basura_usan_el_valor_por_defecto(self):
        response = self.client.get(self.url("generate_label", pk=self.substance.pk), {"ancho_mm": "abc", "alto_mm": "-3"})
        self.assertEqual(response["Content-Type"], "image/png")

    def test_tamano_del_recipiente(self):
        recipiente = RecipientSize.objects.create(name="Vial", height=1, width=1, height_unit="cm", width_unit="cm")
        response = self.client.get(self.url("generate_label", pk=self.substance.pk), {"recipient_size": recipiente.pk})
        # 10×10 mm está por debajo del mínimo: el recipiente manda sobre ancho/alto.
        self.assertEqual(response.status_code, 400)
        response = self.client.get(self.url("generate_label", pk=self.substance.pk), {"recipient_size": 99999, "formato": "svg"})
        self.assertEqual(response["Content-Type"], "image/svg+xml")


class StepZeroTest(SubstanceViewsBase):
    def test_renombra_la_sustancia(self):
        response = self.client.post(self.url("step_zero_pk", pk=self.substance.pk), {"name": "Acetona pura"})
        self.assertRedirects(response, self.url("step_one", pk=self.substance.pk), fetch_redirect_response=False)
        self.substance.refresh_from_db()
        self.assertEqual(self.substance.comercial_name, "Acetona pura")

    def test_exige_sesion_y_organizacion_propia(self):
        nombre = self.substance.comercial_name
        anonimo = Client().post(self.url("step_zero_pk", pk=self.substance.pk), {"name": "Pirata"})
        self.assertIn("login", anonimo["Location"])
        otra = OrganizationStructure.objects.create(name="Otra")
        ajena = Substance.objects.create(comercial_name="Ajena", organization=otra)
        response = self.client.post(self.url("step_zero_pk", pk=ajena.pk), {"name": "Pirata"})
        self.assertIn("status=404", response["Location"])
        self.substance.refresh_from_db()
        ajena.refresh_from_db()
        self.assertEqual((self.substance.comercial_name, ajena.comercial_name), (nombre, "Ajena"))


class AdminTest(SubstanceViewsBase):
    def test_formulario_de_indicacion_filtra_clases(self):
        response = self.client.get(reverse("admin:sga_dangerindication_add"))
        form = response.context["adminform"].form
        self.assertEqual(set(form.fields["warning_class"].queryset.values_list("danger_type", flat=True)), {"class"})
        self.assertEqual(set(form.fields["warning_category"].queryset.values_list("danger_type", flat=True)), {"category"})

    def test_trazabilidad_muestra_el_objeto(self):
        obj = Object.objects.create(name="Reactivo trazado", type=0, organization=self.org)
        con_objeto = SubstanceCharacteristics.objects.create(object_related=obj)
        SDSTraceability.objects.create(sga_substance_characteristics=con_objeto, source="manual")
        sin_objeto = SubstanceCharacteristics.objects.create(object_related=None)
        SDSTraceability.objects.create(sga_substance_characteristics=sin_objeto, source="manual")
        response = self.client.get(reverse("admin:sga_sdstraceability_changelist"))
        self.assertContains(response, "Reactivo trazado")
        self.assertRegex(response.content.decode(), r'field-get_object_name"><a [^>]*>-</a>')


class ModelStrTest(SubstanceViewsBase):
    def test_representaciones(self):
        template = TemplateSGA.objects.get(pk=2)
        display = DisplayLabel.objects.create(
            name="Etiqueta", json_representation="{}", template=template, label=Label.objects.create()
        )
        lab = Laboratory.objects.get(pk=1)
        enlace = SubstanceLaboratory(substance=self.substance, laboratory=lab)
        self.assertEqual(str(enlace), f"{self.substance.pk} - {lab.pk}")
        enlace.code = "EQ-X"
        self.assertEqual(str(enlace), "EQ-X")
        self.assertEqual(str(Component(name="Agua", cas_number="7732-18-5")), "Agua")
        self.assertEqual(str(BuilderInformation(name="ACME")), "ACME")
        self.assertEqual(str(Label(substance=self.substance)), str(self.substance))
        self.assertEqual(str(display), "Etiqueta Height 13.0cm x Width 17.0cm")
        self.assertEqual(str(Provider(name="Proveedor")), "Proveedor")
        self.assertEqual(str(SubstanceObservation(substance=self.substance, created_by=self.user)), f"{self.substance} {self.user}")
        self.assertEqual(str(HCodeCategory(danger_category="health")), "health")
        self.assertEqual(str(Pictogram(name="Llama")), "Llama")
        self.assertEqual(str(DangerSubstance(name="Benceno")), "Benceno")
        self.assertEqual(str(DangerSubstanceCategory(note="Nota")), "Nota")
        sc = SubstanceCharacteristics.objects.get(substance=self.substance)
        traza = SDSTraceability.objects.create(sga_substance_characteristics=sc, source="manual")
        self.assertTrue(str(traza).startswith(f"{sc.pk} - manual ("))

    def test_revision_sin_simbolos_extranos(self):
        review = ReviewSubstance(substance=self.substance, note=8)
        self.assertEqual(str(review), f"{self.user} - 8")

    def test_representacion_sin_nombre_no_falla(self):
        self.assertEqual(str(DangerSubstance(cas_code="71-43-2")), "")
        self.assertEqual(str(DangerSubstanceCategory()), "")


class LookupsTest(SubstanceViewsBase):
    def test_organizaciones_y_laboratorios_del_usuario(self):
        orgs = self.client.get(reverse("user_organization_loop-list")).json()["results"]
        self.assertEqual([o["id"] for o in orgs], [self.org.pk])
        labs = self.client.get(reverse("user_laboratory_loop-list"), {"org_pk": self.org.pk}).json()["results"]
        self.assertEqual([lab["id"] for lab in labs], [1])
        self.assertEqual(self.client.get(reverse("user_laboratory_loop-list")).json()["results"], [])

    def test_querysets_vacios(self):
        sin_perfil = SimpleNamespace()
        self.assertFalse(get_user_organizations_queryset(sin_perfil).exists())
        self.assertFalse(get_user_laboratories_queryset(sin_perfil, self.org.pk).exists())
        self.assertFalse(get_user_laboratories_queryset(self.user, None).exists())

    def test_formulario_de_complementos_sin_organizacion(self):
        self.assertFalse(SGALabelComplementsForm().fields["substance"].queryset.exists())
        self.assertTrue(SGALabelComplementsForm(org_pk=self.org.pk).fields["substance"].queryset.exists())


class BlueprintTest(SubstanceViewsBase):
    def test_complemento_aporta_consejos_y_palabra(self):
        complement = SGAComplement.objects.create(substance=self.substance, warningword=WarningWord.objects.get(name="Peligro"))
        complement.prudence_advice.add(PrudenceAdvice.objects.get(code="P280"))
        bp = blueprint_from_substance(self.substance)
        self.assertIn("P280", bp.consejos_prudencia)
        self.assertEqual(bp.palabra_advertencia, "PELIGRO")

    def test_desde_etiqueta_del_editor(self):
        self.substance.comercial_name = ""
        self.substance.uipa_name = ""
        self.substance.save()
        sin_org = Substance.objects.create(comercial_name="", organization=None)
        recipiente = RecipientSize.objects.create(name="Frasco", height=4, width=7, height_unit="cm", width_unit="cm")
        display = DisplayLabel.objects.create(
            name="Nombre del editor", json_representation="{}", template=TemplateSGA.objects.get(pk=2),
            recipient_size=recipiente, label=Label.objects.create(substance=sin_org),
        )
        display.logo = SimpleNamespace(path="/tmp/logo.png")
        bp = blueprint_from_displaylabel(display)
        self.assertEqual((bp.nombre, bp.ancho_mm, bp.alto_mm), ("Nombre del editor", 70.0, 40.0))
        self.assertEqual(bp.logo_der_path, "/tmp/logo.png")

        class SinRuta:
            @property
            def path(self):
                raise NotImplementedError

        display.logo = SinRuta()
        self.assertEqual(blueprint_from_displaylabel(display).logo_der_path, "")


class BlueprintHelpersTest(SimpleTestCase):
    def test_unidades_y_capacidad(self):
        self.assertEqual(_unit_name(None), "")
        self.assertIsNone(capacity_to_ml("mucho", SimpleNamespace(description="mL")))
        so = SimpleNamespace(
            object=SimpleNamespace(materialcapacity=SimpleNamespace(capacity=None, capacity_measurement_unit=None)),
            quantity=2,
            measurement_unit=SimpleNamespace(description="L"),
        )
        self.assertEqual(_shelfobject_capacity_ml(so), 2000.0)
        self.assertEqual(_shelf_color(None), "")

    def test_recipiente_contenedor(self):
        chars = SimpleNamespace(molecular_formula="", cas_id_number="", h_code=SimpleNamespace(all=lambda: []))
        so = SimpleNamespace(
            object=SimpleNamespace(
                name="Etanol", materialcapacity=None,
                substancharacteristics_object=SimpleNamespace(first=lambda: chars),
            ),
            shelf=SimpleNamespace(name="Estante 1", color="", furniture=None),
            quantity=None, measurement_unit=None, batch="", reactive_expiration_date=None,
            physical_status="", in_where_laboratory=None,
            container_id=5, container=SimpleNamespace(object=SimpleNamespace(name="Bidón azul")),
            shelf_object_url="",
        )
        self.assertEqual(blueprint_from_shelfobject(so).recipiente_nombre, "Bidón azul")


class LabelRenderTest(SimpleTestCase):
    def setUp(self):
        self.bp = LabelBlueprint(nombre="Acetona", frases_peligro="H225", ancho_mm=70, alto_mm=40, dpi=100)

    def test_svg(self):
        response = render_label(self.bp, "SVG", filename="x")
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        self.assertEqual(response["Content-Disposition"], 'inline; filename="x.svg"')
        self.assertIn(b"<svg", response.content)

    def test_pdf(self):
        response = render_label(self.bp, "pdf", filename="x")
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="x.pdf"')
        self.assertTrue(response.content.startswith(b"%PDF"))


class LabelPhrasesTest(TestCase):
    def setUp(self):
        label_phrases.invalidate()
        self.addCleanup(label_phrases.invalidate)

    def test_resuelve_desde_la_base(self):
        DangerIndication.objects.filter(code="H314").update(description="  Texto de la base  ")
        PrudenceAdvice.objects.create(code="P370 + P378", name="Combinado de la base")
        self.assertEqual(label_phrases.resolve("h314"), "Texto de la base")
        self.assertEqual(label_phrases.resolve("P370+P378"), "Combinado de la base")
        self.assertIsNone(label_phrases.resolve("H999"))
        # Queda en memoria hasta invalidar.
        DangerIndication.objects.filter(code="H314").update(description="Otro")
        self.assertEqual(label_phrases.resolve("H314"), "Texto de la base")


class TasksAndUtilsTest(SubstanceViewsBase):
    def test_extraccion_sin_caracteristicas(self):
        self.assertEqual(
            extract_sds_for_characteristics(999999),
            {"ok": False, "message": "characteristics not found", "fields": []},
        )

    def test_extraccion_que_falla_no_propaga(self):
        sc = SubstanceCharacteristics.objects.get(substance=self.substance)
        sc.security_sheet.save("ficha.pdf", ContentFile(MINIMAL_PDF), save=True)
        with mock.patch("laboratory.tasks._update_substance_from_pdf", side_effect=RuntimeError("PDF ilegible")):
            result = extract_sds_for_characteristics(sc.pk)
        self.assertEqual(result, {"ok": False, "message": "PDF ilegible", "fields": []})
        self.assertFalse(SDSTraceability.objects.filter(sga_substance_characteristics=sc).exists())

    def test_envio_de_correo_que_falla_se_registra(self):
        with mock.patch("sga.utils.send_email_from_template", side_effect=OSError("smtp caído")):
            with mock.patch("sga.utils.logger") as logger:
                _send("codigo", "a@test.org", "Asunto", "Cuerpo")
        logger.error.assert_called_once()

    def test_codigos(self):
        tomadas = ["QUI"] + [f"QU{s}" for s in SUFFIXES]
        self.assertIsNone(suggest_code("Química", taken=tomadas))
        lab = SimpleNamespace(code="")
        self.assertIsNone(build_substance_code(lab, SimpleNamespace(code="ORG"), self.substance))
