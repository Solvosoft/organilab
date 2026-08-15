# -*- coding: utf-8 -*-
"""Renderer del marco de color según palabra de advertencia."""
from __future__ import annotations

from sga.label_engine import config
from sga.label_engine.layout.canvas import Canvas
from sga.label_engine.resources import ResourceCache


class BorderRenderer:
    """Dibuja el marco perimetral: rojo=PELIGRO, azul=ATENCIÓN, gris=otro.

    ``content_ref`` = {'palabra_advertencia': str, 'thickness': int}.
    El Box cubre toda la etiqueta (x=0, y=0, width=ancho, height=alto).
    """

    def render(self, box, canvas: Canvas, resources: ResourceCache) -> None:
        d = box.content_ref
        palabra = d.get('palabra_advertencia', '').upper()
        if 'PELIGRO' in palabra:
            color = config.BORDER_COLORS['PELIGRO']
        elif 'ATENCI' in palabra:
            color = config.BORDER_COLORS['ATENCION']
        else:
            color = config.BORDER_COLORS['DEFAULT']

        thickness = d.get('thickness', 3)
        for offset in range(thickness):
            canvas.rectangle(
                (offset, offset, box.width - 1 - offset, box.height - 1 - offset),
                outline=color,
            )
