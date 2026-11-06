"""Vistas del editor de etiquetas SGA (``sga/views/editor.py``).

Cubre plantillas, etiquetas personales, recipientes y empresas: respuestas,
datos que guardan y el aislamiento por organización (403 con una ajena).
"""
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from laboratory.models import OrganizationStructure
from sga.models import (
    BuilderInformation,
    DangerIndication,
    DisplayLabel,
    Label,
    PrudenceAdvice,
    RecipientSize,
    SGAComplement,
    Substance,
    TemplateSGA,
    WarningWord,
)


@override_settings(MEDIA_ROOT="/tmp/organilab-test-media")
class EditorViewsBase(TestCase):
    fixtures = ["substances.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.client.force_login(self.user)
        self.org = OrganizationStructure.objects.get(pk=1)
        self.foreign = OrganizationStructure.objects.create(name="Organización ajena")
        self.substance = Substance.objects.get(pk=134)
        self.template = TemplateSGA.objects.get(pk=2)
        self.recipient = RecipientSize.objects.get(pk=1)

    def url(self, name, org=None, **kwargs):
        return reverse(f"sga:{name}", kwargs={"org_pk": (org or self.org).pk, **kwargs})

    def make_label(self, recipient=None, substance=None, builder=None, **extra):
        label = Label.objects.create(substance=substance, builderInformation=builder)
        return DisplayLabel.objects.create(
            name=extra.pop("name", "Etiqueta de prueba"),
            json_representation="{}",
            template=self.template,
            recipient_size=recipient or self.recipient,
            label=label,
            organization=self.org,
            created_by=extra.pop("created_by", self.user),
            **extra,
        )

    def make_company(self, **extra):
        data = {
            "name": "ACME",
            "phone": "2222-2222",
            "address": "San José",
            "commercial_information": "Distribuidor",
            "user": self.user,
            "organization": self.org,
        }
        data.update(extra)
        return BuilderInformation.objects.create(**data)

    def assertForbidden(self, response):
        """Las páginas HTML convierten el 403 en una redirección a la vista de error."""
        if response.status_code == 302:
            self.assertIn("status=403", response["Location"])
        else:
            self.assertEqual(response.status_code, 403)

    def messages_of(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]


class TemplateEditorTest(EditorViewsBase):
    def test_abre_una_plantilla_existente(self):
        response = self.client.get(self.url("editor"), {"instance": self.template.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["instance"], self.template)
        self.assertTrue(response.context["clean_canvas_editor"])

    def test_guarda_plantilla_en_la_organizacion(self):
        response = self.client.post(
            self.url("editor"),
            {
                "name": "Plantilla nueva",
                "recipient_size": self.recipient.pk,
                "json_representation": "{}",
                "preview": "data:image/png;base64,",
                "community_share": False,
            },
        )
        self.assertRedirects(response, self.url("editor"), fetch_redirect_response=False)
        plantilla = TemplateSGA.objects.get(name="Plantilla nueva")
        self.assertEqual((plantilla.organization, plantilla.created_by), (self.org, self.user))

    def test_plantilla_invalida_conserva_el_lienzo(self):
        response = self.client.post(self.url("editor"), {"name": ""})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["clean_canvas_editor"])
        self.assertIn("name", response.context["generalform"].errors)

    def test_organizacion_ajena(self):
        self.assertForbidden(self.client.get(self.url("editor", org=self.foreign)))


class PersonalTemplateTest(EditorViewsBase):
    def test_editar_muestra_datos_de_la_empresa(self):
        company = self.make_company()
        display = self.make_label(substance=self.substance, builder=company)
        response = self.client.get(self.url("edit_personal", pk=display.pk))
        self.assertEqual(response.status_code, 200)
        initial = response.context["generalform"].initial
        self.assertEqual(initial["company_name"], "ACME")
        self.assertEqual(initial["substance"], self.substance)

    def test_editar_guarda_etiqueta_empresa_y_sustancia(self):
        company = self.make_company()
        display = self.make_label(substance=self.substance, builder=company)
        response = self.client.post(
            self.url("edit_personal", pk=display.pk),
            {
                "name": "Renombrada",
                "json_representation": "{}",
                "preview": "x",
                "recipient_size": self.recipient.pk,
                "substance": self.substance.pk,
                "address": "Heredia",
                "phone": "8888-8888",
                "commercial_information": "Otro",
            },
        )
        self.assertRedirects(response, self.url("add_personal"), fetch_redirect_response=False)
        display.refresh_from_db()
        company.refresh_from_db()
        self.assertEqual(display.name, "Renombrada")
        self.assertEqual(company.address, "Heredia")

    def test_editar_invalido_muestra_error(self):
        company = self.make_company()
        display = self.make_label(builder=company)
        response = self.client.post(self.url("edit_personal", pk=display.pk), {"name": ""})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Invalid form", self.messages_of(response))
        display.refresh_from_db()
        self.assertEqual(display.name, "Etiqueta de prueba")

    def test_borrar_etiqueta_propia(self):
        display = self.make_label()
        response = self.client.post(self.url("delete_sgalabel", pk=display.pk))
        self.assertRedirects(response, self.url("add_personal"), fetch_redirect_response=False)
        self.assertFalse(DisplayLabel.objects.filter(pk=display.pk).exists())

    def test_no_borra_etiqueta_de_otro(self):
        otro = User.objects.create_user("otro", "otro@test.org", "x")
        display = self.make_label(created_by=otro)
        response = self.client.post(self.url("delete_sgalabel", pk=display.pk))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(DisplayLabel.objects.filter(pk=display.pk).exists())
        self.assertIn("Error, user is not creator label", self.messages_of(response))

    def test_borrar_en_organizacion_ajena(self):
        display = self.make_label()
        response = self.client.post(self.url("delete_sgalabel", org=self.foreign, pk=display.pk))
        self.assertForbidden(response)
        self.assertTrue(DisplayLabel.objects.filter(pk=display.pk).exists())

    def test_preview_devuelve_la_representacion(self):
        display = self.make_label()
        response = self.client.get(self.url("get_preview", pk=display.pk))
        self.assertEqual(response.json(), {"svgString": "{}"})
        self.assertForbidden(self.client.get(self.url("get_preview", org=self.foreign, pk=display.pk)))

    def test_preview_motor_etiqueta_demasiado_pequena(self):
        diminuto = RecipientSize.objects.create(name="Vial", height=1, width=1, height_unit="cm", width_unit="cm")
        display = self.make_label(recipient=diminuto)
        response = self.client.get(self.url("engine_label_preview", pk=display.pk))
        self.assertEqual(response.status_code, 400)
        self.assertIn("mínimo", response.content.decode())


class SGALabelWizardTest(EditorViewsBase):
    def test_crear_etiqueta_la_asigna_al_usuario_y_organizacion(self):
        response = self.client.post(self.url("sgalabel_create"), {"name": "Nueva", "template": self.template.pk})
        display = DisplayLabel.objects.get(name="Nueva")
        self.assertRedirects(
            response, self.url("sgalabel_step_one", pk=display.pk), fetch_redirect_response=False
        )
        self.assertEqual((display.created_by, display.organization), (self.user, self.org))
        # Sin dueño la etiqueta no aparecía en "mis etiquetas" ni se podía borrar.
        listado = self.client.get(self.url("add_personal"))
        self.assertIn(display, listado.context["personal_templates"])

    def test_crear_etiqueta_invalida_vuelve_al_listado(self):
        response = self.client.post(self.url("sgalabel_create"), {"name": ""})
        self.assertRedirects(response, self.url("add_personal"), fetch_redirect_response=False)
        self.assertIn("Form is invalid", self.messages_of(response))
        self.assertRedirects(self.client.get(self.url("sgalabel_create")), self.url("add_personal"), fetch_redirect_response=False)

    def test_paso_uno_guarda_complemento_y_empresa(self):
        display = self.make_label()
        danger = DangerIndication.objects.get(code="H314")
        response = self.client.post(
            self.url("sgalabel_step_one", pk=display.pk),
            {
                "substance": self.substance.pk,
                "danger_indication": [danger.pk],
                "prudence_advice": [PrudenceAdvice.objects.first().pk],
                "warningword": WarningWord.objects.first().pk,
                "other_dangers": "Ninguno",
                "name": "Proveedor",
                "address": "Cartago",
                "phone": "2550-0000",
                "commercial_information": "Mayorista",
                "barcode": "12345",
            },
        )
        self.assertRedirects(
            response, self.url("sgalabel_step_two", pk=display.pk), fetch_redirect_response=False
        )
        display.refresh_from_db()
        self.assertEqual(display.label.substance, self.substance)
        self.assertEqual(display.label.builderInformation.name, "Proveedor")
        self.assertEqual(display.barcode, "12345")
        self.assertTrue(SGAComplement.objects.filter(substance=self.substance, danger_indication=danger).exists())

    def test_paso_uno_invalido_se_queda(self):
        display = self.make_label()
        response = self.client.post(self.url("sgalabel_step_one", pk=display.pk), {"substance": self.substance.pk})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["builderinformationform"].errors)
        display.refresh_from_db()
        self.assertIsNone(display.label.builderInformation)

    def _paso_dos(self, display, recipient):
        return self.client.post(
            self.url("sgalabel_step_two", pk=display.pk),
            {"name": display.name, "json_representation": "{}", "preview": "x", "recipient_size": recipient.pk},
        )

    def test_paso_dos_guarda_png_del_motor(self):
        mediano = RecipientSize.objects.create(name="Frasco", height=4, width=7, height_unit="cm", width_unit="cm")
        display = self.make_label(recipient=mediano, substance=self.substance)
        response = self._paso_dos(display, mediano)
        self.assertRedirects(response, self.url("add_personal"), fetch_redirect_response=False)
        display.refresh_from_db()
        self.assertTrue(display.label_in_png.startswith("data:image/png;base64,"))

    def test_paso_dos_etiqueta_pequena_no_bloquea_el_guardado(self):
        diminuto = RecipientSize.objects.create(name="Vial", height=1, width=1, height_unit="cm", width_unit="cm")
        display = self.make_label(recipient=diminuto)
        response = self._paso_dos(display, diminuto)
        self.assertEqual(response.status_code, 302)
        display.refresh_from_db()
        self.assertIsNone(display.label_in_png)


