# -*- coding: utf-8 -*-
"""
Generación de PDF de etiquetas usando reportlab.
"""
from __future__ import annotations

import os
import tempfile

from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A3, A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

from sga.label_engine.models import LabelBlueprint
from sga.label_engine.engine import LabelEngine


PAPER_SIZES = {
    'Letter': letter,
    'A3': A3,
    'A4': A4,
    'Carta': letter,
}


def generate_pdf(
    blueprints: list[LabelBlueprint],
    filename: str,
    paper_size: str = 'Letter',
) -> None:
    """Genera un PDF con una etiqueta por página (o todas en una hoja si caben).

    Args:
        blueprints: lista de LabelBlueprint (cada uno = una etiqueta)
        filename: ruta del PDF a generar
        paper_size: tamaño de papel ('Letter', 'A3', 'A4', 'Carta')
    """
    tamano = PAPER_SIZES.get(paper_size, letter)
    c = canvas.Canvas(filename, pagesize=tamano)
    ancho_pagina, alto_pagina = tamano
    margen_pt = 10 * mm
    x, y = margen_pt, alto_pagina - margen_pt

    engine = LabelEngine()

    for idx, bp in enumerate(blueprints):
        img = engine.generate(bp)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
        img.save(temp_path, 'PNG')

        ancho_pt = bp.ancho_mm * 2.83465
        alto_pt = bp.alto_mm * 2.83465
        c.drawImage(
            ImageReader(temp_path), x, y - alto_pt,
            width=ancho_pt, height=alto_pt,
            preserveAspectRatio=True,
        )
        os.unlink(temp_path)

        x += ancho_pt + 5 * mm
        if x + ancho_pt > ancho_pagina - margen_pt:
            x = margen_pt
            y -= alto_pt + 5 * mm
            if y - alto_pt < margen_pt:
                c.showPage()
                x, y = margen_pt, alto_pagina - margen_pt

    c.save()


def labels_to_pdf(
    data_list: list[dict],
    filename: str,
    paper_size: str = 'Letter',
) -> None:
    """API de compatibilidad: recibe dicts (formato GUI) y genera PDF.

    Args:
        data_list: lista de dicts con datos de etiquetas
        filename: ruta del PDF
        paper_size: tamaño de papel
    """
    blueprints = []
    for data in data_list:
        bp = LabelBlueprint.from_dict(data)
        blueprints.append(bp)
    generate_pdf(blueprints, filename, paper_size)
