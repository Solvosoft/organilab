from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from laboratory.models import Laboratory
from report.models import TaskReport
from report.views.discard_objects import report_discard_object_doc
from report.views.furniture import (
    furniture_doc,
    furniture_html,
    get_dataset,
    get_dataset_report_reactive,
)
from report.views.objects import (
    get_dataset_reactive_precursor,
    get_dataset_report_organization_reactive,
)
from sga.models import SubstanceCharacteristics


class ReactivePrecursorDatasetTest(TestCase):
    """Blinda el filtro del reporte regulatorio de precursores.

    Es un informe con valor regulatorio, así que un filtro invertido no da un
    resultado raro: da uno creíble y equivocado, que es peor. Se comprueba la
    propiedad —toda fila es precursora— y no filas concretas, para que el test
    siga siendo válido si la fixture evoluciona.
    """

    fixtures = ["laboratory_data.json"]

    def build_report(self):
        return SimpleNamespace(data={"organization": 1, "laboratory": [1]})

    def test_dataset_only_contains_precursors(self):
        # Se pide una sola columna para no depender del orden del resto.
        dataset = get_dataset_reactive_precursor(
            self.build_report(), column_list=["precursor"]
        )
        self.assertTrue(dataset, "el reporte no devolvió ninguna fila")
        for row in dataset:
            self.assertEqual(str(row[0]), "Yes", row)

    def test_dataset_is_empty_without_precursors(self):
        SubstanceCharacteristics.objects.update(is_precursor=False)
        dataset = get_dataset_reactive_precursor(
            self.build_report(), column_list=["precursor"]
        )
        self.assertEqual(dataset, [])


class OrganizationReactiveDatasetTest(TestCase):
    """El reporte lee las características desde SGA, la fuente de verdad.

    Un objeto dado de alta por el asistente solo tiene características en SGA, de
    modo que leerlas del modelo obsoleto daría informes vacíos o rotos según el
    origen del dato. La fixture reproduce ese caso.
    """

    fixtures = ["laboratory_data.json"]

    def build_report(self):
        return SimpleNamespace(data={"organization": 1})

    def test_dataset_reads_characteristics_from_sga(self):
        dataset = get_dataset_report_organization_reactive(
            self.build_report(), column_list=["cas"]
        )
        self.assertTrue(dataset, "el reporte no devolvió ninguna fila")
        self.assertEqual(str(dataset[0][0]), "7681-52-9")

    def test_dataset_does_not_depend_on_the_legacy_model(self):
        """El informe no depende de que el modelo obsoleto tenga datos."""
        from laboratory.models import SustanceCharacteristics

        self.assertEqual(SustanceCharacteristics.objects.count(), 0)
        self.assertTrue(
            get_dataset_report_organization_reactive(
                self.build_report(), column_list=["cas"]
            )
        )


@override_settings(MEDIA_ROOT="/tmp/organilab-test-media")
class FurnitureReportWithoutObjectTypeTest(TestCase):
    """Un reporte guardado sin `object_type` debe poder regenerarse.

    El payload se conserva tal como estaba el día que se pidió el informe, así
    que puede carecer de claves que el código espera. Un reporte guardado es una
    promesa de poder volver a generarlo: si una clave ausente tumba la tarea, esa
    promesa se rompe para siempre, porque el payload ya no se puede cambiar.
    """

    fixtures = ["laboratory_data.json"]

    def build_report(self, file_type="xls"):
        return TaskReport.objects.create(
            created_by=User.objects.first(),
            type_report="report_furniture",
            file_type=file_type,
            # Sin `object_type`: el caso que debe seguir siendo regenerable.
            data={
                "name": "reporte-antiguo",
                "title": "Reporte de Objetos por Muebles",
                "organization": 1,
                "laboratory": [1],
            },
            language="es",
        )

    def test_dataset_without_object_type_does_not_raise(self):
        self.assertIsInstance(get_dataset(self.build_report()), list)

    def test_reactive_dataset_without_object_type_does_not_raise(self):
        self.assertIsInstance(
            get_dataset_report_reactive(self.build_report()), list
        )

    def test_html_without_object_type_generates_content(self):
        report = self.build_report(file_type="html")
        furniture_html(report)
        report.refresh_from_db()
        self.assertIn("columns", report.table_content)

    def test_doc_without_object_type_generates_a_file(self):
        report = self.build_report(file_type="xls")
        furniture_doc(report)
        report.refresh_from_db()
        self.assertTrue(report.file)

    def test_missing_object_type_means_every_type(self):
        """Ausencia de tipo equivale a «sin filtro», el comportamiento neutro."""
        sin_tipo = get_dataset(self.build_report())
        report = self.build_report()
        report.data = dict(report.data, object_type="")
        report.save(update_fields=["data"])
        self.assertEqual(sin_tipo, get_dataset(report))


@override_settings(MEDIA_ROOT="/tmp/organilab-test-media")
class DiscardObjectsReportWithDeletedLabTest(TestCase):
    """Un laboratorio borrado no debe tumbar el reporte entero.

    El payload guarda los pks elegidos el día que se pidió el informe, y un
    laboratorio puede desaparecer después. Exigir que todos existan convierte un
    informe parcialmente posible en ninguno; la variante HTML los filtra, y ambas
    deben coincidir.
    """

    fixtures = ["laboratory_data.json"]

    def build_report(self, labs):
        return TaskReport.objects.create(
            created_by=User.objects.first(),
            type_report="report_waste_objects",
            file_type="xls",
            data={
                "name": "informe-de-desechos",
                "title": "Informe de objetos desechados por estante",
                "organization": 1,
                "laboratory": labs,
                "period": "",
            },
            language="es",
        )

    def test_report_skips_laboratories_that_no_longer_exist(self):
        vivo = Laboratory.objects.first()
        borrado = Laboratory.objects.create(
            name="Se borrará", organization=vivo.organization
        )
        pk_borrado = borrado.pk
        borrado.delete()

        report = self.build_report([vivo.pk, pk_borrado])
        report_discard_object_doc(report)

        report.refresh_from_db()
        self.assertTrue(report.file)

    def test_report_with_only_deleted_laboratories_still_generates(self):
        vivo = Laboratory.objects.first()
        borrado = Laboratory.objects.create(
            name="Se borrará", organization=vivo.organization
        )
        pk_borrado = borrado.pk
        borrado.delete()

        report = self.build_report([pk_borrado])
        report_discard_object_doc(report)

        report.refresh_from_db()
        self.assertTrue(report.file)
