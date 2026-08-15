# -*- coding: utf-8 -*-
"""Renderer de línea separadora horizontal."""
from __future__ import annotations

from sga.label_engine.layout.canvas import Canvas
from sga.label_engine.resources import ResourceCache


class RuleRenderer:
    """Dibuja una línea horizontal. ``content_ref`` = {'color': str}.

    El Box define el inicio (x, y) y el ancho; la línea va a la altura ``y``.
    """

    def render(self, box, canvas: Canvas, resources: ResourceCache) -> None:
        color = box.content_ref.get('color', '#CCCCCC')
        canvas.line((box.x, box.y, box.x + box.width, box.y), color, width=1)
