# encoding: utf-8
"""Administración de plataforma: parámetros, notificaciones y alertas por organización.

Lo que se configura aquí lo declara el código (`presentation/parameters.py`, los
contextos de correo registrados, los procesos alertables) y la organización solo guarda
lo que cambia. Un valor propio aplica a la organización y a sus hijas, salvo que una
hija fije el suyo.
"""

from presentation.feature_catalog import Feature, Step

ADMIN_PLATAFORMA = ("administrativo_superior", "administrador_ambiental")

FEATURES = (
    Feature(
        id="PLAT-01",
        name="Ajustar los parámetros del sistema de la organización",
        module="presentation",
        kind="ui",
        description=(
            "Cada parámetro muestra su valor efectivo y de dónde sale: propio, heredado de "
            "un ancestro o el valor por defecto. Restaurar borra el valor propio y vuelve "
            "a heredar. Solo se listan los parámetros cuyo permiso tiene el usuario."
        ),
        priority="P3",
        steps=(
            Step(
                id="parametros",
                name="Consultar, cambiar o restaurar un parámetro",
                actors=ADMIN_PLATAFORMA,
                routes=("platform:systemparameter_list",),
                permissions=("presentation.view_systemparameter",),
                source="src/presentation/platform/parameters_api.py SystemParameterViewSet",
            ),
        ),
    ),
)
