# -*- coding: utf-8 -*-
"""Renderer de frases H (peligro) y P (prudencia) + referencia FDS."""
from __future__ import annotations

from sga.label_engine import config
from sga.label_engine.layout.canvas import Canvas
from sga.label_engine.resources import ResourceCache


class HPPhrasesRenderer:
    """Pinta el plan de frases ya resuelto por el planner, centrado en la caja.

    ``content_ref`` (el "plan") = {font_size, line_height, gap, inner,
                                   h_lines, p_lines, fds_lines}.
    H en rojo, P en azul, FDS en gris. Las líneas vienen pre-envueltas.
    """

    def render(self, box, canvas: Canvas, resources: ResourceCache) -> None:
        plan = box.content_ref
        font = resources.get_font(plan['font_size'], bold=False)
        lh = plan['line_height']
        gap = plan['gap']
        inner = plan.get('inner', int(lh * 0.25))
        y = box.y

        def draw_group(lines, color):
            nonlocal y
            for linea in lines:
                canvas.text((box.x, y), linea, font, color)
                y += lh + inner

        if plan.get('h_lines'):
            draw_group(plan['h_lines'], config.H_PHRASE_COLOR)
        if plan.get('p_lines'):
            y += gap
            draw_group(plan['p_lines'], config.P_PHRASE_COLOR)
        if plan.get('fds_lines'):
            y += gap
            draw_group(plan['fds_lines'], config.FDS_COLOR)
