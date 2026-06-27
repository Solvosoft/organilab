# -*- coding: utf-8 -*-
"""Renderer de pictogramas GHS/OSHA y EPP."""
from __future__ import annotations

from sga.label_engine.layout.canvas import Canvas
from sga.label_engine.resources import ResourceCache


class PictogramRenderer:
    """Renderiza un pictograma (OSHA o EPP) cuadrado en la caja dada.

    ``content_ref`` = {'symbol': str}.
    """

    def render(self, box, canvas: Canvas, resources: ResourceCache) -> None:
        symbol = box.content_ref['symbol']
        # En backends vectoriales, incrustar el pictograma como SVG (nítido a
        # cualquier escala) si hay versión vectorial; si no, fallback a raster.
        if getattr(canvas, 'vector', False):
            svg = resources.get_pictogram_svg(symbol)
            if svg:
                canvas.embed_svg(svg, (box.x, box.y), box.width, box.height)
                return
        picto = resources.get_pictogram(symbol, box.width)
        if picto is None:
            return
        canvas.paste_image(picto, (box.x, box.y))
