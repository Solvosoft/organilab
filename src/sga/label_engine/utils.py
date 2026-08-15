# -*- coding: utf-8 -*-
"""Utilidades de encoding y normalización de texto."""
from __future__ import annotations

import unicodedata


def normalize_text(text: str) -> str:
    """Aplica normalización NFC a texto."""
    if not isinstance(text, str):
        return ""
    try:
        return unicodedata.normalize('NFC', text)
    except Exception:
        return text


def read_text_file(path: str, encodings=('utf-8', 'latin-1', 'cp1252', 'iso-8859-1')) -> str:
    """Lee archivo de texto con detección automática de encoding.

    Intenta leer el archivo con varios encodings comunes (UTF-8, Latin-1, CP1252, ISO-8859-1).
    Si ninguno funciona, usa UTF-8 con errores reemplazados.
    """
    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()
