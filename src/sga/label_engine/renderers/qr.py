# -*- coding: utf-8 -*-
"""Renderer de código QR para hojas de seguridad."""
from __future__ import annotations

from PIL import Image
import qrcode

from sga.label_engine import config
from sga.label_engine.layout.canvas import Canvas
from sga.label_engine.resources import ResourceCache


class QRCodeRenderer:
    """Genera y pega un código QR en la caja indicada.

    ``content_ref`` = ``{'url': str}`` (URL a codificar). Si está vacía, usa la
    URL por defecto de ``config``.
    """

    def render(self, box, canvas: Canvas, resources: ResourceCache) -> None:
        url = (box.content_ref or {}).get('url') or config.QR_SAFETY_SHEETS_URL

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=12,
            border=1,
        )
        qr.add_data(url)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((box.width, box.height), Image.Resampling.LANCZOS)
        if qr_img.mode != 'RGB':
            qr_img = qr_img.convert('RGB')

        canvas.paste_image(qr_img, (box.x, box.y))
