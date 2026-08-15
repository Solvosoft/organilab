from django.test import TestCase

from laboratory.models import Laboratory, OrganizationStructure
from sga.models import Substance
from sga.substance_codes import (
    build_lot_code,
    build_substance_code,
    parse_lot_code,
    suggest_code,
)


class SuggestCodeTest(TestCase):
    """Derivación de la sigla de tres letras.

    La sigla que el nombre ya declara entre paréntesis manda; si no la hay, se
    compone con las iniciales de las palabras que distinguen a esa unidad.
    """

    def test_uses_the_acronym_already_in_the_name(self):
        """Quien escribió una sigla en el nombre ya eligió cómo se llama."""
        nombre = "Centro de Investigación en Biotecnología (CIB)"
        self.assertEqual(suggest_code(nombre), "CIB")

    def test_two_words_take_two_letters_plus_one(self):
        self.assertEqual(suggest_code("Química General"), "QUG")

    def test_ignores_the_generic_word(self):
        """La sigla debe distinguir, y el genérico lo comparten muchos nombres."""
        self.assertEqual(suggest_code("Laboratorio de Química General"), "QUG")
        self.assertNotEqual(suggest_code("Laboratorio de Biología"), "LAB")

    def test_single_word_takes_three_letters(self):
        self.assertEqual(suggest_code("Química"), "QUI")

    def test_strips_accents(self):
        self.assertEqual(suggest_code("Anatomía"), "ANA")

    def test_resolves_collisions(self):
        primera = suggest_code("Química")
        segunda = suggest_code("Química", taken=[primera])
        tercera = suggest_code("Química", taken=[primera, segunda])
        self.assertNotIn(segunda, (primera,))
        self.assertEqual(len({primera, segunda, tercera}), 3)

    def test_name_without_letters_gives_nothing(self):
        self.assertIsNone(suggest_code("---"))

    def test_short_name_is_padded(self):
        self.assertEqual(len(suggest_code("Li")), 3)


class SubstanceCodeTest(TestCase):
    """La parte estable del código, la que identifica a la sustancia."""

    def setUp(self):
        self.org = OrganizationStructure.objects.create(name="Instituto de Ciencias", code="CIE")
        self.lab = Laboratory.objects.create(
            name="Química General", organization=self.org, code="QUG"
        )
        self.substance = Substance.objects.create(
            comercial_name="Acetona", organization=self.org
        )

    def test_format(self):
        code = build_substance_code(self.lab, self.org, self.substance)
        self.assertEqual(code, f"EQ-QUG-CIE-{self.substance.pk:06d}")

    def test_is_idempotent(self):
        """No lleva consecutivo: reaprobar devuelve el mismo código."""
        primero = build_substance_code(self.lab, self.org, self.substance)
        segundo = build_substance_code(self.lab, self.org, self.substance)
        self.assertEqual(primero, segundo)

    def test_changes_only_the_laboratory_segment(self):
        otro = Laboratory.objects.create(
            name="Física", organization=self.org, code="FIS"
        )
        uno = build_substance_code(self.lab, self.org, self.substance)
        dos = build_substance_code(otro, self.org, self.substance)
        self.assertNotEqual(uno, dos)
        self.assertEqual(uno.replace("QUG", "FIS"), dos)

    def test_without_laboratory_code_there_is_no_code(self):
        self.lab.code = None
        self.assertIsNone(build_substance_code(self.lab, self.org, self.substance))

    def test_without_organization_code_there_is_no_code(self):
        self.org.code = None
        self.assertIsNone(build_substance_code(self.lab, self.org, self.substance))


class LotCodeTest(TestCase):
    """El código completo que se imprime en la etiqueta del envase."""

    def test_format(self):
        completo = build_lot_code("EQ-QUG-CIE-000031", 2026, 8, 1)
        self.assertEqual(completo, "EQ-QUG-CIE-000031-2026-08-0001")

    def test_fits_in_the_field(self):
        """El código crece con los datos; el campo debe admitir el caso extremo."""
        from laboratory.models import ShelfObject

        largo = build_lot_code("EQ-QUG-CIE-1234567", 2026, 12, 9999)
        maximo = ShelfObject._meta.get_field("shelfobject_code").max_length
        self.assertLessEqual(len(largo), maximo)

    def test_round_trip(self):
        datos = parse_lot_code("EQ-QUG-CIE-000031-2026-08-0007")
        self.assertEqual(datos["substance"], 31)
        self.assertEqual(datos["year"], 2026)
        self.assertEqual(datos["month"], 8)
        self.assertEqual(datos["counter"], 7)

    def test_ignores_codes_from_another_scheme(self):
        """Un código con otro formato no debe leerse como si fuera un lote.

        El inventario puede traer códigos escritos con cualquier convención
        anterior; interpretarlos sembraría contadores con números inventados.
        """
        for ajeno in ("A-000001", "F-000024", "TA1000", "", None):
            self.assertIsNone(parse_lot_code(ajeno))
