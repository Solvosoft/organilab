from laboratory.models import Catalog, Furniture, Object, OrganizationStructure
from report.tests.utils import ReportTestBase
from report.views import donation, furniture, lab_room, reactive
from sga.models import DangerIndication, HCodeCategory, SubstanceCharacteristics


def as_rows(report):
    names = [c["name"] for c in report.table_content["columns"]]
    return [dict(zip(names, row)) for row in report.table_content["dataset"]]


class HazardDataMixin:
    """Da a «Cal 100 gr» códigos H de las tres categorías de peligro."""

    def give_hazards(self):
        self.cal = Object.objects.get(pk=2)
        SubstanceCharacteristics.objects.update(is_precursor=False)
        sga = SubstanceCharacteristics.objects.get(object_related=self.cal)
        sga.cas_id_number = "1305-78-8"
        sga.is_precursor = True
        sga.save()
        codes = list(DangerIndication.objects.order_by("code")[:3])
        for code, category in zip(codes, ("physical", "health", "environment")):
            HCodeCategory.objects.create(danger_category=category).h_code.add(code)
        sga.h_code.set(codes)
        return {c: code.description for c, code in zip(("physical", "health", "environment"), codes)}


class FurnitureReportTest(HazardDataMixin, ReportTestBase):
    def furniture_report(self, file_type="html", **data):
        data.setdefault("furniture", [1])
        return self.make_report("report_furniture", file_type, **data)

    def test_html_filtrado_por_tipo_material(self):
        report = self.furniture_report(object_type="1")
        furniture.furniture_html(report)
        report.refresh_from_db()
        filas = as_rows(report)
        self.assertTrue(filas)
        self.assertEqual({f["type"] for f in filas}, {"Material"})
        self.assertEqual({f["furniture"] for f in filas}, {"Mueble 1"})

    def test_reactivos_muestran_peligros_por_categoria(self):
        peligros = self.give_hazards()
        self.make_shelfobject(self.cal, physical_status="liquid")
        report = self.furniture_report(object_type="0", is_precursor=True)
        total = furniture.furniture_html(report)
        report.refresh_from_db()
        filas = as_rows(report)
        self.assertEqual(total, len(filas))
        self.assertEqual({f["name"] for f in filas}, {self.cal.name})
        liquido = [f for f in filas if f["physical_status"] == "Liquid"][0]
        self.assertEqual(liquido["physical"], peligros["physical"])
        self.assertEqual(liquido["health"], peligros["health"])
        self.assertEqual(liquido["environment"], peligros["environment"])
        self.assertEqual(liquido["cas_id"], "1305-78-8")
        self.assertEqual(liquido["location"], self.lab.location)

    def test_reactivos_sin_tipo_incluye_todo(self):
        report = self.furniture_report(object_type="0")
        report.data["object_type"] = ""
        sin_tipo = furniture.get_dataset_report_reactive(report)
        self.assertEqual(
            len(sin_tipo), Furniture.objects.get(pk=1).get_objects().count()
        )

    def test_documentos(self):
        material = self.furniture_report("xlsx", object_type="1")
        total = furniture.furniture_doc(material)
        filas = self.read_xlsx(material)
        self.assertEqual(len(filas) - 2, total)
        self.assertEqual(filas[2][3], "Material")

        self.give_hazards()
        reactivos = self.furniture_report("xlsx", object_type="0")
        total = furniture.furniture_doc(reactivos)
        filas = self.read_xlsx(reactivos)
        self.assertEqual(len(filas) - 2, total)
        self.assertEqual(len(filas[1]), 14)


class LabRoomReportTest(HazardDataMixin, ReportTestBase):
    """El fixture tiene una unidad sin `in_where_laboratory` en la sala 1.

    El campo es opcional en el modelo: el reporte por mueble ya lo contemplaba
    y el de sala tiraba AttributeError, dejando al usuario sin informe.
    """

    def test_html_filtra_precursores_reactivos(self):
        self.give_hazards()
        report = self.make_report(
            "report_laboratory_room", "html", object_type="0", is_precursor=True,
            lab_room=[1],
        )
        lab_room.lab_room_html(report)
        report.refresh_from_db()
        self.assertEqual({f["object"] for f in as_rows(report)}, {self.cal.name})

    def test_documento_sin_tipo(self):
        report = self.make_report("report_laboratory_room", "xlsx", lab_room=[1])
        total = lab_room.lab_room_doc(report)
        filas = self.read_xlsx(report)
        self.assertEqual(len(filas) - 2, total)
        self.assertGreater(total, 0)
        self.assertEqual(filas[2][3], self.lab.name)


class ReactiveReportTest(HazardDataMixin, ReportTestBase):
    def test_un_laboratorio(self):
        peligros = self.give_hazards()
        report = self.make_report("reactive_report", "html")
        reactive.report_reactive_html(report)
        report.refresh_from_db()
        cal = [f for f in as_rows(report) if f["name"] == self.cal.name]
        self.assertTrue(cal)
        self.assertEqual(cal[0]["health"], peligros["health"])
        self.assertEqual(cal[0]["in_where_laboratory__name"], self.lab.name)

    def test_varios_laboratorios_en_documento(self):
        self.give_hazards()
        report = self.make_report("reactive_report", "xlsx", laboratory=[1, 2])
        total = reactive.report_reactive_list_doc(report)
        filas = self.read_xlsx(report)
        self.assertEqual(len(filas) - 2, total)
        self.assertEqual({f[3] for f in filas[2:] if f[2] == self.cal.name}, {"1305-78-8"})


class DonationReportTest(ReportTestBase):
    def setUp(self):
        super().setUp()
        self.cal = Object.objects.get(pk=2)
        self.estado = Catalog.objects.create(key="shelfobject_status", description="Nuevo")
        self.make_shelfobject(self.cal, quantity=3, was_donated=True, status=self.estado)
        self.make_shelfobject(
            self.cal, quantity=2, was_donated=True, is_box=True,
            quantity_units=[{"units": 4, "quantity": 1}, {"units": 6, "quantity": 1}],
        )
        self.make_shelfobject(self.cal, quantity=9)

    def test_html_solo_donaciones(self):
        report = self.make_report("donations_report", "html")
        self.assertEqual(donation.report_donations_html(report), 2)
        report.refresh_from_db()
        filas = {f["quantity"]: f for f in as_rows(report)}
        self.assertEqual(filas[3]["status"], "Nuevo")
        self.assertEqual(filas[3]["unit"], str(self.unit()))
        self.assertEqual(filas[2]["unit"], "(10) units per box")
        self.assertEqual(filas[2]["status"], "")
        self.assertIn("Box of", filas[2]["object"])

    def test_documento(self):
        report = self.make_report("donations_report", "xlsx")
        self.assertEqual(donation.report_donations_doc(report), 2)
        filas = self.read_xlsx(report)
        self.assertEqual({f[1] for f in filas[2:]}, {self.cal.code})

    def test_organizacion_sin_laboratorios(self):
        """`ReportForm` deja la lista vacía cuando la organización no tiene laboratorios.

        El dataset recibía el pk de la organización como entero y le pedía sus
        laboratorios: AttributeError y la tarea moría sin informe.
        """
        vacia = OrganizationStructure.objects.create(name="Sin laboratorios")
        report = self.make_report(
            "donations_report", "html", organization=vacia.pk, laboratory=[]
        )
        self.assertEqual(donation.report_donations_html(report), 0)

    def test_sin_laboratorios_usa_los_de_la_organizacion(self):
        report = self.make_report("donations_report", "html", laboratory=[])
        self.assertEqual(donation.report_donations_html(report), 2)
