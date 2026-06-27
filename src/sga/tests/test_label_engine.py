# -*- coding: utf-8 -*-
"""Tests del motor de etiquetas y la capa de mapeo Organilab → LabelBlueprint."""
from types import SimpleNamespace

from django.test import SimpleTestCase, TestCase

from sga.label_engine import LabelBlueprint, LabelEngine, LabelTooSmallError
from sga.label_blueprint import (
    capacity_to_ml,
    capacity_to_size_mm,
    recipient_size_to_mm,
    resolver_pictogramas,
    resolver_palabra_advertencia,
    blueprint_from_shelfobject,
)


def _qs(items):
    """Pequeño doble de queryset: expone ``.all()`` devolviendo ``items``."""
    return SimpleNamespace(all=lambda: list(items))


def _danger(code, description, warning=None, prudence=()):
    return SimpleNamespace(
        code=code,
        description=description,
        warning_words=warning,
        prudence_advice=_qs(prudence),
    )


class LabelEnginePureTest(SimpleTestCase):
    """Pruebas sin base de datos: motor y helpers puros."""

    def _full_blueprint(self, **over):
        data = {
            "nombre": "Ácido Clorhídrico", "formula": "HCl", "cas": "7647-01-0",
            "simbolos": ["Corrosivo"], "palabra_advertencia": "PELIGRO",
            "frases_peligro": "H314", "consejos_prudencia": "P280",
        }
        data.update(over)
        bp = LabelBlueprint.from_dict(data)
        bp.ancho_mm, bp.alto_mm = over.get("ancho_mm", 70), over.get("alto_mm", 40)
        return bp

    def test_engine_generates_png(self):
        img = LabelEngine().generate(self._full_blueprint())
        self.assertEqual(img.mode, "RGB")
        self.assertGreater(img.size[0], 0)

    def test_engine_generates_svg(self):
        svg = LabelEngine().generate_svg(self._full_blueprint())
        self.assertIn("<svg", svg)

    def test_container_color_accent_in_svg(self):
        bp = self._full_blueprint(recipiente_nombre="Estante A", recipiente_color="#1ABB9C")
        svg = LabelEngine().generate_svg(bp)
        self.assertIn("#1ABB9C", svg)

    def test_too_small_label_raises(self):
        bp = self._full_blueprint(ancho_mm=20, alto_mm=12)
        with self.assertRaises(LabelTooSmallError):
            LabelEngine().generate(bp)

    def test_resolver_pictogramas(self):
        self.assertEqual(resolver_pictogramas(["H314"]), ["Corrosivo"])
        self.assertEqual(resolver_pictogramas(["H225"]), ["Inflamable"])
        self.assertEqual(resolver_pictogramas(["ZZZ"]), [])

    def test_resolver_palabra_advertencia_priority(self):
        peligro = SimpleNamespace(name="Peligro")
        atencion = SimpleNamespace(name="Atención")
        self.assertEqual(resolver_palabra_advertencia([atencion, peligro]), "PELIGRO")
        self.assertEqual(resolver_palabra_advertencia([atencion]), "ATENCIÓN")
        self.assertEqual(resolver_palabra_advertencia([]), "")

    def test_capacity_to_ml(self):
        self.assertEqual(capacity_to_ml(1, SimpleNamespace(description="L")), 1000.0)
        self.assertEqual(capacity_to_ml(250, SimpleNamespace(description="mL")), 250.0)
        self.assertIsNone(capacity_to_ml(None, SimpleNamespace(description="mL")))
        self.assertIsNone(capacity_to_ml(5, SimpleNamespace(description="kg")))

    def test_capacity_to_size_mm_tiers(self):
        self.assertEqual(capacity_to_size_mm(30), (50, 30))
        self.assertEqual(capacity_to_size_mm(250), (70, 40))
        self.assertEqual(capacity_to_size_mm(1500), (100, 60))
        self.assertEqual(capacity_to_size_mm(5000), (120, 80))
        self.assertEqual(capacity_to_size_mm(None), (70, 40))

    def test_recipient_size_to_mm(self):
        rs = SimpleNamespace(width=5, width_unit="cm", height=3, height_unit="cm")
        self.assertEqual(recipient_size_to_mm(rs), (50.0, 30.0))


class BlueprintFromShelfObjectTest(SimpleTestCase):
    """Verifica herencia de color del contenedor y tamaño por capacidad (sin DB)."""

    def _shelfobject(self, *, shelf_color="#123456", furniture_color="#999999",
                     capacity=250, capacity_unit="mL"):
        chars = SimpleNamespace(
            molecular_formula="HCl", cas_id_number="7647-01-0",
            h_code=_qs([_danger("H314", "Provoca quemaduras",
                                warning=SimpleNamespace(name="Peligro"),
                                prudence=[SimpleNamespace(code="P280", name="Use guantes")])]),
        )
        material_capacity = SimpleNamespace(
            capacity=capacity,
            capacity_measurement_unit=SimpleNamespace(description=capacity_unit),
        )
        obj = SimpleNamespace(name="Ácido Clorhídrico",
                              sustancecharacteristics=chars,
                              materialcapacity=material_capacity)
        furniture = SimpleNamespace(color=furniture_color)
        shelf = SimpleNamespace(name="Estante A-3", color=shelf_color, furniture=furniture)
        return SimpleNamespace(
            object=obj, shelf=shelf, quantity=200,
            measurement_unit=SimpleNamespace(description="mL"),
            batch="L-2026", reactive_expiration_date=None, physical_status="liquid",
            in_where_laboratory=SimpleNamespace(name="Lab Química"),
            container_id=None, container=None, shelf_object_url="https://x/1",
        )

    def test_inherits_shelf_color(self):
        bp = blueprint_from_shelfobject(self._shelfobject())
        self.assertEqual(bp.recipiente_color, "#123456")
        self.assertEqual(bp.recipiente_nombre, "Estante A-3")

    def test_falls_back_to_furniture_color(self):
        bp = blueprint_from_shelfobject(self._shelfobject(shelf_color=""))
        self.assertEqual(bp.recipiente_color, "#999999")

    def test_size_from_capacity(self):
        bp = blueprint_from_shelfobject(self._shelfobject(capacity=250))
        self.assertEqual((bp.ancho_mm, bp.alto_mm), (70, 40))
        bp = blueprint_from_shelfobject(self._shelfobject(capacity=30))
        self.assertEqual((bp.ancho_mm, bp.alto_mm), (50, 30))

    def test_ghs_fields_and_render(self):
        bp = blueprint_from_shelfobject(self._shelfobject())
        self.assertEqual(bp.palabra_advertencia, "PELIGRO")
        self.assertIn("Corrosivo", bp.simbolos)
        self.assertEqual(bp.estado_fisico, "l")
        # Debe renderizar sin error a su tamaño derivado.
        self.assertEqual(LabelEngine().generate(bp).mode, "RGB")


class BlueprintFromSubstanceTest(TestCase):
    """Prueba la ruta de catálogo con datos reales (fixtures)."""

    fixtures = ["substances.json"]

    def test_blueprint_from_substance(self):
        from sga.models import Substance

        substance = Substance.objects.first()
        bp = blueprint_from_substance_safe(substance)
        self.assertTrue(bp.nombre)
        # Renderiza a tamaño por defecto sin fallar.
        self.assertEqual(LabelEngine().generate(bp).mode, "RGB")


def blueprint_from_substance_safe(substance):
    """Envoltura que inyecta dimensiones por defecto para el test de render."""
    from sga.label_blueprint import blueprint_from_substance

    return blueprint_from_substance(substance)
