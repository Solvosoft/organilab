# -*- coding: utf-8 -*-
"""Renderer del acento de color del recipiente (heredado del contenedor).

Dibuja un marco interno con el color del contenedor donde se encuentra la
sustancia, justo por dentro del marco reglamentario de la palabra de advertencia
(que conserva su color SGA: rojo=PELIGRO, azul=ATENCIÓN, gris=otro). Así la
etiqueta "gana" visualmente el color del envase sin romper el cumplimiento SGA.
"""
from __future__ import annotations

from sga.label_engine.layout.canvas import Canvas
from sga.label_engine.resources import ResourceCache


class AccentRenderer:
    """Marco interno de color del recipiente.

    ``content_ref`` = ``{'color': str, 'thickness': int, 'inset': int}``.
    El Box cubre toda la etiqueta (x=0, y=0, width=ancho, height=alto).
    """

    def render(self, box, canvas: Canvas, resources: ResourceCache) -> None:
        d = box.content_ref or {}
        color = d.get('color')
        if not color:
            return
        thickness = max(1, int(d.get('thickness', 2)))
        inset = max(0, int(d.get('inset', 0)))
        for offset in range(inset, inset + thickness):
            canvas.rectangle(
                (offset, offset, box.width - 1 - offset, box.height - 1 - offset),
                outline=color,
            )
