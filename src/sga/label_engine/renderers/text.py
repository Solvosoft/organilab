# -*- coding: utf-8 -*-
"""
Renderers de texto: bloque genérico, nombre químico y fórmula química.

Todos consumen contenido ya resuelto por el planner (fuentes, líneas, colores) y
pintan sobre un ``Canvas``. No toman decisiones de acomodo.
"""
from __future__ import annotations

from sga.label_engine import config
from sga.label_engine.layout.canvas import Canvas
from sga.label_engine.resources import ResourceCache
from sga.label_engine.utils import normalize_text


class TextBlockRenderer:
    """Renderiza un bloque de líneas de texto, alineadas a izquierda o centro.

    ``content_ref`` = {lines, font_size, bold, color, align('left'|'center'), line_gap}.
    Sirve para texto institucional, palabra de advertencia, info, pie y recipiente.
    """

    def render(self, box, canvas: Canvas, resources: ResourceCache) -> None:
        d = box.content_ref
        font = resources.get_font(d['font_size'], bold=d.get('bold', False))
        color = d.get('color', '#000000')
        align = d.get('align', 'left')
        line_gap = d.get('line_gap', 0)
        lh = canvas.line_height(font)
        y = box.y
        for line in d['lines']:
            if align == 'center':
                w, _ = canvas.measure_text(line, font)
                x = box.x + (box.width - w) // 2
            else:
                x = box.x
            canvas.text((x, y), line, font, color)
            y += lh + line_gap


class ChemicalNameRenderer:
    """Renderiza el nombre del reactivo (1-2 líneas) con estado físico como subíndice.

    ``content_ref`` = {lines, suffix, truncated, font_size_main, font_size_sub, line_gap}.
    """

    def render(self, box, canvas: Canvas, resources: ResourceCache) -> None:
        d = box.content_ref
        font_main = resources.get_font(d['font_size_main'], bold=True)
        font_sub = resources.get_font(d['font_size_sub'], bold=True)
        lines = d['lines']
        suffix = d.get('suffix', '')
        line_gap = d.get('line_gap', canvas.line_height(font_main))

        y = box.y
        for i, line in enumerate(lines):
            canvas.text((box.x, y), line, font_main, 'black')
            if i == len(lines) - 1 and suffix:
                w_main, h_main = canvas.measure_text(line, font_main)
                _, h_sub = canvas.measure_text(suffix, font_sub)
                canvas.text((box.x + w_main + 2, y + h_main - h_sub), suffix, font_sub, 'black')
            y += line_gap
        if d.get('truncated'):
            canvas.text((box.x, y), "...", font_main, 'black')


class FormulaRenderer:
    """Renderiza fórmula química (con sub/superíndices) + CAS + concentración.

    Markup de fórmula: ``_{...}`` para subíndice, ``^{...}`` para superíndice.
    ``content_ref`` = {formula, cas, concentracion, estado_suffix,
                       font_size_main, font_size_sub, font_size_sup, line_gap}.
    """

    @staticmethod
    def parse_formula(formula: str) -> list[tuple[str, str]]:
        """Convierte markup en tokens: [('n','texto'), ('s','texto'), ('p','texto')]."""
        tokens = []
        i = 0
        s = formula
        while i < len(s):
            if s[i] in ('_', '^'):
                kind = 's' if s[i] == '_' else 'p'
                i += 1
                if i < len(s) and s[i] == '{':
                    j = s.find('}', i + 1)
                    if j == -1:
                        content = s[i + 1:]
                        i = len(s)
                    else:
                        content = s[i + 1:j]
                        i = j + 1
                else:
                    content = s[i] if i < len(s) else ''
                    i += 1
                if content:
                    tokens.append((kind, content))
            else:
                j = i + 1
                while j < len(s) and s[j] not in ('_', '^'):
                    j += 1
                tokens.append(('n', s[i:j]))
                i = j
        return tokens

    def render(self, box, canvas: Canvas, resources: ResourceCache) -> None:
        d = box.content_ref
        font_n = resources.get_font(d['font_size_main'], bold=False)
        font_s = resources.get_font(d['font_size_sub'], bold=False)
        font_p = resources.get_font(d['font_size_sup'], bold=False)
        fill = config.FORMULA_LABEL_COLOR

        x = box.x
        y = box.y
        h_main = canvas.measure_text('A', font_n)[1]

        if d['formula']:
            label = "Fórmula: "
            canvas.text((x, y), label, font_n, fill)
            x += canvas.text_width(label, font_n)

            for kind, texto in self.parse_formula(d['formula']):
                texto = normalize_text(texto)
                if kind == 'n':
                    canvas.text((x, y), texto, font_n, fill)
                    x += canvas.text_width(texto, font_n)
                elif kind == 's':
                    h_s = canvas.measure_text(texto, font_s)[1]
                    canvas.text((x, y + h_main - h_s), texto, font_s, fill)
                    x += canvas.text_width(texto, font_s)
                elif kind == 'p':
                    canvas.text((x, y - int(h_main * 0.30)), texto, font_p, fill)
                    x += canvas.text_width(texto, font_p)

            if d.get('estado_suffix'):
                suffix = normalize_text(d['estado_suffix'])
                h_sf = canvas.measure_text(suffix, font_s)[1]
                canvas.text((x + 2, y + h_main - h_sf), suffix, font_s, fill)
                x += 2 + canvas.text_width(suffix, font_s)

            if d['cas']:
                x += canvas.text_width("   ", font_n)

        if d['cas']:
            label = "CAS: "
            canvas.text((x, y), label, font_n, fill)
            x += canvas.text_width(label, font_n)
            canvas.text((x, y), d['cas'], font_n, fill)

        if d['concentracion']:
            y2 = y + d.get('line_gap', int(h_main * 1.3))
            canvas.text((box.x, y2), d['concentracion'], font_n, fill)
