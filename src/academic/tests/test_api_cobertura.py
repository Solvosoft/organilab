"""API de ``academic``: comentarios, tablas de procedimientos, selects y serializadores.

Complementa ``test_my_procedure.py`` y ``test_procedure_api.py`` con las ramas de
error (permisos, datos inválidos, organización inexistente) y los métodos de
presentación de los serializadores.
"""

import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from academic.api.serializers import (
    MyProcedureSerializer,
    ProcedureSerializer,
    ProcedureStepCommentSerializer,
)
from academic.api.views import _extract_form_fields
from academic.models import (
    CommentProcedureStep,
    MyProcedure,
    Procedure,
    ProcedureRequiredObject,
    ProcedureStep,
)
from auth_and_perms.models import Profile
from laboratory.models import OrganizationStructure, UserOrganization


class ExtraerCamposFormioTest(TestCase):
    def test_recorre_contenedores_columnas_y_componentes_anidados(self):
        componentes = [
            {"type": "button", "key": "enviar"},
            {
                "type": "panel",
                "components": [{"type": "textfield", "key": "a", "label": "A"}],
            },
            {
                "type": "columns",
                "columns": [
                    {"components": [{"type": "number", "key": "b", "label": "B"}]},
                    {"components": []},
                ],
            },
            {
                "type": "container",
                "key": "grupo",
                "label": "Grupo",
                "components": [{"type": "textfield", "key": "c"}],
            },
            {"type": "textfield"},
        ]
        campos = _extract_form_fields(componentes, {"a": "uno", "b": 2, "grupo": {}})
        self.assertEqual(
            campos,
            [
                {"label": "A", "value": "uno"},
                {"label": "B", "value": 2},
                {"label": "Grupo", "value": {}},
                {"label": "c", "value": ""},
            ],
        )


class ComentariosDePasoErroresTest(TestCase):
    fixtures = ["object.json", "my_procedure.json"]

    def setUp(self):
        self.kwargs = {"org_pk": 1, "lab_pk": 1}
        self.client.force_login(User.objects.get(pk=1))

    def test_usuario_sin_permisos_recibe_403(self):
        self.client.force_login(User.objects.get(pk=3))
        response = self.client.post(
            reverse("laboratory:api-my-procedure-add-comment", kwargs=self.kwargs),
            {"procedure_step": 24, "my_procedure": 1, "comment": "intruso"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(CommentProcedureStep.objects.filter(comment="intruso").exists())

    def test_agregar_comentario_vacio_es_invalido(self):
        total = CommentProcedureStep.objects.count()
        response = self.client.post(
            reverse("laboratory:api-my-procedure-add-comment", kwargs=self.kwargs),
            {"procedure_step": 24, "my_procedure": 1},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("comment", response.json())
        self.assertEqual(CommentProcedureStep.objects.count(), total)

    def test_actualizar_comentario_vacio_es_invalido(self):
        comment = CommentProcedureStep.objects.first()
        original = comment.comment
        response = self.client.put(
            reverse(
                "laboratory:api-my-procedure-update-comment",
                kwargs={**self.kwargs, "pk": comment.pk},
            ),
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        comment.refresh_from_db()
        self.assertEqual(comment.comment, original)


class TablasConOrganizacionInvalidaTest(TestCase):
    """Con ``org_pk`` 0 (falso) la tabla no expone nada y responde 400."""

    fixtures = ["object.json", "my_procedure.json"]

    def setUp(self):
        self.admin = User.objects.create_superuser("admin_academic", password="x")
        Profile.objects.create(user=self.admin)
        self.client.force_login(self.admin)

    def test_mis_procedimientos_sin_organizacion(self):
        response = self.client.get(
            reverse("academic:api-my-procedure-list", kwargs={"org_pk": 0, "lab_pk": 1})
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("organization", response.json())

    def test_procedimientos_sin_organizacion(self):
        response = self.client.get(
            reverse("academic:api-procedure-list", kwargs={"org_pk": 0})
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("organization", response.json())

    def test_select_de_plantillas_sin_organizacion(self):
        response = self.client.get(reverse("custom_procedure_template-list"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("organization", response.json()["errors"])


class BusquedaEnTablasTest(TestCase):
    fixtures = ["object.json", "my_procedure.json"]

    def setUp(self):
        admin = User.objects.create_superuser("admin_busqueda", password="x")
        Profile.objects.create(user=admin)
        # Ser superusuario no basta: la API exige pertenecer a la organización.
        UserOrganization.objects.create(user=admin, organization_id=1, type_in_organization=1, status=True)
        self.client.force_login(admin)

    def test_busqueda_de_procedimientos(self):
        procedure = Procedure.objects.get(pk=10)
        procedure.content_object = OrganizationStructure.objects.get(pk=1)
        procedure.save()
        url = reverse("academic:api-procedure-list", kwargs={"org_pk": 1})
        encontrado = self.client.get(url, {"search": "description"}).json()
        vacio = self.client.get(url, {"search": "no-existe"}).json()
        self.assertEqual(encontrado["recordsFiltered"], 1)
        self.assertEqual(vacio["recordsFiltered"], 0)


class PresentacionDeModelosYSerializadoresTest(TestCase):
    fixtures = ["object.json", "procedure.json"]

    def test_textos_de_los_modelos(self):
        user = User.objects.get(pk=1)
        step = ProcedureStep.objects.get(pk=17)
        required = ProcedureRequiredObject.objects.get(pk=12)
        comment = CommentProcedureStep.objects.create(
            created_by=user, comment="hola", procedure_step=step
        )
        my_procedure = MyProcedure(name="Mi práctica")
        self.assertEqual(str(my_procedure), "Mi práctica")
        self.assertEqual(str(step), step.title)
        self.assertTrue(str(comment).startswith(str(user)))
        self.assertEqual(
            required.get_object_detail(),
            "%s %s" % (required.object, required.measurement_unit),
        )
        step.description = "<b>negrita</b>"
        self.assertEqual(step.get_description_display(), "<b>negrita</b>")

    def test_autor_del_comentario(self):
        serializer = ProcedureStepCommentSerializer()
        sin_nombre = User(username="anonimo")
        self.assertEqual(serializer.get_created_by(None), "No user found")
        self.assertEqual(
            serializer.get_created_by(CommentProcedureStep(created_by=None)), "No user found"
        )
        self.assertEqual(
            serializer.get_created_by(CommentProcedureStep(created_by=sin_nombre)), "anonimo"
        )

    def test_campos_vacios_de_mis_procedimientos(self):
        serializer = MyProcedureSerializer()
        vacio = MyProcedure(name="", custom_procedure=None, status="", created_by=None)
        self.assertEqual(serializer.get_name(vacio), "")
        self.assertEqual(serializer.get_custom_procedure(vacio), "")
        self.assertEqual(serializer.get_status(vacio), "")
        self.assertEqual(serializer.get_created_by(None), "No user found")
        self.assertEqual(serializer.get_created_by(vacio), "No user found")
        vacio.created_by = User(username="anonimo")
        self.assertEqual(serializer.get_created_by(vacio), "anonimo")
        # Un objeto sin `created_by` no rompe la tabla.
        self.assertEqual(serializer.get_created_by(object()), "No user found")

    def test_campos_vacios_de_procedimientos(self):
        serializer = ProcedureSerializer()
        vacio = Procedure(title="", description="")
        self.assertEqual(serializer.get_title(vacio), "")
        self.assertEqual(serializer.get_description(vacio), "")
