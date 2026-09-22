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
    Feature(
        id="PLAT-02",
        name="Decidir qué correos manda la organización y con qué texto",
        module="presentation",
        kind="ui",
        description=(
            "Lista los procesos con correo registrado (`register_context`). La "
            "organización puede apagar uno o reemplazar su asunto y mensaje; la "
            "configuración se hereda a las hijas. `send_process_email` la aplica al enviar."
        ),
        priority="P3",
        steps=(
            Step(
                id="notificaciones",
                name="Apagar, personalizar o restaurar el correo de un proceso",
                actors=("administrativo_superior",),
                routes=("platform:notificationsetting_list",),
                permissions=("presentation.view_notificationsetting",),
                source="src/presentation/platform/notifications_api.py, src/presentation/notifications.py",
            ),
        ),
    ),
    Feature(
        id="PLAT-03",
        name="Configurar reglas de alerta y revisar sus disparos",
        module="presentation",
        kind="ui",
        description=(
            "Una regla dice qué proceso vigilar, con qué disparador y umbral, y a quién "
            "avisar: responsable, roles, correo del proceso, tarea pendiente y, si es "
            "crítica, notificación en la campana. Solo se ven los procesos cuyo permiso "
            "tiene el usuario; la pestaña de historial lista cada disparo."
        ),
        priority="P2",
        steps=(
            Step(
                id="reglas",
                name="Crear, ajustar o desactivar una regla y consultar su historial",
                actors=ADMIN_PLATAFORMA,
                routes=("platform:alertrule_list",),
                permissions=("presentation.view_alertrule",),
                source="src/presentation/platform/alerts_api.py, src/presentation/alerts.py",
            ),
        ),
    ),
)
