# -*- coding: utf-8 -*-
"""
Medición de texto para el planner.

El planner necesita decidir tamaños de fuente y envolver texto *antes* de dibujar.
``Measurer`` encapsula esa medición sobre una superficie de scratch, junto con la
resolución de fuentes (vía ``ResourceCache``) y el cálculo de pisos de legibilidad
en milímetros reales —de modo que "legible" signifique lo mismo en cualquier tamaño
o DPI de etiqueta.
"""
from __future__ import annotations

from typing import Any

from sga.label_engine import config
from sga.label_engine.layout.canvas import PILCanvas
from sga.label_engine.resources import ResourceCache


class Measurer:
    """Mide texto y resuelve fuentes para el planner.

    Usa un ``PILCanvas`` mínimo solo para medir; las dimensiones reales de la
    etiqueta no afectan la medición de texto (depende solo de la fuente).
    """

    def __init__(self, resources: ResourceCache | None = None, dpi: int = 300):
        self.resources = resources or ResourceCache()
        self.dpi = dpi
        self._scratch = PILCanvas(4, 4)

    # ── Fuentes ───────────────────────────────────────────────────────────────
    def font(self, size: int, bold: bool = False) -> Any:
        return self.resources.get_font(max(1, int(size)), bold=bold)

    def mm_to_px(self, mm: float) -> int:
        return int(round(mm * self.dpi / 25.4))

    def font_floor_px(self, min_mm: float = config.MIN_PHRASE_FONT_MM) -> int:
        """Tamaño de fuente mínimo legible (px) para el DPI actual."""
        return max(8, self.mm_to_px(min_mm))

    # ── Medición ────────────────────────────────────────────────────────────
    def text_size(self, text: str, font: Any) -> tuple[int, int]:
        return self._scratch.measure_text(text, font)

    def text_width(self, text: str, font: Any) -> int:
        return self._scratch.text_width(text, font)

    def line_height(self, font: Any) -> int:
        return self._scratch.line_height(font)

    # ── Wrapping ──────────────────────────────────────────────────────────────
    def wrap(self, text: str, max_width: int, font: Any) -> list[str]:
        """Envuelve un texto en líneas que caben en ``max_width``.

        Las palabras más anchas que ``max_width`` se cortan a nivel de carácter.
        """
        if not text or not text.strip():
            return []
        out: list[str] = []
        cur = ""
        for word in text.split():
            while self.text_width(word, font) > max_width and len(word) > 1:
                lo, hi = 1, len(word)
                while lo < hi:
                    mid = (lo + hi + 1) // 2
                    if self.text_width(word[:mid], font) <= max_width:
                        lo = mid
                    else:
                        hi = mid - 1
                if cur:
                    out.append(cur)
                    cur = ""
                out.append(word[:lo])
                word = word[lo:]
            test = (cur + " " + word).strip() if cur else word
            if self.text_width(test, font) <= max_width:
                cur = test
            else:
                if cur:
                    out.append(cur)
                cur = word
        if cur:
            out.append(cur)
        return out

    def wrap_items(self, items: list[str], max_width: int, font: Any) -> list[str]:
        """Envuelve varias frases; cada ítem inicia en su propia línea."""
        lines: list[str] = []
        for it in items:
            if it and it.strip():
                lines.extend(self.wrap(it.strip(), max_width, font))
        return lines

    def fits_width(self, text: str, max_width: int, font: Any) -> bool:
        return self.text_width(text, font) <= max_width
