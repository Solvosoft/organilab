# -*- coding: utf-8 -*-
"""
Tipos compartidos del módulo de layout.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Box:
    """Representa un elemento posicionado en la imagen final.

    El Box no contiene los píxeles, solo la posición, dimensiones
    y una referencia al contenido que será renderizado por el renderer.
    """
    x: int
    y: int
    width: int
    height: int
    element_type: str
    content_ref: Any = None
    z_index: int = 0


@dataclass
class LayoutResult:
    """Resultado del planner: lista de boxes posicionados y advertencias."""
    boxes: list[Box]
    total_height_used: int
    warnings: list[str]
