"""Un solo punto para convertir HTML en PDF (xhtml2pdf).

Todas las vistas y reportes que generan PDF pasan por :func:`html_to_pdf`. El
motor anterior (WeasyPrint) armaba el documento entero en memoria y con
reportes grandes llegaba a varios GiB; xhtml2pdf dibuja con reportlab página a
página.

Las plantillas deben limitarse a lo que xhtml2pdf entiende: CSS 2.1 sin flex ni
grid, encabezados y pies con ``@page`` + ``@frame`` y numeración con
``<pdf:pagenumber>``/``<pdf:pagecount>``.
"""

import os
from io import BytesIO
from urllib.parse import unquote, urljoin, urlparse

from django.conf import settings
from django.contrib.staticfiles import finders
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from xhtml2pdf import default as xhtml2pdf_default
from xhtml2pdf import pisa

FONT_DIR = os.path.join(os.path.dirname(__file__), "static", "fonts")

# Las fuentes base de PDF (Helvetica, Arial...) solo traen Latin-1: sin
# subíndices (C₃H₈O₃), marcas de dirección (U+200E) ni griego. DejaVu Sans sí,
# así que se registra una vez y los alias sans de xhtml2pdf apuntan a ella;
# las plantillas siguen pidiendo "Helvetica, Arial, sans-serif" sin cambios.
PDF_SANS_FONT = "DejaVuSans"
_SANS_FACES = {
    "normal": "DejaVuSans",
    "bold": "DejaVuSans-Bold",
    "italic": "DejaVuSans-Oblique",
    "boldItalic": "DejaVuSans-BoldOblique",
}
_SANS_ALIASES = (
    "helvetica", "arial", "sans", "sansserif", "sans-serif", "verdana",
    "geneva", "ui-sans-serif", "system-ui", "ui-rounded", "fantasy", "emoji",
)


def register_pdf_fonts():
    """Registra DejaVu Sans en reportlab y la usa para los alias sans."""
    if PDF_SANS_FONT in pdfmetrics.getRegisteredFontNames():
        return
    for face in _SANS_FACES.values():
        pdfmetrics.registerFont(TTFont(face, os.path.join(FONT_DIR, face + ".ttf")))
    pdfmetrics.registerFontFamily(PDF_SANS_FONT, **_SANS_FACES)
    for alias in _SANS_ALIASES:
        xhtml2pdf_default.DEFAULT_FONT[alias] = PDF_SANS_FONT
    xhtml2pdf_default.DEFAULT_FONT["helvetica-bold"] = _SANS_FACES["bold"]
    xhtml2pdf_default.DEFAULT_FONT["helvetica-oblique"] = _SANS_FACES["italic"]
    xhtml2pdf_default.DEFAULT_FONT["helvetica-boldoblique"] = _SANS_FACES["boldItalic"]


register_pdf_fonts()


class PDFRenderError(Exception):
    """xhtml2pdf no pudo generar el documento."""


def _local_path(path):
    """Ruta en disco de un recurso estático o de media, o ``None``."""
    static_url = settings.STATIC_URL or "/static/"
    media_url = settings.MEDIA_URL or "/media/"
    if path.startswith(media_url):
        candidate = os.path.join(settings.MEDIA_ROOT, path[len(media_url):])
        return candidate if os.path.isfile(candidate) else None
    if path.startswith(static_url):
        relative = path[len(static_url):]
        found = finders.find(relative)
        if found:
            return found
        candidate = os.path.join(settings.STATIC_ROOT or "", relative)
        return candidate if os.path.isfile(candidate) else None
    return None


def link_callback_for(base_url=None):
    """``link_callback`` de xhtml2pdf: resuelve imágenes y CSS a disco.

    Nunca sale a la red por un recurso propio: las URLs del sitio (absolutas o
    relativas a ``base_url``) se traducen a ``STATIC_ROOT``/``MEDIA_ROOT``.
    Lo que no se puede resolver se devuelve tal cual.
    """

    def link_callback(uri, rel=None):
        if not uri or uri.startswith("data:"):
            return uri
        parsed = urlparse(uri)
        if parsed.scheme == "file":
            return unquote(parsed.path)
        if not parsed.scheme and base_url:
            parsed = urlparse(urljoin(base_url, uri))
        local = _local_path(unquote(parsed.path))
        if local:
            return local
        # Lo demás (rutas de disco sueltas, URLs externas) va tal cual.
        return uri

    return link_callback


def html_to_pdf(html, base_url=None, output=None):
    """Convierte ``html`` en PDF.

    Devuelve los bytes del PDF, o escribe en ``output`` (un archivo abierto en
    binario) y devuelve ``None``.
    """
    target = output if output is not None else BytesIO()
    result = pisa.CreatePDF(
        src=html,
        dest=target,
        encoding="utf-8",
        link_callback=link_callback_for(base_url),
    )
    if result.err:
        raise PDFRenderError("xhtml2pdf: %s errores al generar el PDF" % result.err)
    if output is None:
        return target.getvalue()
    return None
