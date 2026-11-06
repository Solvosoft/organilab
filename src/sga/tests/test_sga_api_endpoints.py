"""Endpoints REST de ``sga/api``: recipientes, etiquetas, sustancias, revisión y
componentes SGA (palabras de advertencia, indicaciones y consejos).

Cada prueba aserta el JSON devuelto, el efecto en la base y el rechazo a
usuarios sin permiso o de otra organización.
"""
import json
from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status

from auth_and_perms.models import Profile
from laboratory.models import Catalog, OrganizationStructure
from sga.api import serializers as sga_serializers
from sga.models import (
    DangerIndication,
    DangerSubstance,
    DangerSubstanceCategory,
    DisplayLabel,
    Label,
    PrudenceAdvice,
    RecipientSize,
    ReviewSubstance,
    SecurityLeaf,
    Substance,
    TemplateSGA,
    WarningWord,
)


class ComponentsBase(TestCase):
    fixtures = ["sga_components_data.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.client.force_login(self.user)
        self.org = OrganizationStructure.objects.get(pk=1)

    def sin_permisos(self):
        """Miembro sin ningún rol: el middleware no le da permisos efectivos."""
        user = User.objects.create_user("sinrol", "sinrol@test.org", "x")
        Profile.objects.create(user=user)
        client = Client()
        client.force_login(user)
        return client

    def lab_url(self, name, **kwargs):
        return reverse(f"laboratory:{name}", kwargs={"org_pk": self.org.pk, **kwargs})

    def sga_url(self, name, **kwargs):
        return reverse(f"sga:{name}", kwargs={"org_pk": self.org.pk, **kwargs})


class RecipientSizeAPITest(ComponentsBase):
    def test_listado_con_busqueda_y_acciones(self):
        RecipientSize.objects.create(name="Bidón", height=40, width=30)
        response = self.client.get(self.sga_url("api-recipient-size-list"), {"search": "Bid", "draw": 3})
        data = response.json()
        self.assertEqual((data["draw"], data["recordsFiltered"]), (3, 1))
        self.assertEqual(data["recordsTotal"], RecipientSize.objects.count())
        fila = data["data"][0]
        self.assertEqual((fila["name"], fila["height"], fila["height_unit"]), ("Bidón", 40.0, "Centimeters"))
        self.assertIn("edit_recipient_size", fila["actions"])
        self.assertIn("delete_recipient_size", fila["actions"])

    def test_listado_valores_vacios(self):
        RecipientSize.objects.all().delete()
        RecipientSize.objects.create(name="", height=0, width=0, height_unit="", width_unit="")
        fila = self.client.get(self.sga_url("api-recipient-size-list")).json()["data"][0]
        self.assertEqual(
            [fila[k] for k in ("name", "height", "height_unit", "width", "width_unit")], ["", 0, "", 0, ""]
        )

    def test_obtener_crear_y_actualizar(self):
        recipient = RecipientSize.objects.create(name="Frasco", height=10, width=5)
        detalle = self.client.get(self.sga_url("api-recipient-size-get-recipient", pk=recipient.pk)).json()
        self.assertEqual(detalle["name"], "Frasco")

        data = {"name": "Galón", "height": 30, "height_unit": "cm", "width": 20, "width_unit": "cm"}
        response = self.client.post(self.sga_url("api-recipient-size-create-recipient"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(RecipientSize.objects.filter(name="Galón").exists())
        response = self.client.post(self.sga_url("api-recipient-size-create-recipient"), {"name": "Malo", "height": -1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("height", response.json()["errors"])

        url = self.sga_url("api-recipient-size-update-recipient", pk=recipient.pk)
        response = self.client.put(url, data=json.dumps(dict(data, name="Frasco grande")), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recipient.refresh_from_db()
        self.assertEqual((recipient.name, recipient.height), ("Frasco grande", 30.0))
        response = self.client.put(url, data=json.dumps({"name": "x", "width_unit": "km"}), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("width_unit", response.json()["errors"])

    def test_borrar_solo_si_no_esta_en_uso(self):
        url = self.sga_url("api-recipient-size-delete-recipient")
        libre = RecipientSize.objects.create(name="Libre")
        response = self.client.delete(url, data=json.dumps({"pk": libre.pk}), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(RecipientSize.objects.filter(pk=libre.pk).exists())

        en_uso = TemplateSGA.objects.get(pk=2).recipient_size
        response = self.client.delete(url, data=json.dumps({"pk": en_uso.pk}), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(RecipientSize.objects.filter(pk=en_uso.pk).exists())

        response = self.client.delete(url, data=json.dumps({"pk": 99999}), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rechaza_sin_permiso_y_organizacion_ajena(self):
        response = self.sin_permisos().get(self.sga_url("api-recipient-size-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        ajeno = Client()
        ajeno.force_login(User.objects.get(pk=2))
        response = ajeno.post(self.sga_url("api-recipient-size-create-recipient"), {"name": "x"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DisplayLabelAPITest(ComponentsBase):
    def setUp(self):
        super().setUp()
        template = TemplateSGA.objects.get(pk=2)
        otra = OrganizationStructure.objects.create(name="Otra")
        self.user.first_name, self.user.last_name = "Ana", "Mora"
        self.user.save()
        sin_nombre = User.objects.create_user("sin_nombre")
        for name, org, autor in (("Mía", self.org, self.user), ("Anónima", self.org, sin_nombre), ("Ajena", otra, self.user)):
            DisplayLabel.objects.create(
                name=name, json_representation="{}", template=template, label=Label.objects.create(),
                organization=org, created_by=autor,
            )

    def test_listado_de_la_organizacion(self):
        data = self.client.get(self.sga_url("api-labels-list")).json()
        self.assertEqual(data["recordsTotal"], 3)
        filas = {f["name"]: f for f in data["data"]}
        self.assertEqual(set(filas), {"Mía", "Anónima"})
        self.assertEqual(filas["Mía"]["created_by"], "Ana Mora")
        self.assertEqual(filas["Anónima"]["created_by"], "sin_nombre")
        self.assertEqual(filas["Mía"]["actions"], "actions")

    def test_filtro_por_autor(self):
        data = self.client.get(self.sga_url("api-labels-list"), {"created_by": "mora"}).json()
        self.assertEqual([f["name"] for f in data["data"]], ["Mía"])

    def test_serializer_sin_autor(self):
        self.assertEqual(sga_serializers.DisplayLabelSerializer().get_created_by(SimpleNamespace(created_by=None)), "")


class SgaComponentsPermissionTest(ComponentsBase):
    def test_sin_permiso_en_cada_endpoint(self):
        client = self.sin_permisos()
        for name in (
            "api-warnings-table-list",
            "api-warning-word-list",
            "api-dangers-table-list",
            "api-danger-indication-list",
            "api-advices-table-list",
            "api-prudence-advice-list",
        ):
            with self.subTest(name=name):
                response = client.get(self.lab_url(name))
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SgaComponentsAPITest(ComponentsBase):
    def test_tabla_de_consejos(self):
        PrudenceAdvice.objects.create(code="P999", name="Lavar con agua")
        data = self.client.get(self.lab_url("api-advices-table-list"), {"search": "P999", "draw": 2}).json()
        self.assertEqual((data["draw"], data["recordsFiltered"]), (2, 1))
        self.assertEqual(data["data"][0]["name"], "Lavar con agua")

    def test_listado_de_indicaciones(self):
        data = self.client.get(self.lab_url("api-danger-indication-list")).json()
        codigos = [r["code"] for r in data["results"]]
        self.assertEqual(codigos, sorted(codigos))
        self.assertEqual(data["count"], DangerIndication.objects.count())

    def test_crear_invalido_responde_errores(self):
        for name, campo in (
            ("api-warning-word-list", "name"),
            ("api-danger-indication-list", "code"),
            ("api-prudence-advice-list", "code"),
        ):
            with self.subTest(name=name):
                response = self.client.post(self.lab_url(name), {})
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(campo, response.json()["errors"])

    def test_actualizar_invalido(self):
        casos = (
            ("api-warning-word-detail", 18),
            ("api-danger-indication-detail", "H131"),
            ("api-prudence-advice-detail", 1),
        )
        for name, pk in casos:
            with self.subTest(name=name):
                response = self.client.put(self.lab_url(name, pk=pk), data=json.dumps({}), content_type="application/json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(WarningWord.objects.get(pk=18).name, "Hazard")

    def test_actualizar_indicacion(self):
        data = {
            "code": "H131",
            "description": "Descripción nueva",
            "warning_words": 16,
            "warning_class": [2],
            "warning_category": [2],
            "prudence_advice": [1],
        }
        url = self.lab_url("api-danger-indication-detail", pk="H131")
        response = self.client.put(url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        danger = DangerIndication.objects.get(pk="H131")
        self.assertEqual((danger.description, danger.warning_words_id), ("Descripción nueva", 16))

    def test_serializers_campos_vacios(self):
        vacio = SimpleNamespace(code="", name="", description="", warning_words=None)
        self.assertEqual(sga_serializers.PrudenceAdviceSerializer().get_code(vacio), "")
        self.assertEqual(sga_serializers.PrudenceAdviceSerializer().get_name(vacio), "")
        self.assertEqual(sga_serializers.WarningWordSerializer().get_name(vacio), "")
        danger = sga_serializers.DangerIndicationSerializer()
        self.assertEqual((danger.get_code(vacio), danger.get_description(vacio), danger.get_warning_words(vacio)), ("", "", ""))


class DangerSubstanceAPITest(ComponentsBase):
    def test_listado_con_tipo_y_categoria(self):
        DangerSubstance.objects.create(name="Benceno", cas_code="71-43-2", type_match="cas")
        data = self.client.get(self.sga_url("api-danger-substance-list")).json()
        fila = data["data"][0]
        self.assertEqual((fila["type_match"]["id"], fila["type_match"]["text"]), ("cas", "CAS"))

        DangerSubstanceCategory.objects.create(
            h_code=DangerIndication.objects.get(pk="H131"), category="health", note="Nota"
        )
        fila = self.client.get(self.sga_url("api-danger-substance-category-list")).json()["data"][0]
        self.assertEqual((fila["category"]["id"], fila["category"]["text"]), ("health", "Health"))
        self.assertEqual(fila["actions"], {"create": True, "update": True, "destroy": True})


class SubstanceAPITest(TestCase):
    fixtures = ["substances.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.client.force_login(self.user)

    def test_borrar_sustancia(self):
        url = reverse("sga:api-substance-detail", kwargs={"org_pk": 1, "pk": 134})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertFalse(Substance.objects.filter(pk=134).exists())

    def test_no_borra_sustancia_de_otra_organizacion(self):
        otra = OrganizationStructure.objects.create(name="Otra")
        ajena = Substance.objects.create(comercial_name="Ajena", organization=otra, created_by=self.user)
        url = reverse("sga:api-substance-detail", kwargs={"org_pk": 1, "pk": ajena.pk})
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Substance.objects.filter(pk=ajena.pk).exists())

    def test_serializer_sustancia(self):
        ser = sga_serializers.SubstanceSerializer()
        sin_nombre = User(username="usuario")
        self.assertEqual(ser.get_created_by(None), "No user found")
        self.assertEqual(ser.get_created_by(SimpleNamespace(created_by=None)), "No user found")
        self.assertEqual(ser.get_created_by(SimpleNamespace(created_by=sin_nombre)), "usuario")
        self.assertEqual(ser.get_created_by(SimpleNamespace()), "No user found")
        self.assertEqual(ser.get_organization(SimpleNamespace(organization=None)), "")
        substance = Substance(status=Substance.APPROVED)
        self.assertEqual(ser.get_status(substance), "Approved")


class ReviewSubstanceAPITest(TestCase):
    fixtures = ["substances.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.client.force_login(self.user)
        self.substance = Substance.objects.get(pk=134)
        revisor = User.objects.create_user("revisor_sin_nombre")
        ReviewSubstance.objects.create(substance=self.substance, created_by=revisor, organization=self.substance.organization)
        self.url = reverse("sga:api-reviewsubstance-list", kwargs={"org_pk": 1})

    def test_listado_con_filtros(self):
        SecurityLeaf.objects.create(substance=self.substance)
        data = self.client.get(self.url, {"created_by": "revisor", "comercial_name": self.substance.comercial_name[:4]}).json()
        self.assertEqual(data["recordsFiltered"], 1)
        fila = data["data"][0]
        self.assertEqual(fila["created_by"], "revisor_sin_nombre")
        self.assertIn(reverse("sga:security_leaf_pdf", kwargs={"org_pk": 1, "substance": 134}), fila["actions"])
        vacio = self.client.get(self.url, {"created_by": "nadie"}).json()
        self.assertEqual(vacio["recordsFiltered"], 0)

    def test_serializer_sin_sustancia(self):
        ser = sga_serializers.ReviewSubstanceSerializer()
        sin_sustancia = SimpleNamespace(substance=None)
        self.assertEqual(ser.get_comercial_name(sin_sustancia), "")
        self.assertEqual(ser.get_laboratories(sin_sustancia), "")
        self.assertEqual(ser.get_organization(SimpleNamespace(substance=SimpleNamespace(organization=None))), "")


class CatalogLookupsTest(ComponentsBase):
    def test_unidades_del_catalogo(self):
        response = self.client.get(reverse("catalogsga-list"))
        textos = {r["text"] for r in response.json()["results"]}
        self.assertTrue(textos <= {"Litros", "Kilogramos", "Libra"})
        self.assertIn("Litros", textos)
        self.assertTrue(Catalog.objects.filter(key="units", description="Metros").exists())
