# -*- coding: utf-8 -*-
"""
Carga centralizada de recursos con caché: logos, fontes e pictogramas.
"""
from __future__ import annotations

import logging
import os

from PIL import Image, ImageDraw, ImageFont

from sga.label_engine import config

logger = logging.getLogger("etiquetador")


class ResourceCache:
    """Carga y memoria caché de recursos estáticos."""

    def __init__(self):
        self._logos: dict[str, Image.Image] = {}
        self._pictograms: dict[str, Image.Image] = {}
        self._pictogram_svgs: dict[str, str | None] = {}
        self._fonts: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}

    # ─────────────────────────────────────────────────────────────────────────
    # Logos
    # ─────────────────────────────────────────────────────────────────────────
    def get_logo(self, key: str) -> Image.Image | None:
        if key in self._logos:
            return self._logos[key]

        # ``key`` puede ser una clave conocida ('una'/'quimica') o una ruta de
        # archivo (logo de la organización inyectado por el blueprint).
        path = {
            'una': config.RUTA_LOGO_UNA,
            'quimica': config.RUTA_LOGO_QUIMICA,
        }.get(key, key)

        if not path or not os.path.exists(path):
            logger.warning(f"Logo no encontrado: {key} ({path})")
            return None

        try:
            img = Image.open(path).convert('RGBA')
            self._logos[key] = img
            logger.info(f"Logo cargado: {key}")
            return img
        except Exception as e:
            logger.error(f"Error abriendo logo {key}: {e}")
            return None

    def preload_logos(self) -> list[str]:
        """Carga ambos logos y retorna lista de errores."""
        errors = []
        for key in ('una', 'quimica'):
            if self.get_logo(key) is None:
                errors.append(f"No se pudo cargar logo: {key}")
        return errors

    # ─────────────────────────────────────────────────────────────────────────
    # Fontes
    # ─────────────────────────────────────────────────────────────────────────
    def get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        clave = (size, bold)
        if clave in self._fonts:
            return self._fonts[clave]

        # Elegir el primer candidato existente cuyo PESO coincida con lo pedido
        # (negrita ↔ archivo *Bold*). Antes se devolvía siempre el primer
        # candidato —el Bold— incluso para texto normal, dejando todo en negrita.
        def _try(candidates):
            for candidate in candidates:
                try:
                    return ImageFont.truetype(candidate, size)
                except Exception:
                    continue
            return None

        def es_bold(c):
            return 'bold' in os.path.basename(c).lower()

        match = [c for c in config.FONT_CANDIDATES if es_bold(c) == bold]
        rest = [c for c in config.FONT_CANDIDATES if es_bold(c) != bold]
        font = _try(match) or _try(rest)
        if font is None:
            logger.warning(f"No se encontró fuente de {size}pt, usando default")
            font = ImageFont.load_default()
        self._fonts[clave] = font
        return font

    # ─────────────────────────────────────────────────────────────────────────
    # Pictogramas
    # ─────────────────────────────────────────────────────────────────────────
    def get_pictogram(self, symbol: str, size: int) -> Image.Image:
        key = f"{symbol}_{size}"
        if key in self._pictograms:
            return self._pictograms[key]

        img = self._load_pictogram_file(symbol, size)
        if img is None:
            img = self._generate_fallback_pictogram(symbol, size)

        self._pictograms[key] = img
        return img

    def get_pictogram_svg(self, symbol: str) -> str | None:
        """Devuelve el SVG vectorial del pictograma si existe (para salida SVG).

        Busca un ``.svg`` junto al recurso EPS del símbolo. Devuelve ``None`` si no
        hay versión vectorial (el llamador hará fallback a raster)."""
        if symbol in self._pictogram_svgs:
            return self._pictogram_svgs[symbol]
        content = self._load_pictogram_svg(symbol)
        self._pictogram_svgs[symbol] = content
        return content

    def _load_pictogram_svg(self, symbol: str) -> str | None:
        candidates: list[str] = []
        if symbol in config.PICTOGRAMAS_OSHA:
            base = os.path.splitext(config.PICTOGRAMAS_OSHA[symbol])[0]
            candidates.append(os.path.join(config.CARPETA_PICTOGRAMAS, base + '.svg'))
        elif symbol in config.PICTOGRAMAS_EPP:
            fn = config.PICTOGRAMAS_EPP[symbol]
            d = config.CARPETA_PICTOGRAMAS_EPP
            stem = os.path.splitext(fn)[0]
            candidates += [
                os.path.join(d, fn + '.svg'),
                os.path.join(d, stem + '.svg'),
                os.path.join(d, 'svg_from_web', stem + '.svg'),
            ]
        else:
            return None
        for p in candidates:
            if os.path.exists(p):
                try:
                    with open(p, encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    logger.error(f"Error leyendo SVG {p}: {e}")
        return None

    def _load_pictogram_file(self, symbol: str, size: int) -> Image.Image | None:
        if symbol in config.PICTOGRAMAS_OSHA:
            filename = config.PICTOGRAMAS_OSHA[symbol]
            full_path = os.path.join(config.CARPETA_PICTOGRAMAS, filename)
        elif symbol in config.PICTOGRAMAS_EPP:
            filename = config.PICTOGRAMAS_EPP[symbol]
            full_path = os.path.join(config.CARPETA_PICTOGRAMAS_EPP, filename)

            thumb_name = f"{os.path.splitext(filename)[0]}.png"
            thumb_path = os.path.join(config.CARPETA_PICTOGRAMAS_EPP, 'thumbs', thumb_name)
            if os.path.exists(thumb_path):
                try:
                    thumb = Image.open(thumb_path)
                    if thumb.mode != 'RGBA':
                        thumb = thumb.convert('RGBA')
                    return thumb.resize((size, size), Image.Resampling.LANCZOS)
                except Exception as e:
                    logger.error(f"Error miniatura {thumb_path}: {e}")
        else:
            return None

        if not os.path.exists(full_path):
            return None

        try:
            eps_img = Image.open(full_path)
            base_size = config.DEFAULT_EPS_BASE_SIZE
            w, h = eps_img.size
            ratio = base_size / max(w, h)
            eps_img = eps_img.resize(
                (int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS
            )
            if eps_img.mode != 'RGBA':
                eps_img = eps_img.convert('RGBA')
            return eps_img.resize((size, size), Image.Resampling.LANCZOS)
        except Exception as e:
            logger.error(f"Error procesando EPS {symbol}: {e}")
            return None

    def _generate_fallback_pictogram(self, symbol: str, size: int) -> Image.Image:
        img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        margin = int(size * 0.08)
        cx, cy = size // 2, size // 2

        points = [
            (cx, margin),
            (size - margin, cy),
            (cx, size - margin),
            (margin, cy),
        ]
        draw.polygon(points, fill='white')
        for i in range(3):
            offset = i * 0.8
            draw.polygon(
                [
                    (points[0][0], points[0][1] + offset),
                    (points[1][0] - offset, points[1][1]),
                    (points[2][0], points[2][1] - offset),
                    (points[3][0] + offset, points[3][1]),
                ],
                outline='#C8102E',
                width=max(2, int(size * 0.025)),
            )

        try:
            font = self.get_font(int(size * 0.3), bold=True)
        except Exception:
            font = ImageFont.load_default()

        if "Explosivo" in symbol:
            draw.ellipse(
                [cx - size * 0.2, cy - size * 0.2, cx + size * 0.2, cy + size * 0.2],
                outline='black', width=3,
            )
            draw.line(
                [cx - size * 0.25, cy - size * 0.1, cx + size * 0.25, cy - size * 0.1],
                fill='black', width=3,
            )
            draw.line(
                [cx - size * 0.1, cy - size * 0.25, cx + size * 0.1, cy - size * 0.25],
                fill='black', width=3,
            )
        elif "Inflamable" in symbol:
            draw.ellipse(
                [cx - size * 0.15, cy - size * 0.25, cx + size * 0.15, cy + size * 0.1],
                fill='#FF6600',
            )
            draw.polygon(
                [(cx, cy - size * 0.35), (cx - size * 0.1, cy - size * 0.1), (cx + size * 0.1, cy - size * 0.1)],
                fill='#FF6600',
            )
        elif "Comburente" in symbol:
            draw.ellipse(
                [cx - size * 0.2, cy - size * 0.2, cx + size * 0.2, cy + size * 0.2],
                outline='black', width=3,
            )
            bbox = draw.textbbox((0, 0), "O", font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text((cx - tw / 2, cy - th / 2), "O", fill='black', font=font)
        elif "Gas Comprimido" in symbol:
            draw.ellipse(
                [cx - size * 0.2, cy - size * 0.25, cx + size * 0.2, cy - size * 0.15],
                outline='black', width=2,
            )
            draw.rectangle(
                [cx - size * 0.2, cy - size * 0.15, cx + size * 0.2, cy + size * 0.2],
                outline='black', width=2,
            )
            draw.ellipse(
                [cx - size * 0.2, cy + size * 0.1, cx + size * 0.2, cy + size * 0.2],
                outline='black', width=2,
            )
        elif "Corrosivo" in symbol:
            draw.rectangle(
                [cx - size * 0.25, cy - size * 0.15, cx - size * 0.1, cy + size * 0.2],
                fill='gray', outline='black',
            )
            draw.rectangle(
                [cx + size * 0.1, cy - size * 0.1, cx + size * 0.25, cy + size * 0.15],
                fill='gray', outline='black',
            )
        elif "Tóxico" in symbol:
            draw.ellipse(
                [cx - size * 0.2, cy - size * 0.25, cx - size * 0.05, cy - size * 0.1],
                fill='black',
            )
            draw.ellipse(
                [cx + size * 0.05, cy - size * 0.25, cx + size * 0.2, cy - size * 0.1],
                fill='black',
            )
            draw.polygon(
                [(cx - size * 0.15, cy), (cx, cy + size * 0.15), (cx + size * 0.15, cy)],
                fill='black',
            )
        elif "Peligro para la Salud" in symbol:
            draw.rectangle(
                [cx - size * 0.25, cy - size * 0.1, cx + size * 0.25, cy - size * 0.1],
                fill='black',
            )
            draw.rectangle(
                [cx - size * 0.1, cy - size * 0.25, cx + size * 0.1, cy + size * 0.25],
                fill='black',
            )
        elif "Peligro Ambiental" in symbol:
            draw.polygon(
                [
                    (cx - size * 0.2, cy),
                    (cx - size * 0.1, cy - size * 0.15),
                    (cx, cy),
                    (cx + size * 0.1, cy - size * 0.15),
                    (cx + size * 0.2, cy),
                ],
                fill='green',
            )
        elif "Irritante" in symbol:
            draw.rectangle(
                [cx - 5, cy - size * 0.25, cx + 5, cy - size * 0.05],
                fill='black',
            )
            draw.ellipse(
                [cx - 5, cy + size * 0.05, cx + 5, cy + size * 0.15],
                fill='black',
            )
        else:
            bbox = draw.textbbox((0, 0), symbol[0], font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text((cx - tw / 2, cy - th / 2), symbol[0], fill='black', font=font)

        return img
