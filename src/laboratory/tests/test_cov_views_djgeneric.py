"""Vistas genéricas de `laboratory.views.djgeneric`.

Se prueban con `RequestFactory` y subclases mínimas: lo que interesa es el control
de acceso común (404 cuando el usuario no alcanza la org/lab, edificio ajeno) y las
exportaciones de `ReportListView`, no una vista concreta.
"""

from django.contrib.auth import get_user_model
from django.http import Http404
from django.test import RequestFactory

from laboratory.models import Laboratory, OrganizationStructure, Provider
from laboratory.tests.utils import BaseLaboratorySetUpTest
from laboratory.views import djgeneric
from risk_management.models import Buildings


# Las respuestas de RequestFactory no se renderizan: basta con context_data,
# así que la plantilla no necesita existir.
class _MuestraContexto:
    """En vez de redirigir tras guardar, devuelve el contexto para inspeccionarlo."""

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class _Crear(_MuestraContexto, djgeneric.CreateView):
    model = Provider
    fields = ["name"]
    template_name = "no_se_renderiza.html"
    success_url = "/"


class _Editar(_MuestraContexto, djgeneric.UpdateView):
    model = Provider
    fields = ["name"]
    template_name = "no_se_renderiza.html"
    success_url = "/"


class _Borrar(djgeneric.DeleteView):
    model = Provider
    template_name = "no_se_renderiza.html"
    success_url = "/"


class _Listar(djgeneric.ListView):
    model = Provider
    template_name = "no_se_renderiza.html"


class _Detalle(djgeneric.DetailView):
    model = Provider
    template_name = "no_se_renderiza.html"


class _ReporteSinPlantilla(djgeneric.ReportListView):
    model = Laboratory
    template_name = "no_se_renderiza.html"
    file_name = "laboratorios"

    def get_book(self, context):
        return [["Nombre"]] + [[lab.name] for lab in context["object_list"]]


class _Reporte(_ReporteSinPlantilla):
    pdf_template = "pdf/hcode_pdf.html"


class DjGenericAccesoTest(BaseLaboratorySetUpTest):
    """Usuario miembro de la org pero sin perfil: pasa
    `user_is_allowed_on_organization` y cae en `check_user_access_kwargs_org_lab`."""

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.sin_perfil = get_user_model().objects.create_user(
            username="sinperfil", password="x"
        )
        self.org.users.add(self.sin_perfil)
        self.provider = Provider.objects.first()
        self.building = Buildings.objects.create(
            name="Edificio A", organization=self.org, created_by=self.user
        )
        self.otra_org = OrganizationStructure.objects.get(name="Organization Testing")
        self.edificio_ajeno = Buildings.objects.create(
            name="Edificio ajeno", organization=self.otra_org, created_by=self.user
        )

    def _req(self, method="get", user=None, data=None):
        request = getattr(self.factory, method)("/", data or {})
        request.user = user or self.sin_perfil
        return request

    def test_sin_acceso_a_la_org_responde_404_en_todas_las_vistas(self):
        casos = [
            (_Crear, "get", {}),
            (_Crear, "post", {}),
            (_Editar, "get", {"pk": self.provider.pk}),
            (_Editar, "post", {"pk": self.provider.pk}),
            (_Borrar, "get", {"pk": self.provider.pk}),
            (_Borrar, "post", {"pk": self.provider.pk}),
            (_Listar, "get", {}),
        ]
        for vista, metodo, extra in casos:
            with self.subTest(vista=vista.__name__, metodo=metodo):
                with self.assertRaises(Http404):
                    vista.as_view()(self._req(metodo), org_pk=self.org.pk, **extra)

    def test_detalle_y_reporte_con_laboratorio_sin_acceso_responden_404(self):
        for vista, extra in [(_Detalle, {"pk": self.provider.pk}), (_Reporte, {})]:
            with self.subTest(vista=vista.__name__):
                with self.assertRaises(Http404):
                    vista.as_view()(
                        self._req(), org_pk=self.org.pk, lab_pk=self.lab.pk, **extra
                    )

    def test_post_con_edificio_de_la_org_resuelve_el_edificio(self):
        response = _Crear.as_view()(
            self._req("post", data={}),
            org_pk=self.org.pk,
            building_pk=self.building.pk,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["building"], self.building)
        response = _Editar.as_view()(
            self._req("post", data={"name": ""}),
            org_pk=self.org.pk,
            building_pk=self.building.pk,
            pk=self.provider.pk,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["building"], self.building)

    def test_borrar_con_edificio_ajeno_responde_404(self):
        with self.assertRaises(Http404):
            _Borrar.as_view()(
                self._req("post"),
                org_pk=self.org.pk,
                building_pk=self.edificio_ajeno.pk,
                pk=self.provider.pk,
            )
        self.assertTrue(Provider.objects.filter(pk=self.provider.pk).exists())


class ReportListViewFormatosTest(BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def _get(self, vista, formato):
        request = self.factory.get("/", {"format": formato})
        request.user = self.user
        return vista.as_view()(request, org_pk=self.org.pk)

    def test_exporta_hojas_de_calculo(self):
        for formato in ["xls", "xlsx", "ods"]:
            with self.subTest(formato=formato):
                response = self._get(_Reporte, formato)
                self.assertEqual(response.status_code, 200)
                self.assertIn(
                    "laboratorios.%s" % formato, response["Content-Disposition"]
                )

    def test_exporta_pdf(self):
        response = self._get(_Reporte, "pdf")
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn('filename="laboratorios.pdf"', response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_formato_desconocido_responde_404(self):
        with self.assertRaises(Http404):
            self._get(_Reporte, "docx")

    def test_pdf_sin_plantilla_falla_explicitamente(self):
        with self.assertRaises(RuntimeError):
            self._get(_ReporteSinPlantilla, "pdf")


class ResultQueryElementTest(BaseLaboratorySetUpTest):

    def test_expone_las_claves_como_atributos(self):
        elemento = djgeneric.ResultQueryElement({"nombre": "Ácido", "cantidad": 3})
        self.assertEqual(elemento.nombre, "Ácido")
        self.assertEqual(elemento.cantidad, 3)
        self.assertIsNone(elemento.inexistente)
