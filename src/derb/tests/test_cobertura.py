"""Ramas de derb no alcanzadas por las pruebas de vistas y API existentes."""
import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from derb.models import CustomForm, CustomFormField, FieldType, Section, Subsection, WidgetType
from laboratory.models import Laboratory, OrganizationStructure, UserOrganization


class DerbModelsStrTest(TestCase):
    """Representación de los catálogos del constructor de formularios."""

    def test_str_de_tipos_y_campo(self):
        field_type = FieldType.objects.create(import_name="django.forms.CharField", display_name="Texto")
        widget = WidgetType.objects.create(import_name="django.forms.TextInput", display_name="Caja")
        form = CustomForm.objects.create(name="F", schema={}, organization=OrganizationStructure.objects.create(name="O"))
        section = Section.objects.create(form=form, name="S")
        subsection = Subsection.objects.create(section=section, name="SS")
        field = CustomFormField.objects.create(
            subsection=subsection, name="nombre", label="Nombre", field_type=field_type, widget_type=widget
        )
        self.assertEqual(str(field_type), "Texto")
        self.assertEqual(str(widget), "Caja")
        self.assertEqual(str(field), "Nombre")


class DerbViewsBranchesTest(TestCase):
    fixtures = ["derb.json"]

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client.force_login(self.user)
        self.org_kw = {"org_pk": 1}

    def test_crear_formulario_solo_por_post(self):
        response = self.client.get(reverse("derb:create_form", kwargs=self.org_kw))
        self.assertEqual(response.status_code, 405)

    def test_editar_esquema_sin_ajax_es_peticion_invalida(self):
        response = self.client.post(
            reverse("derb:edit_view", kwargs={"org_pk": 1}),
            data=json.dumps({"components": []}), content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_editar_esquema_por_ajax(self):
        form = CustomForm.objects.first()
        page = reverse("derb:edit_view", kwargs={"org_pk": 1, "form_id": form.pk})
        # El JS publica en `editView/` y el formulario sale del Referer de la página.
        response = self.client.post(
            reverse("derb:edit_view", kwargs={"org_pk": 1}),
            data=json.dumps({"components": [{"key": "x"}]}), content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest", HTTP_REFERER="http://testserver" + page,
        )
        self.assertEqual(json.loads(response.json()), {"result": True})
        form.refresh_from_db()
        self.assertEqual(form.schema, {"components": [{"key": "x"}]})

    def test_autocompletar_plantillas_por_organizacion(self):
        url = reverse("informtemplate-detail", kwargs={"pk": 1})
        names = {row["text"] for row in self.client.get(url).json()["results"]}
        self.assertEqual(names, set(CustomForm.objects.filter(organization=1).values_list("name", flat=True)))
        self.assertEqual(self.client.get(reverse("informtemplate-detail", kwargs={"pk": 999999})).status_code, 404)

    def test_listado_de_plantillas_sin_organizacion_esta_vacio(self):
        response = self.client.get(reverse("informtemplate-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])


class OrganizationUsersByLabTest(TestCase):
    """`api/orgView/?lab=<pk>` devuelve los usuarios del árbol de la organización."""

    fixtures = ["laboratory_data.json"]

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client.force_login(self.user)
        self.org = OrganizationStructure.objects.get(pk=1)
        child = OrganizationStructure.objects.create(name="Hija", parent=self.org)
        self.child_user = User.objects.create_user(username="hija_user")
        UserOrganization.objects.create(user=self.child_user, organization=child, status=True)
        # pk de varios dígitos: el parámetro no se puede leer carácter a carácter.
        self.lab = Laboratory.objects.create(pk=4321, name="Lab hijo", organization=self.org)
        self.url = reverse("derb:api_org_structure", kwargs={"org_pk": self.org.pk})

    def values(self, **params):
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200)
        return [row["value"] for row in response.json()]

    def test_con_laboratorio_incluye_organizaciones_hijas(self):
        self.assertIn("hija_user", self.values(lab=self.lab.pk))

    def test_sin_laboratorio_solo_la_organizacion(self):
        self.assertNotIn("hija_user", self.values())
        self.assertNotIn("hija_user", self.values(lab="no-es-numero"))
