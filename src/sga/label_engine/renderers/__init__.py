"""
Renderers package for label_engine.

Todos los renderers comparten la firma ``render(box, canvas, resources)`` y solo
pintan contenido ya resuelto por el planner sobre un ``Canvas``.
"""
from sga.label_engine.renderers.logos import LogoRenderer
from sga.label_engine.renderers.text import (
    TextBlockRenderer,
    ChemicalNameRenderer,
    FormulaRenderer,
)
from sga.label_engine.renderers.pictogram import PictogramRenderer
from sga.label_engine.renderers.qr import QRCodeRenderer
from sga.label_engine.renderers.phrases import HPPhrasesRenderer
from sga.label_engine.renderers.rule import RuleRenderer
from sga.label_engine.renderers.border import BorderRenderer
from sga.label_engine.renderers.accent import AccentRenderer

__all__ = [
    'LogoRenderer',
    'TextBlockRenderer',
    'ChemicalNameRenderer',
    'FormulaRenderer',
    'PictogramRenderer',
    'QRCodeRenderer',
    'HPPhrasesRenderer',
    'RuleRenderer',
    'BorderRenderer',
    'AccentRenderer',
]
