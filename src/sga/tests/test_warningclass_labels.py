"""Las etiquetas de WarningClass sin una consulta por opción."""

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from sga.models import WarningClass
from sga.views.substance.forms import DangerIndicationForm


class WarningClassLabelTest(TestCase):

    def setUp(self):
        self.parent = WarningClass.objects.create(name="Explosivos", danger_type="class")
        self.other = WarningClass.objects.create(name="Gases", danger_type="class")
        WarningClass.objects.create(name="1", parent=self.parent)
        WarningClass.objects.create(name="Categoría A", parent=self.parent)
        WarningClass.objects.create(name="Categoría A", parent=self.other)
        WarningClass.objects.create(name="Única", parent=self.other)

    def labels(self, queryset):
        return {str(item) for item in queryset}

    def test_la_anotacion_da_las_mismas_etiquetas(self):
        self.assertEqual(
            self.labels(WarningClass.objects.labelled()),
            self.labels(WarningClass.objects.all()),
        )
        self.assertIn("Explosivos > 1", self.labels(WarningClass.objects.labelled()))
        self.assertIn("Gases > Categoría A", self.labels(WarningClass.objects.labelled()))
        self.assertIn("Única", self.labels(WarningClass.objects.labelled()))

    def test_el_formulario_no_consulta_por_opcion(self):
        def render_count():
            with CaptureQueriesContext(connection) as captured:
                str(DangerIndicationForm()["warning_class"])
                str(DangerIndicationForm()["warning_category"])
            return len(captured)

        before = render_count()
        for index in range(10):
            WarningClass.objects.create(name="Extra %d" % index, parent=self.parent)
        self.assertEqual(render_count(), before)
