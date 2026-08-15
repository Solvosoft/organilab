# -*- coding: utf-8 -*-
"""Tests del motor de etiquetas y la capa de mapeo Organilab → LabelBlueprint."""
from types import SimpleNamespace

from django.test import SimpleTestCase, TestCase

from sga.label_engine import LabelBlueprint, LabelEngine, LabelTooSmallError
from sga.label_engine.phrases_catalog import expand_item, group_codes, parse_codes
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


def _related(items):
    """Doble de related manager: expone ``.first()`` como el ORM."""
    items = list(items)
    return SimpleNamespace(first=lambda: items[0] if items else None)


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
                              substancharacteristics_object=_related([chars]),
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


class CombinedCodesTest(SimpleTestCase):
    """Los códigos combinados son una frase única, se escriban como se escriban.

    En la base de datos se registran con espacios ("P370 + P378"), así que el
    parseo debe tolerarlos sin partir la combinación en códigos sueltos: hacerlo
    dejaba la frase en su encabezado ("EN CASO DE CONTACTO CON LA PIEL:") sin la
    acción de primeros auxilios.
    """

    def test_parses_combined_codes_with_and_without_spaces(self):
        for raw in ("P302+P352", "P302 + P352", "P302+ P352"):
            self.assertEqual(parse_codes(raw), ("P302", "P352"), raw)

    def test_parses_single_code_with_letter_suffix(self):
        self.assertEqual(parse_codes("H360D"), ("H360D",))

    def test_free_text_is_not_a_code(self):
        self.assertEqual(parse_codes("P302 - Lavar con agua"), ())

    def test_combined_code_keeps_the_action(self):
        texto = expand_item("P302 + P352")
        self.assertTrue(texto.startswith("P302+P352 "))
        # No puede quedarse en el encabezado: debe traer la acción.
        self.assertNotEqual(texto.strip(), "P302+P352 EN CASO DE CONTACTO CON LA PIEL:")

    def test_preformed_combination_is_not_regrouped(self):
        groups = group_codes(["P302+P352", "P280"], "P")
        self.assertIn("P302+P352", [c for c, _ in groups])

    def test_loose_codes_are_grouped_into_official_combination(self):
        groups = group_codes(["H312", "H332"], "H")
        self.assertEqual([c for c, _ in groups], ["H312+H332"])


class PhysicalStateTest(SimpleTestCase):
    """El estado físico se imprime una sola vez, junto al nombre."""

    def test_state_is_not_repeated_on_the_formula(self):
        from sga.label_engine.layout.planner import LabelPlanner

        bp = LabelBlueprint(
            nombre="Acetona", formula="C3H6O", cas="67-64-1",
            estado_fisico="Líquido", frases_peligro="H225",
            ancho_mm=70, alto_mm=40,
        )
        layout = LabelPlanner().plan(
            bp, int(70 * 300 / 25.4), int(40 * 300 / 25.4)
        )
        formula = [b for b in layout.boxes if b.element_type == "formula"]
        self.assertTrue(formula)
        self.assertEqual(formula[0].content_ref["estado_suffix"], "")
        name = [b for b in layout.boxes if b.element_type == "name"]
        self.assertIn("Líquido", name[0].content_ref["suffix"])


class LabelSizeSourceTest(SimpleTestCase):
    """El recipiente manda sobre la capacidad y respeta su unidad."""

    def test_recipient_size_converts_from_its_unit(self):
        recipient = SimpleNamespace(width=7, height=4, width_unit="cm", height_unit="cm")
        self.assertEqual(recipient_size_to_mm(recipient), (70.0, 40.0))

    def test_recipient_takes_precedence_over_capacity(self):
        from sga.label_blueprint import _label_size_mm

        recipient = SimpleNamespace(width=7, height=4, width_unit="cm", height_unit="cm")
        shelfobject = SimpleNamespace(
            object=SimpleNamespace(materialcapacity=None), quantity=None,
            measurement_unit=None,
        )
        self.assertEqual(_label_size_mm(shelfobject, recipient), (70.0, 40.0))


class SubstanceNameFallbackTest(SimpleTestCase):
    """Una sustancia en borrador sin nombre comercial hereda el de su organización.

    Sin nombre el blueprint es inválido y la generación caía con ValueError, que
    la vista devolvía como 500.
    """

    def test_falls_back_to_parent_organization_name(self):
        from sga.label_blueprint import _substance_name

        substance = SimpleNamespace(comercial_name="", uipa_name="", organization=None)
        org = SimpleNamespace(name="UNA")
        self.assertEqual(_substance_name(substance, org), "UNA")

    def test_own_name_wins_over_organization(self):
        from sga.label_blueprint import _substance_name

        substance = SimpleNamespace(
            comercial_name="Acetona", uipa_name="", organization=None
        )
        self.assertEqual(_substance_name(substance, SimpleNamespace(name="UNA")), "Acetona")


class RenderLabelErrorsTest(SimpleTestCase):
    """Un blueprint inválido es un 400 (dato del usuario), nunca un 500."""

    def test_invalid_blueprint_returns_400(self):
        from sga.label_render import render_label

        response = render_label(LabelBlueprint(nombre=""), "png")
        self.assertEqual(response.status_code, 400)

    def test_too_small_label_returns_400(self):
        from sga.label_render import render_label

        bp = LabelBlueprint(nombre="Acetona", frases_peligro="H225",
                            ancho_mm=20, alto_mm=12)
        self.assertEqual(render_label(bp, "png").status_code, 400)
