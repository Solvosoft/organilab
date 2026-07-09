# -*- coding: utf-8 -*-
"""
Configuración centralizada para el motor de etiquetas.
(Constantes extraídas originalmente de la GUI monolítica, hoy en archive/etiDS00.py.)
"""
from __future__ import annotations

import os

# ─────────────────────────────────────────────────────────────────────────────
# Rutas de recursos (vendorizados en sga/label_engine/assets/)
# ─────────────────────────────────────────────────────────────────────────────
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")


def _resource_path(relative_path: str) -> str:
    return os.path.join(ASSETS_DIR, relative_path)


# Logos institucionales por defecto (fallback). En Organilab (multi-tenant) cada
# etiqueta puede inyectar su propio logo por organización vía LabelBlueprint.
RUTA_LOGO_UNA = _resource_path("imagen2.png")
RUTA_LOGO_QUIMICA = _resource_path("Escuela.png")
CARPETA_PICTOGRAMAS = _resource_path("pictogramas_osha")
CARPETA_PICTOGRAMAS_EPP = _resource_path("EPP")

# ─────────────────────────────────────────────────────────────────────────────
# Pictogramas OSHA / GHS
# ─────────────────────────────────────────────────────────────────────────────
PICTOGRAMAS_OSHA = {
    "Explosivo": "exploding_bomb.eps",
    "Inflamable": "flame.eps",
    "Comburente": "flame_over_circle.eps",
    "Gas Comprimido": "gas_cylinder.eps",
    "Corrosivo": "corrosion.eps",
    "Tóxico": "skull_crossbones.eps",
    "Peligro para la Salud": "health_hazard.eps",
    "Peligro Ambiental": "environment.eps",
    "Irritante": "exclamation.eps",
}


def cargar_pictogramas_epp() -> dict[str, str]:
    pictogramas = {}
    if not os.path.isdir(CARPETA_PICTOGRAMAS_EPP):
        return pictogramas
    for archivo in sorted(os.listdir(CARPETA_PICTOGRAMAS_EPP)):
        if archivo.lower().endswith(".eps"):
            nombre_base = os.path.splitext(archivo)[0]
            nombre_limpio = (
                nombre_base.split(".", 1)[0].replace("_", " ").replace("-", " ").strip()
            )
            if not nombre_limpio:
                nombre_limpio = nombre_base
            if nombre_limpio in pictogramas:
                nombre_limpio = f"{nombre_limpio} ({archivo})"
            pictogramas[nombre_limpio] = archivo
    return pictogramas


PICTOGRAMAS_EPP = cargar_pictogramas_epp()

# ─────────────────────────────────────────────────────────────────────────────
# Família de fontes
# ─────────────────────────────────────────────────────────────────────────────
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",
]

# ─────────────────────────────────────────────────────────────────────────────
# Dimensiones de etiquetas y papel
# ─────────────────────────────────────────────────────────────────────────────
LABEL_SIZES: dict[str, tuple[float, float] | None] = {
    "Pequeña (50x30mm)": (50, 30),
    "Mediana (70x40mm)": (70, 40),
    "Grande (100x60mm)": (100, 60),
    "Extra Grande (120x80mm)": (120, 80),
    "Personalizado": None,
}

PAPER_SIZES: dict[str, tuple[float, float]] = {
    "Letter": (612, 792),
    "A3": (841.8897637795275, 1190.5511811023622),
    "A4": (595.2755905511811, 841.8897637795275),
    "Carta": (612, 792),
}

# ─────────────────────────────────────────────────────────────────────────────
# Colores
# ─────────────────────────────────────────────────────────────────────────────
BORDER_COLORS: dict[str, str] = {
    "PELIGRO": "#CD1719",
    "ATENCION": "#034991",
    "ATENCIÓN": "#034991",
    "DEFAULT": "#a7a7a9",
}

H_PHRASE_COLOR = "#CC0000"
P_PHRASE_COLOR = "#0066CC"
INFO_COLOR = "#666666"
INSTITUTIONAL_COLOR = "#000000"
MISC_COLOR = "#444444"
FORMULA_LABEL_COLOR = "#333333"

# ─────────────────────────────────────────────────────────────────────────────
# Ratios de layout (fracción del tamaño en píxeles)
# ─────────────────────────────────────────────────────────────────────────────
LOGO_HEIGHT_RATIO = 0.04
PICTOGRAM_SCALE = 0.14
QR_SCALE = 0.12
QR_SCALE_EFFECTIVE = 0.16
MARGIN_RATIO = 0.012
MARGIN_INT_RATIO = 0.005
MIN_MARGIN_CM = 0.25  # cm -> px (dpi-dependent)
WARNING_FONT_RATIO = 0.06
WARNING_VERTICAL_SPACING_RATIO = 0.005

# ─────────────────────────────────────────────────────────────────────────────
# QR URL hardcodeada
# ─────────────────────────────────────────────────────────────────────────────
QR_SAFETY_SHEETS_URL = (
    "https://drive.google.com/drive/folders/1c2MBCverT3r01K9cP0jyiLrG5xnFxYQ3"
)

# ─────────────────────────────────────────────────────────────────────────────
# Configuración de pictogramas
# ─────────────────────────────────────────────────────────────────────────────
MAX_OSHA_PICTOGRAMS = 5
DEFAULT_EPS_BASE_SIZE = 500

# ─────────────────────────────────────────────────────────────────────────────
# Frases H/P: manejo inteligente de espacio (SGA/RTCR 481:2015)
# ─────────────────────────────────────────────────────────────────────────────
# Política de degradación cuando las frases no caben (en orden):
#   1) Encoger la fuente hasta MIN_PHRASE_FONT_MM (piso de legibilidad).
#   2) Recortar consejos de prudencia (P) mostrando los más relevantes primero.
#   3) Compactar P a códigos (P280 · P305+P351+P338).
#   4) Reemplazar el remanente por la referencia a la FDS.
# Las indicaciones de peligro (H) son obligatorias y nunca se recortan salvo
# que la etiqueta sea físicamente demasiado pequeña (último recurso).
# Tamaño mínimo absoluto de etiqueta (mm). Por debajo se rechaza sin medir.
MIN_LABEL_MM = (35.0, 20.0)  # (ancho, alto)
# Factor de escala mínimo del cuerpo en la negociación de espacio. Si ni a esta
# escala cabe el contenido obligatorio a piso legible → LabelTooSmallError.
MIN_BODY_SCALE = 0.40

MIN_PHRASE_FONT_MM = 1.2  # altura mínima legible de carácter (mm)
PHRASE_FONT_RATIO = 0.040  # tamaño "cómodo" inicial = ratio * dim_reference
FDS_REFERENCE_TEXT = "Consulte la FDS para información completa"
FDS_COLOR = "#666666"
MAX_P_PHRASES = 6  # GHS recomienda limitar P a los más relevantes