class RecipientAndCompanyTest(EditorViewsBase):
    def test_crear_recipiente_redirige_a_su_organizacion(self):
        data = {"name": "Botella", "height": 10, "height_unit": "cm", "width": 5, "width_unit": "cm"}
        response = self.client.post(self.url("add_recipient_size"), data)
        self.assertRedirects(response, self.url("add_recipient_size"), fetch_redirect_response=False)
        self.assertTrue(RecipientSize.objects.filter(name="Botella").exists())
        total = RecipientSize.objects.count()
        response = self.client.post(self.url("add_recipient_size"), {"name": "Sin medidas", "height_unit": "x"})
        self.assertRedirects(response, self.url("add_recipient_size"), fetch_redirect_response=False)
        self.assertEqual(RecipientSize.objects.count(), total)

    def test_datos_de_empresa_y_recipiente(self):
        company = self.make_company()
        self.assertEqual(
            self.client.get(self.url("get_company", pk=company.pk)).json(),
            {"name": "ACME", "address": "San José", "phone": "2222-2222", "commercial_information": "Distribuidor"},
        )
        data = self.client.get(self.url("get_recipient_size", pk=self.recipient.pk)).json()
        self.assertEqual((data["width"], data["height"], data["width_unit"]), (17.0, 13.0, "cm"))

    def test_complemento_por_sustancia(self):
        self.assertEqual(self.client.get(self.url("get_sgacomplement_by_substance", pk=self.substance.pk)).json(), {})
        complement = SGAComplement.objects.create(substance=self.substance)
        complement.danger_indication.add(DangerIndication.objects.get(code="H314"))
        data = self.client.get(self.url("get_sgacomplement_by_substance", pk=self.substance.pk)).json()
        self.assertEqual(data["danger_indication"][0]["id"], "H314")
        self.assertTrue(data["danger_indication"][0]["name"].startswith("(H314) "))

    def test_endpoints_json_exigen_sesion_y_organizacion(self):
        company = self.make_company()
        urls = [
            ("get_company", company.pk),
            ("get_sgacomplement_by_substance", self.substance.pk),
        ]
        for name, pk in urls:
            with self.subTest(name=name):
                self.assertForbidden(self.client.get(self.url(name, org=self.foreign, pk=pk)))
                anonimo = Client().get(self.url(name, pk=pk))
                self.assertEqual(anonimo.status_code, 302)
                self.assertIn("login", anonimo["Location"])

    def test_codigo_de_barras_svg(self):
        response = self.client.get(self.url("barcode_from_number", code="12345"))
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        self.assertIn(b"<svg", response.content)
        self.assertForbidden(self.client.get(self.url("barcode_from_number", org=self.foreign, code="1")))

    def test_quitar_empresa(self):
        company = self.make_company()
        response = self.client.post(self.url("remove_company", pk=company.pk))
        self.assertTrue(response.json()["status"])
        self.assertFalse(BuilderInformation.objects.filter(pk=company.pk).exists())
        self.assertEqual(self.client.post(self.url("remove_company", pk=0)).json(), {"msg": "Error", "status": False})
