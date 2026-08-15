# -*- coding: utf-8 -*-
"""Pruebas de la corrección de frases GHS incompletas (migración sga.0096)."""
import importlib

from django.test import SimpleTestCase, TestCase

from sga.models import PrudenceAdvice

migration = importlib.import_module("sga.migrations.0096_fix_incomplete_ghs_phrases")


class IncompleteDetectionTest(SimpleTestCase):
    """Qué cuenta como texto a medias."""

    def test_combination_left_at_its_heading_is_incomplete(self):
        self.assertTrue(
            migration._is_incomplete("P304 + P340", "EN CASO DE INHALACIÓN:")
        )

    def test_simple_code_heading_is_correct(self):
        # P304 por sí solo ES el encabezado: terminar en ":" no es un defecto.
        self.assertFalse(migration._is_incomplete("P304", "EN CASO DE INHALACIÓN:"))

    def test_text_cut_with_ellipsis_is_incomplete(self):
        self.assertTrue(migration._is_incomplete("P352", "Lavar con abundante agua/…"))
        self.assertTrue(migration._is_incomplete("P501", "Eliminar el contenido..."))

    def test_complete_text_is_left_alone(self):
        self.assertFalse(
            migration._is_incomplete("P352", "Lavar con abundante agua y jabón.")
        )

    def test_placeholder_phrases_have_no_replacement(self):
        # P230 y P401 llevan un hueco que completa el proveedor: no se tocan.
        for code in ("P230", "P401"):
            self.assertIsNone(migration.FIXES.get(migration._normalize(code)), code)

    def test_code_normalization_ignores_spacing(self):
        for raw in ("P304 + P340", "P304+P340", "p304+ p340"):
            self.assertEqual(migration._normalize(raw), "P304+P340", raw)

    def test_every_replacement_carries_an_action(self):
        """Ninguna corrección puede quedarse en el encabezado."""
        for code, text in migration.FIXES.items():
            self.assertFalse(text.endswith(":"), code)
            self.assertFalse(text.endswith("...") or text.endswith("…"), code)


class FixPhrasesTest(TestCase):
    """La migración completa lo incompleto y respeta lo demás."""

    def _run(self):
        from django.apps import apps as global_apps

        migration.fix_phrases(global_apps, None)

    def test_completes_truncated_combination(self):
        advice = PrudenceAdvice.objects.create(
            code="P304 + P340", name="EN CASO DE INHALACIÓN:"
        )
        self._run()
        advice.refresh_from_db()
        self.assertIn("Transportar a la persona al aire libre", advice.name)

    def test_does_not_overwrite_a_manual_correction(self):
        manual = "EN CASO DE INHALACIÓN: llevar al aire libre de inmediato."
        advice = PrudenceAdvice.objects.create(code="P304 + P340", name=manual)
        self._run()
        advice.refresh_from_db()
        self.assertEqual(advice.name, manual)

    def test_is_idempotent(self):
        advice = PrudenceAdvice.objects.create(code="P352", name="Lavar con agua/…")
        self._run()
        advice.refresh_from_db()
        first = advice.name
        self._run()
        advice.refresh_from_db()
        self.assertEqual(advice.name, first)

    def test_leaves_placeholder_phrase_untouched(self):
        advice = PrudenceAdvice.objects.create(
            code="P401", name="Almacenar conforme a..."
        )
        self._run()
        advice.refresh_from_db()
        self.assertEqual(advice.name, "Almacenar conforme a...")
