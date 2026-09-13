# -*- coding: utf-8 -*-
"""
Motor principal de generación de etiquetas.

``LabelEngine`` es un orquestador delgado: valida el blueprint, planifica el layout
con ``LabelPlanner`` y pinta los boxes resultantes con los renderers del registro
sobre un ``Canvas``. Toda la decisión de acomodo vive en el planner; todo el dibujo,
en los renderers.
"""
from __future__ import annotations

import logging

from PIL import Image

from sga.label_engine.models import LabelBlueprint
from sga.label_engine.resources import ResourceCache
from sga.label_engine.layout.canvas import Canvas, PILCanvas, SVGCanvas
from sga.label_engine.layout.planner import LabelPlanner
from sga.label_engine.renderers.registry import build_registry

logger = logging.getLogger("etiquetador")


class LabelEngine:
    """Genera etiquetas a partir de un ``LabelBlueprint``.

    El planner y los renderers son agnósticos del backend, por lo que el mismo
    pipeline produce PNG (``generate``) o SVG vectorial para web (``generate_svg``).
    """

    def __init__(self):
        self.resources = ResourceCache()
        self.planner = LabelPlanner(self.resources)
        self.renderers = build_registry()

    def generate(self, blueprint: LabelBlueprint) -> Image.Image:
        """Renderiza la etiqueta como imagen PIL (PNG/raster)."""
        canvas = self._render(blueprint, PILCanvas)
        return canvas.result()

    def generate_svg(self, blueprint: LabelBlueprint, embed_fonts: bool = False) -> str:
        """Renderiza la etiqueta como SVG vectorial (string), ideal para web.

        Args:
            embed_fonts: si True, incrusta la fuente DejaVu (subset) como
                ``@font-face`` base64 para fidelidad tipográfica en cualquier
                navegador sin la fuente instalada (SVG autocontenido, más pesado).
        """
        canvas = self._render(blueprint, SVGCanvas, embed_fonts=embed_fonts)
        return canvas.result()

    # ------------------------------------------------------------------
    def _render(self, blueprint: LabelBlueprint, canvas_cls, **canvas_kwargs) -> Canvas:
        """Pipeline común: validar → planificar → pintar boxes por z-index."""
        errors = blueprint.validate()
        if errors:
            raise ValueError("Blueprint inválido: " + ", ".join(errors))

        ancho_px = int(blueprint.ancho_mm * blueprint.dpi / 25.4)
        alto_px = int(blueprint.alto_mm * blueprint.dpi / 25.4)

        layout = self.planner.plan(blueprint, ancho_px, alto_px)
        for w in layout.warnings:
            logger.warning("layout: %s", w)

        canvas = canvas_cls(ancho_px, alto_px, background='white', **canvas_kwargs)
        for box in sorted(layout.boxes, key=lambda b: b.z_index):
            renderer = self.renderers.get(box.element_type)
            if renderer is None:
                logger.warning("Sin renderer para element_type=%s", box.element_type)
                continue
            renderer.render(box, canvas, self.resources)

        return canvas
