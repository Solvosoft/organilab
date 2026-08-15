# -*- coding: utf-8 -*-
"""Pruebas de la corrección ortográfica del catálogo GHS (migración sga.0097)."""
import importlib

from django.apps import apps as global_apps
from django.test import SimpleTestCase, TestCase

from sga.models import DangerIndication, WarningWord

migration = importlib.import_module("sga.migrations.0097_fix_ghs_phrase_spelling")


class SameWordsTest(SimpleTestCase):
    """Qué se considera una diferencia sólo de forma."""

    def test_accents_and_final_dot_are_cosmetic(self):
        self.assertTrue(
            migration._same_words(
                "Liquido y vapores muy inflamables",
                "Líquido y vapores muy inflamables.",
            )
        )

    def test_different_words_are_not_cosmetic(self):
        self.assertFalse(
            migration._same_words(
                "Puede explotar al calentarse",
                "Peligro de explosión en caso de calentamiento.",
            )
        )

    def test_concatenated_phrases_are_not_cosmetic(self):
        # La base guarda algunas combinaciones como frases pegadas: es una
        # diferencia de estructura, no de ortografía.
        self.assertFalse(
            migration._same_words(
                "Mortal en contacto con la piel\r\nMortal si se inhala",
                "Mortal en contacto con la piel o si se inhala.",
            )
        )

    def test_every_replacement_is_accented_and_closed(self):
        replacements = list(migration.COSMETIC.values()) + [
            new for _, new in migration.SPELLING.values()
        ]
        for text in replacements:
            self.assertTrue(text.endswith(".") or text.endswith(":"), text)

    def test_spelling_entries_declare_the_text_they_replace(self):
        for code, pair in migration.SPELLING.items():
            self.assertEqual(len(pair), 2, code)
            old, new = pair
            self.assertNotEqual(old, new, code)


class FixSpellingTest(TestCase):
    """La migración arregla la forma y respeta el contenido."""

    def setUp(self):
        self.warning_word = WarningWord.objects.create(name="Peligro", weigth=10)

    def _indication(self, code, description):
        # `code` es la clave primaria y las fixtures ya traen el catálogo GHS,
        # así que se reutiliza la fila si existe.
        indication, _ = DangerIndication.objects.update_or_create(
            code=code,
            defaults={
                "description": description,
                "warning_words": self.warning_word,
            },
        )
        return indication

    def _run(self):
        migration.fix_spelling(global_apps, None)

    def test_adds_missing_accent_and_dot(self):
        indication = self._indication("H225", "Liquido y vapores muy inflamables")
        self._run()
        indication.refresh_from_db()
        self.assertEqual(indication.description, "Líquido y vapores muy inflamables.")

    def test_fixes_typo(self):
        indication = self._indication("H205", "Peligro de expasión en masa en caso de incendio")
        self._run()
        indication.refresh_from_db()
        self.assertIn("explosión", indication.description)

    def test_does_not_touch_a_rewritten_description(self):
        rewritten = "Se inflama de inmediato al contacto con el aire ambiente."
        indication = self._indication("H225", rewritten)
        self._run()
        indication.refresh_from_db()
        self.assertEqual(indication.description, rewritten)

    def test_does_not_touch_concatenated_combination(self):
        pegado = "Mortal en contacto con la piel\r\nMortal si se inhala"
        indication = self._indication("H310 + H330", pegado)
        self._run()
        indication.refresh_from_db()
        self.assertEqual(indication.description, pegado)

    def test_is_idempotent(self):
        indication = self._indication("H221", "Gas inflamable")
        self._run()
        indication.refresh_from_db()
        first = indication.description
        self._run()
        indication.refresh_from_db()
        self.assertEqual(indication.description, first)

    def test_leaves_unlisted_codes_alone(self):
        indication = self._indication("H999", "frase inventada sin tilde")
        self._run()
        indication.refresh_from_db()
        self.assertEqual(indication.description, "frase inventada sin tilde")
