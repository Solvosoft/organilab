"""Búsqueda libre de la tabla «Mis procedimientos» (``MyProcedureFilterSet``).

La vista de la API rechaza hoy el listado aun con la relación org-lab (ver
HALLAZGOS_COBERTURA, sección academic), así que el filtro se prueba directo:
es lo que aplica ``MyProceduresAPI.filter_queryset`` con ``?search=``.
"""
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase

from academic.api.filterset import MyProcedureFilterSet
from academic.models import MyProcedure, Procedure
from laboratory.models import OrganizationStructure


class BusquedaDeMisProcedimientosTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        org = OrganizationStructure.objects.create(name="Organización")
        cls.autora = User.objects.create_user("mgarcia", first_name="María", last_name="García")
        plantilla = Procedure.objects.create(title="Titulación ácido-base", description="d")
        tipo = ContentType.objects.get_for_model(OrganizationStructure)
        datos = dict(content_type=tipo, object_id=org.pk, organization=org)
        cls.titulacion = MyProcedure.objects.create(
            name="Práctica 1", custom_procedure=plantilla, created_by=cls.autora, **datos
        )
        cls.otra = MyProcedure.objects.create(name="Destilación", **datos)

    def buscar(self, texto):
        request = RequestFactory().get("/", {"search": texto})
        filtro = MyProcedureFilterSet(request.GET, queryset=MyProcedure.objects.all(), request=request)
        return set(filtro.filter_queryset(MyProcedure.objects.all()))

    def test_busca_por_nombre_autor_y_plantilla(self):
        self.assertEqual(self.buscar("Destila"), {self.otra})
        # Nombre completo del autor: necesita la anotación ``fullname``.
        self.assertEqual(self.buscar("María García"), {self.titulacion})
        self.assertEqual(self.buscar("mgarcia"), {self.titulacion})
        self.assertEqual(self.buscar("ácido-base"), {self.titulacion})

    def test_sin_busqueda_no_filtra(self):
        self.assertEqual(self.buscar(""), {self.titulacion, self.otra})
