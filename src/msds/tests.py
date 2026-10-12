from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
import json


class MsdsTest(TestCase):
    fixtures = ["msds_data.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        permission = Permission.objects.get(codename="institution_can_access")
        self.user.user_permissions.add(permission)
        for codename in ["view_msdsobject", "add_msdsobject"]:
            perm = Permission.objects.get(codename=codename)
            self.user.user_permissions.add(perm)
        self.url_attr = {"org_pk": 1}
        self.client.force_login(self.user)

    def test_get_msds(self):
        response = self.client.get(reverse("msds:list_msds", kwargs=self.url_attr))
        self.assertEqual(response.status_code, 200)

    def test_index_msds(self):
        response = self.client.get(reverse("msds:index_msds", kwargs=self.url_attr))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name="index_msds.html")

    def test_sds_create_redirects_to_the_sga_wizard(self):
        """El alta de sustancias vive solo en el asistente de SGA."""
        response = self.client.get(reverse("msds:sds_create", kwargs=self.url_attr))
        self.assertRedirects(
            response,
            reverse("sga:create_sustance", kwargs=self.url_attr),
            fetch_redirect_response=False,
        )

    def test_get_regulations(self):
        response = self.client.get(reverse("regulation_docs"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["object_list"].count() == 15)


import shutil  # noqa: E402
import tempfile  # noqa: E402
import zipfile  # noqa: E402
from io import BytesIO  # noqa: E402

from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.test import override_settings  # noqa: E402

from laboratory.models import Catalog, Object, OrganizationStructure  # noqa: E402
from msds.models import OrganilabNode, RegulationDocument  # noqa: E402
from sga.models import (  # noqa: E402
    DangerIndication,
    SDSTraceability,
    SubstanceCharacteristics,
    WarningWord,
)

MEDIA_TMP = tempfile.mkdtemp(prefix="msds_tests_")


def tearDownModule():
    shutil.rmtree(MEDIA_TMP, ignore_errors=True)


def crear_sustancia(organization, name, cas="", **kwargs):
    obj = Object.objects.create(name=name, organization=organization)
    sc = SubstanceCharacteristics.objects.create(
        object_related=obj, cas_id_number=cas, **kwargs
    )
    return obj, sc


class MsdsModelsTest(TestCase):
    """Representación de los nodos del árbol y de los documentos de regulación."""

    fixtures = ["msds_data.json"]

    def test_nodo_raiz_y_hoja(self):
        raiz = OrganilabNode.objects.get(pk=11)
        hoja = OrganilabNode.objects.get(pk=18)
        self.assertEqual(str(raiz), "Tutoriales")
        self.assertFalse(raiz.is_leaf_node)
        self.assertFalse(raiz.is_not_root_node)
        self.assertTrue(hoja.is_leaf_node)
        self.assertTrue(hoja.is_not_root_node)

    def test_str_documento_regulacion(self):
        doc = RegulationDocument.objects.first()
        self.assertEqual(str(doc), doc.name)


@override_settings(MEDIA_ROOT=MEDIA_TMP)
class ListMsdsFiltersTest(TestCase):
    """El endpoint de DataTables de `index_msds`: filtros, paginación y fila."""

    fixtures = ["msds_data.json"]

    @classmethod
    def setUpTestData(cls):
        cls.org = OrganizationStructure.objects.get(pk=1)
        cls.otra = OrganizationStructure.objects.create(name="Otra organización")
        cls.user = User.objects.get(pk=1)
        for codename in ["view_msdsobject", "add_msdsobject"]:
            cls.user.user_permissions.add(Permission.objects.get(codename=codename))
        _, cls.sc_acetona = crear_sustancia(cls.org, "Acetona", cas="67-64-1")
        _, cls.sc_etanol = crear_sustancia(
            cls.org,
            "Etanol",
            cas="64-17-5",
            security_sheet=SimpleUploadedFile("etanol.pdf", b"%PDF-1.4"),
        )
        _, cls.sc_ajena = crear_sustancia(cls.otra, "Ajena", cas="1-1-1")
        cls.t_acetona = SDSTraceability.objects.create(
            sga_substance_characteristics=cls.sc_acetona,
            source="merck",
            revision_date="2024-01-10",
            security_sheet=SimpleUploadedFile("acetona.pdf", b"%PDF-1.4"),
        )
        cls.t_etanol = SDSTraceability.objects.create(
            sga_substance_characteristics=cls.sc_etanol, source="pubchem"
        )
        SDSTraceability.objects.create(sga_substance_characteristics=cls.sc_ajena)

    def setUp(self):
        self.client.force_login(self.user)
        self.url = reverse("msds:list_msds", kwargs={"org_pk": self.org.pk})

    def get(self, **params):
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_lista_solo_la_organizacion_y_arma_la_fila(self):
        data = self.get(draw="3")
        self.assertEqual(data["recordsTotal"], 2)
        self.assertEqual(data["draw"], 3)
        filas = {fila[0]: fila for fila in data["data"]}
        self.assertEqual(set(filas), {"Acetona", "Etanol"})
        acetona = filas["Acetona"]
        self.assertEqual(acetona[1], "67-64-1")
        self.assertEqual(acetona[2], "Merck/Sigma-Aldrich")
        self.assertEqual(acetona[3], "2024-01-10")
        self.assertIn("acetona", acetona[5])
        # Sin ficha propia en la traza cae a la de la sustancia.
        self.assertIn("etanol", filas["Etanol"][5])

    def test_sin_ficha_muestra_na(self):
        self.t_etanol.sga_substance_characteristics.security_sheet = None
        self.t_etanol.sga_substance_characteristics.save()
        filas = {fila[0]: fila for fila in self.get()["data"]}
        self.assertEqual(filas["Etanol"][5], "N/A")
        self.assertEqual(filas["Etanol"][3], "")

    def test_busqueda_global_y_filtros_por_columna(self):
        self.assertEqual(self.get(**{"search[value]": "67-64"})["recordsFiltered"], 1)
        self.assertEqual(self.get(substance__icontains="eta")["data"][0][0], "Etanol")
        self.assertEqual(self.get(cas_code="67-64")["data"][0][0], "Acetona")
        self.assertEqual(self.get(source="pubchem")["data"][0][0], "Etanol")

    def test_rango_de_fechas_de_revision(self):
        data = self.get(revision_date="2024-01-01, 2024-01-31")
        self.assertEqual([f[0] for f in data["data"]], ["Acetona"])
        self.assertEqual(self.get(revision_date="2024-02-01,")["recordsFiltered"], 0)
        self.assertEqual(self.get(revision_date=",2023-12-31")["recordsFiltered"], 0)
        # Más de dos partes: el filtro se ignora.
        self.assertEqual(self.get(revision_date="a,b,c")["recordsFiltered"], 2)

    def test_paginacion_por_pagina_y_valores_invalidos(self):
        data = self.get(page="2", page_size="1")
        self.assertEqual(len(data["data"]), 1)
        # Una página fuera de rango vuelve a la primera.
        self.assertEqual(len(self.get(page="9", page_size="1")["data"]), 1)
        # Valores no numéricos caen a los valores por defecto.
        self.assertEqual(len(self.get(page_size="x")["data"]), 2)
        self.assertEqual(len(self.get(page_size="0")["data"]), 2)

    def test_draw_invalido_se_omite(self):
        self.assertNotIn("draw", self.get(draw="abc"))


@override_settings(MEDIA_ROOT=MEDIA_TMP)
class RegulationDownloadTest(TestCase):
    """La descarga empaqueta todos los documentos de regulación en un zip."""

    def test_descarga_zip_con_nombre_y_pais(self):
        RegulationDocument.objects.create(
            name="Ley", country="CR", file=SimpleUploadedFile("ley.pdf", b"%PDF")
        )
        response = self.client.get(reverse("download_all_regulations"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("regulations.zip", response["Content-Disposition"])
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            self.assertEqual(z.namelist(), ["Ley_CR.pdf"])


@override_settings(MEDIA_ROOT=MEDIA_TMP)
class SDSTraceabilityApiTest(TestCase):
    """API de fichas verificadas: listado, verificación y detalle de la sustancia."""

    fixtures = ["msds_data.json"]

    @classmethod
    def setUpTestData(cls):
        cls.org = OrganizationStructure.objects.get(pk=1)
        cls.otra = OrganizationStructure.objects.create(name="Otra organización")
        cls.user = User.objects.get(pk=1)
        for codename in ["view_sdstraceability", "change_sdstraceability"]:
            cls.user.user_permissions.add(Permission.objects.get(codename=codename))
        cls.verificador = User.objects.create_user(
            username="verif", first_name="Ana", last_name="Solís"
        )
        palabra = WarningWord.objects.create(name="Peligro")
        cls.h_prueba = DangerIndication.objects.create(
            code="HX999", description="Inflamable de prueba", warning_words=palabra
        )
        obj, cls.sc = crear_sustancia(
            cls.org,
            "Acetona",
            cas="67-64-1",
            molecular_formula="C3H6O",
            valid_molecular_formula=True,
            is_precursor=True,
            iarc=Catalog.objects.create(key="IARC", description="Grupo 3"),
            imdg=Catalog.objects.create(key="IDMG", description="Clase 3"),
            precursor_type=Catalog.objects.create(key="Precursor", description="Tabla I"),
            security_sheet=SimpleUploadedFile("acetona.pdf", b"%PDF"),
        )
        cls.sc.h_code.add(cls.h_prueba)
        cls.sc.white_organ.add(Catalog.objects.create(key="white_organ", description="Hígado"))
        cls.sc.ue_code.add(Catalog.objects.create(key="ue_code", description="EUH066"))
        cls.sc.nfpa.add(Catalog.objects.create(key="nfpa", description="3"))
        cls.sc.storage_class.add(Catalog.objects.create(key="storage_class", description="3"))
        cls.traza = SDSTraceability.objects.create(
            sga_substance_characteristics=cls.sc, verified_by=cls.verificador
        )
        _, cls.sc_simple = crear_sustancia(cls.org, "Agua")
        cls.traza_simple = SDSTraceability.objects.create(
            sga_substance_characteristics=cls.sc_simple
        )

    def setUp(self):
        self.client.force_login(self.user)
        self.kw = {"org_pk": self.org.pk}

    def test_listado_serializa_las_filas(self):
        response = self.client.get(
            reverse("msds:api-sds-traceability-list", kwargs=self.kw)
        )
        self.assertEqual(response.status_code, 200)
        filas = {f["sustance_characteristics_name"]: f for f in response.json()["data"]}
        acetona = filas["Acetona"]
        self.assertEqual(acetona["sustance_characteristics_cas_id_number"], "67-64-1")
        self.assertEqual(acetona["verified_by_name"], "Ana Solís")
        self.assertIn("acetona", acetona["security_sheet_url"])
        self.assertEqual(acetona["hcodes"], "HX999")
        self.assertEqual(
            acetona["actions"],
            {"list": True, "verify": True, "create": False, "update": False,
             "destroy": False, "verified": False},
        )
        agua = filas["Agua"]
        self.assertEqual(agua["verified_by_name"], "")
        self.assertEqual(agua["security_sheet_url"], "")
        self.assertEqual(agua["hcodes"], "")

    def test_listado_sin_objeto_relacionado(self):
        """Una sustancia cuyo objeto se borró (SET_NULL) no rompe el listado."""
        self.sc_simple.object_related = None
        self.sc_simple.save()
        response = self.client.get(
            reverse("msds:api-sds-traceability-list", kwargs=self.kw)
        )
        self.assertEqual(response.status_code, 200)
        nombres = [f["sustance_characteristics_name"] for f in response.json()["data"]]
        self.assertIn("", nombres)

    def test_verificar_y_desverificar(self):
        url = reverse("msds:api-sds-traceability-verify", kwargs=self.kw)
        response = self.client.post(url, {"id": self.traza.pk, "is_verified": True})
        self.assertEqual(response.status_code, 200)
        self.traza.refresh_from_db()
        self.assertTrue(self.traza.is_verified)
        self.assertEqual(self.traza.verified_by, self.user)
        self.assertIsNotNone(self.traza.verified_date)

        response = self.client.post(url, {"id": self.traza.pk, "is_verified": False})
        self.assertEqual(response.status_code, 200)
        self.traza.refresh_from_db()
        self.assertFalse(self.traza.is_verified)
        self.assertIsNone(self.traza.verified_by)
        self.assertIsNone(self.traza.verified_date)

    def test_verificar_con_dato_invalido_y_sin_ficha(self):
        url = reverse("msds:api-sds-traceability-verify", kwargs=self.kw)
        response = self.client.post(url, {"id": self.traza.pk, "is_verified": "quizá"})
        self.assertEqual(response.status_code, 400)
        response = self.client.post(url, {"id": 999999, "is_verified": True})
        self.assertEqual(response.status_code, 404)

    def test_verificar_en_organizacion_ajena(self):
        url = reverse("msds:api-sds-traceability-verify", kwargs={"org_pk": self.otra.pk})
        response = self.client.post(url, {"id": self.traza.pk, "is_verified": True})
        self.assertEqual(response.status_code, 403)
        self.traza.refresh_from_db()
        self.assertFalse(self.traza.is_verified)

    def test_informacion_de_la_sustancia(self):
        url = reverse(
            "msds:api-sds-traceability-get-sustance-characteristics-info", kwargs=self.kw
        )
        data = self.client.get(url, {"pk": self.traza.pk}).json()
        self.assertEqual(data["obj_name"], "Acetona")
        self.assertEqual(data["cas_id_number"], "67-64-1")
        self.assertEqual(data["molecular_formula"], "C3H6O")
        self.assertEqual(data["is_precursor"], "Yes")
        self.assertEqual(data["iarc_name"], "Grupo 3")
        self.assertEqual(data["imdg_name"], "Clase 3")
        self.assertEqual(data["precursor_type_name"], "Tabla I")
        self.assertEqual(data["white_organ_list"], ["Hígado"])
        self.assertEqual(data["h_code_list"], ["(HX999) Inflamable de prueba"])
        self.assertEqual(data["ue_code_list"], ["EUH066"])
        self.assertEqual(data["nfpa_list"], ["3"])
        self.assertEqual(data["storage_class_list"], ["3"])
        self.assertIn("acetona", data["security_sheet_url"])

        self.sc_simple.object_related = None
        self.sc_simple.save()
        data = self.client.get(url, {"pk": self.traza_simple.pk}).json()
        self.assertEqual(
            [data[k] for k in ("obj_name", "cas_id_number", "molecular_formula",
                               "is_precursor", "iarc_name", "imdg_name",
                               "precursor_type_name", "security_sheet_url")],
            ["", "", "", "No", "", "", "", ""],
        )

    def test_informacion_en_organizacion_ajena(self):
        url = reverse(
            "msds:api-sds-traceability-get-sustance-characteristics-info",
            kwargs={"org_pk": self.otra.pk},
        )
        self.assertEqual(self.client.get(url, {"pk": self.traza.pk}).status_code, 403)
