# -*- coding: utf-8 -*-
"""
Modelos de datos para el motor de etiquetas.
LabelBlueprint es el objeto inmutable que contiene todos los datos de una etiqueta.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sga.label_engine.utils import normalize_text


class LabelTooSmallError(ValueError):
    """La etiqueta es demasiado pequeña para alojar el contenido obligatorio
    (pictogramas, nombre, palabra de advertencia y frases H) a un tamaño legible."""


@dataclass
class LabelBlueprint:
    """Datos de entrada para la generación de una etiqueta."""

    # Identificación química
    nombre: str = ""
    formula: str = ""
    cas: str = ""
    estado_fisico: str = ""

    # Concentración y cantidad
    concentracion: str = ""
    cantidad: str = ""

    # Fechas
    fecha_caducidad: str = ""
    fecha_preparacion: str = ""
    lote: str = ""

    # Institucional
    fabricante: str = ""
    ubicacion: str = ""
    responsable: str = ""
    catedra: str = ""
    laboratorio: str = ""
    # Multi-tenant: encabezado, logos y QR inyectados por organización.
    institucion: str = ""        # línea superior del encabezado (org). "" = default.
    logo_izq_path: str = ""      # ruta de logo izquierdo (org). "" = logo por defecto.
    logo_der_path: str = ""      # ruta de logo derecho (org). "" = logo por defecto.
    qr_url: str = ""             # URL codificada en el QR. "" = QR por defecto.

    # Hazard
    simbolos: list[str] = field(default_factory=list)
    palabra_advertencia: str = ""
    frases_peligro: str = ""
    consejos_prudencia: str = ""

    # Adicional
    info_adicional: str = ""
    recipiente_nombre: str = ""
    recipiente_color: str = ""

    # Dimensiones
    ancho_mm: float = 70.0
    alto_mm: float = 40.0
    dpi: int = 300

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LabelBlueprint:
        """Construye un LabelBlueprint desde el dict que devuelve la GUI."""

        simbolos = data.get('simbolos', [])
        if not isinstance(simbolos, list):
            simbolos = []

        return cls(
            nombre=normalize_text(data.get('nombre', 'SIN NOMBRE')),
            formula=normalize_text(data.get('formula', '')),
            cas=normalize_text(data.get('cas', '')),
            fabricante=normalize_text(data.get('fabricante', '')),
            concentracion=normalize_text(data.get('concentracion', '')),
            estado_fisico=data.get('estado_fisico', '').strip(),
            cantidad=normalize_text(data.get('cantidad', '')),
            fecha_caducidad=data.get('fecha_caducidad', ''),
            lote=data.get('lote', ''),
            fecha_preparacion=data.get('fecha_preparacion', ''),
            ubicacion=normalize_text(data.get('ubicacion', '')),
            responsable=normalize_text(data.get('responsable', '')),
            catedra=normalize_text(data.get('catedra', '')),
            laboratorio=normalize_text(data.get('laboratorio', '')),
            institucion=normalize_text(data.get('institucion', '')),
            logo_izq_path=data.get('logo_izq_path', ''),
            logo_der_path=data.get('logo_der_path', ''),
            qr_url=data.get('qr_url', ''),
            simbolos=simbolos,
            palabra_advertencia=data.get('palabra_advertencia', ''),
            frases_peligro=normalize_text(data.get('frases_peligro', '')),
            consejos_prudencia=normalize_text(data.get('consejos_prudencia', '')),
            info_adicional=normalize_text(data.get('info_adicional', '')),
            recipiente_nombre=normalize_text(data.get('recipiente_nombre', '')),
            recipiente_color=normalize_text(data.get('recipiente_color', '')),
        )

    def validate(self) -> list[str]:
        """Retorna lista de errores de validación (vacío = válido)."""
        errors = []
        if not self.nombre or self.nombre == 'SIN NOMBRE':
            errors.append("El nombre del reactivo es obligatorio")
        if self.ancho_mm <= 0 or self.alto_mm <= 0:
            errors.append("Las dimensiones de la etiqueta deben ser positivas")
        if self.dpi <= 0:
            errors.append("DPI debe ser positivo")
        return errors
