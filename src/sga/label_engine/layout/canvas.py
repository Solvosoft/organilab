# -*- coding: utf-8 -*-
"""
Abstracción de superficie de dibujo (Canvas) para el motor de etiquetas.

El Canvas desacopla *qué* se dibuja (decidido por el planner, pintado por los
renderers) de *sobre qué* se dibuja. Hoy existe una única implementación basada en
Pillow (``PILCanvas``); en el futuro un ``SVGCanvas`` que implemente la misma
interfaz habilitará salida vectorial para web sin tocar el planner ni los renderers.

Los objetos de fuente (``font``) que reciben los métodos son los que entrega
``ResourceCache.get_font`` / ``Measurer`` para el backend activo. En PIL son
``ImageFont.FreeTypeFont``.
"""
from __future__ import annotations

import base64
import html
import io
import os
import re
from abc import ABC, abstractmethod
from typing import Any

from PIL import Image, ImageDraw


class Canvas(ABC):
    """Interfaz mínima de dibujo que usan los renderers.

    Coordenadas en píxeles, origen arriba-izquierda. Los colores son strings
    ``'#RRGGBB'`` o nombres reconocidos por el backend.
    """

    width: int
    height: int
    vector: bool = False  # True si el backend admite contenido vectorial (embed_svg)

    # ── Medición ────────────────────────────────────────────────────────────
    @abstractmethod
    def measure_text(self, text: str, font: Any) -> tuple[int, int]:
        """Ancho y alto (px) del texto con la fuente dada."""

    @abstractmethod
    def text_width(self, text: str, font: Any) -> int:
        """Ancho (px) del texto. Más barato que ``measure_text`` para wrap."""

    @abstractmethod
    def line_height(self, font: Any) -> int:
        """Alto (px) de una línea de texto con la fuente dada (referencia 'Ag')."""

    # ── Dibujo ──────────────────────────────────────────────────────────────
    @abstractmethod
    def text(self, xy: tuple[int, int], text: str, font: Any, fill: str) -> None:
        """Dibuja ``text`` en la esquina superior-izquierda ``xy``."""

    @abstractmethod
    def paste_image(self, img: Any, xy: tuple[int, int], mask: Any = None) -> None:
        """Pega una imagen en ``xy`` (con máscara opcional para transparencia)."""

    @abstractmethod
    def rectangle(self, xy: tuple[int, int, int, int], outline: str | None = None,
                  width: int = 1, fill: str | None = None) -> None:
        """Dibuja un rectángulo ``(x0, y0, x1, y1)``."""

    @abstractmethod
    def line(self, xy: tuple[int, int, int, int], fill: str, width: int = 1) -> None:
        """Dibuja una línea ``(x0, y0, x1, y1)``."""

    @abstractmethod
    def result(self) -> Any:
        """Devuelve el artefacto nativo del backend (p.ej. ``PIL.Image``)."""


class PILCanvas(Canvas):
    """Implementación de ``Canvas`` sobre Pillow."""

    def __init__(self, width: int, height: int, background: str = 'white'):
        self.width = width
        self.height = height
        self._image = Image.new('RGB', (width, height), color=background)
        self._draw = ImageDraw.Draw(self._image)

    # ── Medición ────────────────────────────────────────────────────────────
    def measure_text(self, text: str, font: Any) -> tuple[int, int]:
        bbox = self._draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def text_width(self, text: str, font: Any) -> int:
        try:
            return int(self._draw.textlength(text, font=font))
        except Exception:
            bbox = self._draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0]

    def line_height(self, font: Any) -> int:
        bbox = self._draw.textbbox((0, 0), "Ag", font=font)
        return bbox[3] - bbox[1]

    # ── Dibujo ──────────────────────────────────────────────────────────────
    def text(self, xy: tuple[int, int], text: str, font: Any, fill: str) -> None:
        self._draw.text(xy, text, font=font, fill=fill)

    def paste_image(self, img: Any, xy: tuple[int, int], mask: Any = None) -> None:
        if mask is not None:
            self._image.paste(img, xy, mask)
        elif getattr(img, 'mode', None) == 'RGBA':
            self._image.paste(img, xy, img)
        else:
            self._image.paste(img, xy)

    def rectangle(self, xy: tuple[int, int, int, int], outline: str | None = None,
                  width: int = 1, fill: str | None = None) -> None:
        self._draw.rectangle(list(xy), outline=outline, width=width, fill=fill)

    def line(self, xy: tuple[int, int, int, int], fill: str, width: int = 1) -> None:
        self._draw.line(list(xy), fill=fill, width=width)

    def result(self) -> Image.Image:
        return self._image

    # Acceso directo para transición desde el engine actual (uso interno).
    @property
    def image(self) -> Image.Image:
        return self._image

    @property
    def draw(self) -> ImageDraw.ImageDraw:
        return self._draw


