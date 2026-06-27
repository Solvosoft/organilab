# -*- coding: utf-8 -*-
"""
Render de un ``LabelBlueprint`` a una respuesta HTTP (PNG / SVG / PDF).

Helper compartido por las vistas de etiquetas de ``sga`` (catálogo) y
``laboratory`` (instancia física), para no duplicar el pipeline del motor.
"""
from __future__ import annotations

import io

from django.http import HttpResponse
from django.utils.translation import gettext as _

from sga.label_engine import LabelEngine, LabelTooSmallError


def render_label(blueprint, formato="png", filename="etiqueta"):
    """Genera la etiqueta y devuelve un ``HttpResponse`` en el formato pedido.

    ``formato`` ∈ {``png``, ``svg``, ``pdf``}. Si la etiqueta es demasiado
    pequeña para el contenido obligatorio SGA, devuelve un 400 con el mensaje
    del motor (que sugiere un tamaño mínimo).
    """
    formato = (formato or "png").lower()
    engine = LabelEngine()

    try:
        if formato == "svg":
            svg = engine.generate_svg(blueprint)
            response = HttpResponse(svg, content_type="image/svg+xml")
            response["Content-Disposition"] = f'inline; filename="{filename}.svg"'
            return response

        img = engine.generate(blueprint)
    except LabelTooSmallError as exc:
        return HttpResponse(str(exc), status=400, content_type="text/plain; charset=utf-8")

    if formato == "pdf":
        from reportlab.pdfgen import canvas as pdf_canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import mm
        import tempfile
        import os

        buf = io.BytesIO()
        c = pdf_canvas.Canvas(buf, pagesize=letter)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            img.save(tmp.name, "PNG")
            c.drawImage(tmp.name, 20, letter[1] - blueprint.alto_mm * mm - 20,
                        width=blueprint.ancho_mm * mm, height=blueprint.alto_mm * mm,
                        preserveAspectRatio=True)
            os.unlink(tmp.name)
        c.save()
        buf.seek(0)
        response = HttpResponse(buf.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
        return response

    # PNG por defecto.
    buf = io.BytesIO()
    img.save(buf, "PNG")
    response = HttpResponse(buf.getvalue(), content_type="image/png")
    response["Content-Disposition"] = f'inline; filename="{filename}.png"'
    return response
