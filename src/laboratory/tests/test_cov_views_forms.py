# encoding: utf-8
"""Validaciones de ``laboratory/forms.py`` que el recorrido web no alcanza.

Parte por la vista (objetos con ``?type_id=`` y la capacidad del material) y
parte instanciando el formulario: organizaciones inactivas, el código de un QR
ya emitido, la carga masiva de reactivos y la solicitud de laboratorio u
organización.
"""

from django.urls import reverse

from laboratory.forms import (
    AddOrganizationForm,
    ChangeOrganizationParentForm,
    InformForm,
    LabOrOrgRequestForm,
    ObjectMaterialForm,
    ReactiveStockForm,
    ReactiveUploadForm,
    RegisterUserQRForm,
    RelOrganizationPKIntForm,
    ReservationModalForm,
)
from laboratory.models import (
    Catalog,
    LabOrOrgRequest,
    MaterialCapacity,
    Object,
    OrganizationStructure,
    Shelf,
)
from laboratory.tests.test_cov_views_laboratory import RegisterUserQRBaseTest
from laboratory.tests.utils import BaseLaboratorySetUpTest


class ObjectFormPorTipoTest(BaseLaboratorySetUpTest):
    """``?type_id=`` fija el tipo del formulario de objetos al crear y al editar."""

    def url(self, name, **kwargs):
        kwargs.update({"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        return reverse("laboratory:" + name, kwargs=kwargs)

    def test_crear_material_con_tipo_en_la_consulta(self):
        response = self.client.get(self.url("objectview_create"), {"type_id": Object.MATERIAL})
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertEqual(form.fields["type"].initial, Object.MATERIAL)
        self.assertIn("capacity", form.fields)

    def test_editar_material_contenedor_precarga_su_capacidad(self):
        material = Object.objects.get(pk=4)
        MaterialCapacity.objects.create(
            object=material, capacity=125, capacity_measurement_unit_id=64
        )
        response = self.client.get(
            self.url("objectview_update", pk=material.pk), {"type_id": Object.MATERIAL}
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertEqual(form.fields["object"].initial, material.pk)
        self.assertEqual(form.fields["capacity"].initial, 125)
        self.assertEqual(form.fields["capacity_measurement_unit"].initial, 64)

    def test_editar_equipo_exige_modelo(self):
        equipo = Object.objects.get(pk=8)
        response = self.client.get(
            self.url("objectview_update", pk=equipo.pk), {"type_id": Object.EQUIPMENT}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].fields["model"].required)

    def test_contenedor_sin_unidad_de_capacidad_no_se_guarda(self):
        material = Object.objects.get(pk=5)
        response = self.client.post(
            self.url("objectview_update", pk=material.pk),
            {
                "name": material.name,
                "code": "B300",
                "is_public": True,
                "type": Object.MATERIAL,
                "is_container": True,
                "capacity": 5,
                "features": [1],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("capacity_measurement_unit", response.context["form"].errors)
        self.assertFalse(MaterialCapacity.objects.filter(object=material).exists())


class FormulariosDeOrganizacionTest(BaseLaboratorySetUpTest):

    def setUp(self):
        super().setUp()
        self.inactiva = OrganizationStructure.objects.create(name="Inactiva", active=False)

    def test_padre_inactivo_no_se_acepta(self):
        form = AddOrganizationForm(data={"name": "Hija", "parent": self.inactiva.pk})
        self.assertFalse(form.is_valid())
        self.assertIn("Organization parent cannot be inactive", form.non_field_errors())

    def test_relacionar_con_organizacion_inactiva(self):
        form = RelOrganizationPKIntForm(data={"organization": self.inactiva.pk})
        self.assertFalse(form.is_valid())
        self.assertIn("organization", form.errors)

    def test_no_se_cambia_el_padre_de_una_organizacion_inactiva(self):
        form = ChangeOrganizationParentForm(
            data={"parent": self.org.pk}, instance=self.inactiva
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Organization cannot be inactive", form.non_field_errors())


class FormulariosSinContextoTest(BaseLaboratorySetUpTest):

    def test_informe_sin_organizacion_no_ofrece_formularios(self):
        form = InformForm()
        self.assertFalse(form.fields["custom_form"].queryset.exists())
        self.assertTrue(form.fields["custom_form"].required)

    def test_reserva_explica_las_fechas(self):
        form = ReservationModalForm()
        self.assertTrue(form.fields["initial_date"].help_text)
        self.assertTrue(form.fields["final_date"].help_text)

    def test_stock_acepta_laboratorio_y_filtra_reactivos_de_la_organizacion(self):
        form = ReactiveStockForm(laboratory=self.lab.pk, organization=self.org.pk)
        tipos = set(form.fields["object"].queryset.values_list("type", flat=True))
        self.assertEqual(tipos, {Object.REACTIVE})

    def test_material_contenedor_exige_unidad(self):
        form = ObjectMaterialForm(data={"is_container": True, "capacity": 3})
        form.is_valid()
        self.assertIn("capacity_measurement_unit", form.errors)

    def test_material_no_contenedor_descarta_la_capacidad(self):
        form = ObjectMaterialForm(data={"capacity": 3, "capacity_measurement_unit": 64})
        form.is_valid()
        self.assertNotIn("capacity", form.cleaned_data)
        self.assertNotIn("capacity_measurement_unit", form.cleaned_data)


class RegisterUserQRFormTest(RegisterUserQRBaseTest):

    def test_editar_qr_conserva_su_propio_codigo(self):
        """Al editar, el código del propio QR no cuenta como repetido."""
        form = RegisterUserQRForm(
            data={"activate_user": True, "url": ""}, instance=self.qr, obj=self.qr
        )
        form.is_valid()
        self.assertNotIn("code", form.errors)
        self.assertEqual(form.cleaned_data["code"], "Q001")


class ReactiveUploadFormTest(BaseLaboratorySetUpTest):
    """Validación de cada fila de la carga masiva de reactivos."""

    def setUp(self):
        super().setUp()
        self.unidad = Catalog.objects.filter(key="units").first().description
        self.shelf = Shelf.objects.first()

    def datos(self, **extra):
        data = {
            "nombre_producto": "Ácido",
            "cantidad": 1,
            "unidades_cantidad": self.unidad,
            "capacidad_envase": 10,
            "unidades_capacidad": self.unidad,
            "material_contenedor": "Vidrio",
            "unidades_cantidad_maxima": self.unidad,
            "shelf": self.shelf.pk,
        }
        data.update(extra)
        return data

    def test_fila_valida(self):
        form = ReactiveUploadForm(data=self.datos())
        self.assertTrue(form.is_valid(), form.errors)

    def test_unidades_desconocidas_y_cantidad_mayor_al_envase(self):
        form = ReactiveUploadForm(
            data=self.datos(
                cantidad=50,
                unidades_cantidad="Inexistente",
                unidades_capacidad="Inexistente",
                unidades_cantidad_maxima="Inexistente",
            )
        )
        self.assertFalse(form.is_valid())
        for field in [
            "cantidad",
            "unidades_cantidad",
            "unidades_capacidad",
            "unidades_cantidad_maxima",
        ]:
            self.assertIn(field, form.errors)


class LabOrOrgRequestFormTest(BaseLaboratorySetUpTest):

    def form(self, is_org):
        form = LabOrOrgRequestForm(
            data={
                "name": "Solicitud",
                "is_org": is_org,
                "area": "0",
                "workplace": [self.org.pk],
                # Como el navegador: los widgets de archivo siempre envían su input.
                "nearby_sites": "",
                "water_resources_affected": "",
            },
            org_pk=self.org.pk,
        )
        self.assertTrue(form.is_valid(), form.errors)
        return form

    def test_sin_commit_solo_fija_el_tipo(self):
        instance = self.form(is_org=True).save(commit=False)
        self.assertIsNone(instance.pk)
        self.assertEqual(instance.entity_type, LabOrOrgRequest.TYPE_ORGANIZATION)

    def test_guardar_solicitud_de_laboratorio_con_lugares_de_trabajo(self):
        form = self.form(is_org=False)
        form.instance.requested_by = self.user
        instance = form.save()
        self.assertIsNotNone(instance.pk)
        self.assertEqual(instance.entity_type, LabOrOrgRequest.TYPE_LABORATORY)
        self.assertEqual(list(instance.workplace.all()), [self.org])
