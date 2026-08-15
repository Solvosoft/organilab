# -*- coding: utf-8 -*-
"""Renderer de logos institucionales (UNA y Escuela de Química)."""
from __future__ import annotations

from PIL import Image

from sga.label_engine.layout.canvas import Canvas
from sga.label_engine.resources import ResourceCache


class LogoRenderer:
    """Pega un logo redimensionado a la caja indicada por el planner.

    ``content_ref`` = 'una' | 'quimica'.
    """

    def render(self, box, canvas: Canvas, resources: ResourceCache) -> None:
        logo = resources.get_logo(box.content_ref)
        if logo is None:
            return
        resized = logo.resize((max(1, box.width), max(1, box.height)),
                              Image.Resampling.LANCZOS)
        if resized.mode == 'RGBA':
            background = Image.new('RGB', resized.size, (255, 255, 255))
            background.paste(resized, mask=resized.split()[3])
            resized = background
        canvas.paste_image(resized, (box.x, box.y))
