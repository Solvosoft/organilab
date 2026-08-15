# -*- coding: utf-8 -*-
"""
Registro de renderers: mapea ``element_type`` (lo que produce el planner en cada
``Box``) a la instancia de renderer encargada de pintarlo.

El engine lo recorre así::

    for box in sorted(layout.boxes, key=lambda b: b.z_index):
        registry[box.element_type].render(box, canvas, resources)

Todos los renderers comparten la firma ``render(box, canvas, resources)``.
"""
from __future__ import annotations

from sga.label_engine.renderers import (
    LogoRenderer,
    TextBlockRenderer,
    ChemicalNameRenderer,
    FormulaRenderer,
    PictogramRenderer,
    QRCodeRenderer,
    HPPhrasesRenderer,
    RuleRenderer,
    BorderRenderer,
    AccentRenderer,
)


def build_registry() -> dict[str, object]:
    """Construye el mapeo ``element_type -> renderer`` con instancias frescas."""
    return {
        'logo': LogoRenderer(),
        'text': TextBlockRenderer(),
        'name': ChemicalNameRenderer(),
        'formula': FormulaRenderer(),
        'pictogram': PictogramRenderer(),
        'qr': QRCodeRenderer(),
        'phrases': HPPhrasesRenderer(),
        'rule': RuleRenderer(),
        'border': BorderRenderer(),
        'accent': AccentRenderer(),
    }


# Tipos de elemento que el planner puede emitir.
ELEMENT_TYPES = (
    'logo', 'text', 'name', 'formula', 'pictogram', 'qr', 'phrases', 'rule',
    'border', 'accent',
)