class SVGCanvas(Canvas):
    """Implementación de ``Canvas`` que emite SVG (salida vectorial para web).

    El texto se emite como elementos ``<text>`` vectoriales (escalables y
    seleccionables); las imágenes rasterizadas (logos, pictogramas EPS, QR) se
    incrustan como PNG base64. La medición de texto usa las mismas métricas de
    fuente PIL que el planner, de modo que las posiciones coinciden con el render
    raster.
    """

    FONT_FAMILY = "DejaVu Sans, Arial, Helvetica, sans-serif"
    vector = True

    def __init__(self, width: int, height: int, background: str = 'white',
                 embed_fonts: bool = False):
        self.width = width
        self.height = height
        self.background = background
        self.embed_fonts = embed_fonts
        self._elements: list[str] = []
        # Caracteres usados por peso, para subsetear la fuente al incrustarla.
        self._used_chars: dict[bool, set[str]] = {False: set(), True: set()}
        # Superficie de scratch solo para medir (no se dibuja en ella).
        self._scratch = ImageDraw.Draw(Image.new('RGB', (4, 4)))

    # ── Medición (idéntica a PILCanvas: métricas PIL) ─────────────────────────
    def measure_text(self, text: str, font: Any) -> tuple[int, int]:
        bbox = self._scratch.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def text_width(self, text: str, font: Any) -> int:
        try:
            return int(self._scratch.textlength(text, font=font))
        except Exception:
            bbox = self._scratch.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0]

    def line_height(self, font: Any) -> int:
        bbox = self._scratch.textbbox((0, 0), "Ag", font=font)
        return bbox[3] - bbox[1]

    # ── Dibujo ──────────────────────────────────────────────────────────────
    def text(self, xy: tuple[int, int], text: str, font: Any, fill: str) -> None:
        size = int(getattr(font, 'size', 12) or 12)
        try:
            ascent, _ = font.getmetrics()
        except Exception:
            ascent = size
        is_bold = 'bold' in str(getattr(font, 'path', '')).lower()
        self._used_chars[is_bold].update(text)
        weight = 'bold' if is_bold else 'normal'
        y_base = xy[1] + ascent
        self._elements.append(
            f'<text x="{xy[0]}" y="{y_base}" font-family="{self.FONT_FAMILY}" '
            f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'xml:space="preserve">{html.escape(text)}</text>'
        )

    def embed_svg(self, svg_content: str, xy: tuple[int, int], width: int, height: int) -> None:
        """Incrusta un SVG vectorial (p.ej. un pictograma) escalado a la caja dada,
        anidándolo inline (conserva su viewBox y namespaces, redimensiona a w×h)."""
        s = re.sub(r'<\?xml.*?\?>', '', svg_content, flags=re.S)
        s = re.sub(r'<!--.*?-->', '', s, flags=re.S).strip()
        m = re.match(r'<svg\b([^>]*)>', s, flags=re.S)
        if not m:
            return
        attrs = re.sub(r'\s(width|height|x|y)\s*=\s*"[^"]*"', '', m.group(1))
        nested = (f'<svg{attrs} x="{xy[0]}" y="{xy[1]}" width="{width}" '
                  f'height="{height}" preserveAspectRatio="xMidYMid meet">'
                  f'{s[m.end():]}')
        self._elements.append(nested)

    def paste_image(self, img: Any, xy: tuple[int, int], mask: Any = None) -> None:
        if not isinstance(img, Image.Image):
            return
        out = img if img.mode in ('RGB', 'RGBA') else img.convert('RGBA')
        buf = io.BytesIO()
        out.save(buf, 'PNG')
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        w, h = out.size
        self._elements.append(
            f'<image x="{xy[0]}" y="{xy[1]}" width="{w}" height="{h}" '
            f'href="data:image/png;base64,{b64}" '
            f'preserveAspectRatio="none"/>'
        )

    def rectangle(self, xy: tuple[int, int, int, int], outline: str | None = None,
                  width: int = 1, fill: str | None = None) -> None:
        x0, y0, x1, y1 = xy
        attrs = [f'x="{x0}"', f'y="{y0}"',
                 f'width="{max(0, x1 - x0)}"', f'height="{max(0, y1 - y0)}"']
        attrs.append(f'fill="{fill}"' if fill else 'fill="none"')
        if outline:
            attrs.append(f'stroke="{outline}"')
            attrs.append(f'stroke-width="{width}"')
        self._elements.append(f'<rect {" ".join(attrs)}/>')

    def line(self, xy: tuple[int, int, int, int], fill: str, width: int = 1) -> None:
        x0, y0, x1, y1 = xy
        self._elements.append(
            f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" '
            f'stroke="{fill}" stroke-width="{width}"/>'
        )

    def result(self) -> str:
        defs = self._font_face_defs() if self.embed_fonts else ''
        body = "\n".join(self._elements)
        return (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}">\n'
            f'{defs}'
            f'<rect x="0" y="0" width="{self.width}" height="{self.height}" '
            f'fill="{self.background}"/>\n'
            f'{body}\n'
            f'</svg>\n'
        )

    # ── Incrustación de fuente (@font-face base64, subset) ────────────────────
    def _font_face_defs(self) -> str:
        faces = []
        for is_bold, weight in ((False, 'normal'), (True, 'bold')):
            chars = self._used_chars[is_bold]
            if not chars:
                continue
            path = self._resolve_font_path(is_bold)
            if not path:
                continue
            data = self._font_bytes(path, chars)
            if not data:
                continue
            b64 = base64.b64encode(data).decode('ascii')
            faces.append(
                "@font-face{font-family:'DejaVu Sans';font-style:normal;"
                f"font-weight:{weight};"
                f"src:url(data:font/ttf;base64,{b64}) format('truetype');}}"
            )
        if not faces:
            return ''
        return '<defs><style type="text/css">' + ''.join(faces) + '</style></defs>\n'

    @staticmethod
    def _resolve_font_path(is_bold: bool) -> str | None:
        from sga.label_engine import config
        for cand in config.FONT_CANDIDATES:
            if not os.path.exists(cand):
                continue
            if ('bold' in os.path.basename(cand).lower()) == is_bold:
                return cand
        return None

    @staticmethod
    def _font_bytes(path: str, chars: set[str]) -> bytes | None:
        """Devuelve el TTF subset a ``chars`` (fonttools); si no, el TTF completo."""
        try:
            from fontTools.subset import Subsetter, Options, load_font, save_font
            options = Options()
            options.glyph_names = False
            font = load_font(path, options)
            ss = Subsetter(options=options)
            ss.populate(text=''.join(sorted(chars)) + ' ')
            ss.subset(font)
            buf = io.BytesIO()
            save_font(font, buf, options)
            return buf.getvalue()
        except Exception:
            try:
                with open(path, 'rb') as f:
                    return f.read()
            except Exception:
                return None
