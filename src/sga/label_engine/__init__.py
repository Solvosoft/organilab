# -*- coding: utf-8 -*-
"""
label_engine - Motor de generación de etiquetas GHS/SGA para reactivos químicos.

Escuela de Química - Universidad Nacional de Costa Rica.
Cumple RTCR 481:2015 (SGA/GHS).

Uso típico (API Python):
    from sga.label_engine import LabelBlueprint, LabelEngine

    data = {
        'nombre': 'Ácido Clorhídrico',
        'formula': 'HCl',
        'estado_fisico': 'l',
        'simbolos': ['Corrosivo'],
        'palabra_advertencia': 'PELIGRO',
    }
    bp = LabelBlueprint.from_dict(data)
    bp.ancho_mm, bp.alto_mm = 70, 40

    engine = LabelEngine()
    img = engine.generate(bp)
    img.save('etiqueta.png')

Vendorizado en Organilab desde el proyecto Etiquetador (Escuela de Química, UNA).
Los datos institucionales (logos, texto de cabecera, URL del QR) se inyectan por
organización vía ``LabelBlueprint`` en lugar de estar fijos en la configuración.
"""
from __future__ import annotations

from sga.label_engine.models import LabelBlueprint, LabelTooSmallError
from sga.label_engine.engine import LabelEngine
from sga.label_engine.pdf import generate_pdf, labels_to_pdf
from sga.label_engine.config import (
    RUTA_LOGO_UNA,
    RUTA_LOGO_QUIMICA,
    CARPETA_PICTOGRAMAS,
    CARPETA_PICTOGRAMAS_EPP,
    PICTOGRAMAS_OSHA,
    PICTOGRAMAS_EPP,
    QR_SAFETY_SHEETS_URL,
    LABEL_SIZES,
    BORDER_COLORS,
    FORMULA_LABEL_COLOR,
    H_PHRASE_COLOR,
    P_PHRASE_COLOR,
    INFO_COLOR,
    LOGO_HEIGHT_RATIO,
    PICTOGRAM_SCALE,
    QR_SCALE,
    QR_SCALE_EFFECTIVE,
    MARGIN_RATIO,
    MARGIN_INT_RATIO,
    FONT_CANDIDATES,
)

__version__ = "1.0.0"

__all__ = [
    # Core API
    "LabelBlueprint",
    "LabelTooSmallError",
    "LabelEngine",
    # Config constants
    "RUTA_LOGO_UNA",
    "RUTA_LOGO_QUIMICA",
    "CARPETA_PICTOGRAMAS",
    "CARPETA_PICTOGRAMAS_EPP",
    "PICTOGRAMAS_OSHA",
    "PICTOGRAMAS_EPP",
    "QR_SAFETY_SHEETS_URL",
    "LABEL_SIZES",
    "BORDER_COLORS",
    "FORMULA_LABEL_COLOR",
    "H_PHRASE_COLOR",
    "P_PHRASE_COLOR",
    "INFO_COLOR",
    "LOGO_HEIGHT_RATIO",
    "PICTOGRAM_SCALE",
    "QR_SCALE",
    "QR_SCALE_EFFECTIVE",
    "MARGIN_RATIO",
    "MARGIN_INT_RATIO",
    "FONT_CANDIDATES",
    "__version__",
    # PDF generation
    "generate_pdf",
    "labels_to_pdf",
]
