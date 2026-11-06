from laboratory.models import Furniture, Laboratory, LaboratoryRoom, Object
from report.forms import (
    CompatibilityReportForm,
    HazardMapReportForm,
    OrganizationReactiveForm,
    PrecursorFilterForm,
    PrecursorReportValuesViewForm,
    RiskZoneReportForm,
    TasksForm,
    ValidateFurnitureForm,
    ValidateLaboratoryRoomReportForm,
    ValidateObjectTypeForm,
)
from report.tests.utils import ReportTestBase
from risk_management.models import Buildings, RiskZone, ZoneType
from sga.models import SubstanceCharacteristics


class ReportFormsTest(ReportTestBase):
    """Validación de los formularios que reciben los parámetros del reporte."""

    def base(self, **extra):
        data = {
            "name": "Mi Reporte",
            "title": "Título",
            "organization": self.org.pk,
            "report_name": "x",
            "format": "html",
        }
        data.update(extra)
        return data

    def test_sala_y_mueble_elegidos_se_respetan(self):
        sala = LaboratoryRoom.objects.get(pk=2)
        mueble = Furniture.objects.filter(labroom=sala).first()
        form = ValidateLaboratoryRoomReportForm(
            self.base(laboratory=[self.lab.pk], lab_room=[sala.pk], furniture=[mueble.pk]),
            org_pk=self.org.pk, user=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["lab_room"], [sala.pk])
        self.assertEqual(form.cleaned_data["furniture"], [mueble.pk])
        self.assertEqual(form.cleaned_data["name"], "mi-reporte")

    def test_sin_laboratorio_usa_los_del_usuario(self):
        form = ValidateLaboratoryRoomReportForm(self.base(), org_pk=self.org.pk, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIn(self.lab.pk, form.cleaned_data["laboratory"])

    def test_sin_mueble_elegido_usa_todos_los_de_la_sala(self):
        sala = LaboratoryRoom.objects.get(pk=2)
        form = ValidateLaboratoryRoomReportForm(
            self.base(laboratory=[self.lab.pk], lab_room=[sala.pk]), org_pk=self.org.pk, user=self.user
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            set(form.cleaned_data["furniture"]),
            set(Furniture.objects.filter(labroom=sala).values_list("pk", flat=True)),
        )

    def test_mueble_de_otra_sala_se_descarta(self):
        sala = LaboratoryRoom.objects.get(pk=2)
        otro_mueble = Furniture.objects.exclude(labroom=sala).first()
        form = ValidateLaboratoryRoomReportForm(
            self.base(laboratory=[self.lab.pk], lab_room=[sala.pk], furniture=[otro_mueble.pk]),
            org_pk=self.org.pk, user=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["furniture"], [])

    def test_laboratorio_no_permitido_es_error_de_validacion(self):
        form = ValidateLaboratoryRoomReportForm(
            self.base(laboratory=[999999], lab_room=[2]), org_pk=self.org.pk, user=self.user
        )
        self.assertFalse(form.is_valid())
        self.assertIn("laboratory", form.errors)

    def test_sala_de_otro_laboratorio_se_descarta(self):
        otro = Laboratory.objects.create(name="Otro lab", organization=self.org)
        sala_ajena = LaboratoryRoom.objects.create(name="Sala ajena", laboratory=otro)
        form = ValidateLaboratoryRoomReportForm(
            self.base(laboratory=[self.lab.pk], lab_room=[sala_ajena.pk]),
            org_pk=self.org.pk, user=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["lab_room"], [])

    def test_usuarios_elegidos_se_guardan_como_pk_de_usuario(self):
        form = OrganizationReactiveForm(
            self.base(users=[self.user.profile.pk]), org_pk=self.org.pk
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["users"], [self.user.pk])

    def test_tipo_de_objeto(self):
        self.assertTrue(ValidateObjectTypeForm({"type_id": "0"}).is_valid())
        form = ValidateObjectTypeForm({"type_id": "7"})
        self.assertFalse(form.is_valid())
        self.assertIn("type_id", form.errors)

    def test_mueble_requiere_organizacion(self):
        """Sin organización el formulario es inválido, no un KeyError."""
        form = ValidateFurnitureForm({"furniture": 1}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("organization", form.errors)
        self.assertIn("furniture", form.errors)

    def test_mueble_de_otro_laboratorio_no_se_acepta(self):
        # La sala 3 es del laboratorio 2; se le copia un mueble.
        mueble_lab_2 = Furniture.objects.get(pk=1)
        mueble_lab_2.pk = None
        mueble_lab_2.labroom = LaboratoryRoom.objects.get(pk=3)
        mueble_lab_2.save()
        form = ValidateFurnitureForm(
            {"furniture": mueble_lab_2.pk, "laboratory": [self.lab.pk]},
            org_pk=self.org.pk, user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("furniture", form.errors)

        valido = ValidateFurnitureForm(
            {"furniture": 1, "laboratory": [self.lab.pk]}, org_pk=self.org.pk, user=self.user
        )
        self.assertTrue(valido.is_valid(), valido.errors)
        self.assertEqual(valido.cleaned_data["laboratory"], [self.lab.pk])

    def test_tarea_inexistente(self):
        form = TasksForm({"task": "t", "taskreport": 999999})
        self.assertFalse(form.is_valid())
        self.assertIn("taskreport", form.errors)

    def test_zonas_y_edificios_elegidos(self):
        tipo = ZoneType.objects.create(name="Lab")
        edificio = Buildings.objects.create(name="E", organization=self.org)
        zona = RiskZone.objects.create(
            name="Z", organization=self.org, num_workers=1, zone_type=tipo
        )
        datos = self.base(risk_zone=[zona.pk], building=[edificio.pk])
        for form_class in (RiskZoneReportForm, CompatibilityReportForm):
            with self.subTest(form=form_class.__name__):
                form = form_class(datos, org_pk=self.org.pk, user=self.user)
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.cleaned_data["risk_zone"], [zona.pk])
                self.assertEqual(form.cleaned_data["building"], [edificio.pk])

        ajeno = Buildings.objects.create(name="Ajeno", organization=self.foreign_org)
        form = RiskZoneReportForm(
            self.base(building=[ajeno.pk]), org_pk=self.org.pk, user=self.user
        )
        self.assertFalse(form.is_valid())

    def test_mapa_de_peligros_con_laboratorio(self):
        form = HazardMapReportForm(
            self.base(laboratory=[self.lab.pk]), org_pk=self.org.pk, user=self.user
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["laboratory"], [self.lab.pk])

    def test_filtro_de_precursores_sin_organizacion(self):
        form = PrecursorFilterForm(user=self.user)
        self.assertIsNone(form.fields["organization"].initial)

    def test_valores_de_precursor_solo_ofrecen_precursores_de_la_organizacion(self):
        cal = Object.objects.get(pk=2)
        SubstanceCharacteristics.objects.filter(object_related=cal).update(is_precursor=True)
        form = PrecursorReportValuesViewForm(org_pk=self.org.pk)
        self.assertIn(cal, form.fields["object"].queryset)
        ajena = PrecursorReportValuesViewForm(org_pk=self.foreign_org.pk)
        self.assertNotIn(cal, ajena.fields["object"].queryset)
