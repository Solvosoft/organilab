# encoding: utf-8
"""Reservar, aprobar, entregar y devolver material del laboratorio.

Es el flujo multi-actor arquetípico de Organilab y el peor cubierto: seis pruebas
unitarias en 89 líneas (`reservations_management/tests/test_reservations.py`), ninguna
de devolver, cerrar ni acción por producto, y todas conceden permisos con
`user.user_permissions.add()`, que salta la capa `Rol` entera.

**El hallazgo que este fichero deja por escrito:** el sistema *no separa* los cuatro
actores que el negocio nombra. Solo hay tres permisos para todo el flujo
(`views.py:37,64,129,168,273`): quien entrega y quien recibe la devolución comparten
`change_reservedproducts`, y quien aprueba y quien cierra comparten
`change_reservations`. El aprobador tampoco está atado al responsable del laboratorio.
La separación de responsabilidades que ISO 17025 supone no está implementada, así que
no puede estar probada: es un hallazgo de diseño, no un hueco de cobertura.
"""

from presentation.feature_catalog import Feature, Step

#: Los dos conjuntos de estados comparten enteros: `ACCEPTED == BORROWED == 1` y
#: `CLOSED == SELECTED == 3` (`reservations_management/models.py:9-14`). No son
#: transiciones distintas en base de datos, solo etiquetas distintas según el modelo.
RESERVATION_STATES = (
    "Reservations.status: REQUESTED(0) → ACCEPTED(1) | DENIED(2) → CLOSED(3)",
    "ReservedProducts.status: SELECTED(3) → REQUESTED(0) → BORROWED(1) | DENIED(2) "
    "→ RETURNED(4)",
)

SOLICITANTES = (
    "estudiante", "profesor", "tecnico_laboratorio", "asistente_laboratorio",
)
APROBADORES = (
    "administrador_laboratorio", "administrativo_centro_trabajo",
    "asistente_laboratorio",
)

FEATURES = (
    Feature(
        id="RES-01",
        name="Reservar material y llevar la reserva hasta su devolución",
        module="reservations_management",
        kind="ui",
        description=(
            "Un usuario del laboratorio pide una cantidad de un `ShelfObject` para un "
            "rango de fechas. Un gestor acepta o rechaza la reserva completa, o "
            "producto por producto. Al aceptar se descuenta el stock. Al terminar, "
            "alguien registra la devolución y el stock vuelve. La reserva se cierra "
            "cuando ya no queda nada vivo en ella."
        ),
        states=RESERVATION_STATES,
        priority="P1",
        doc="docs/source/desc_funcionalidades/reservas_mo.rst",
        steps=(
            Step(
                id="reservar_directo",
                name="Reservar desde el estante (reserva directa)",
                actors=SOLICITANTES + ("estudiante",),
                routes=("laboratory:object_reservation",),
                # Ojo: reservar exige un permiso de INVENTARIO, no de reservas.
                # Ver HALLAZGO-RES-4.
                permissions=("laboratory.add_shelfobject",),
                transition="→ ReservedProducts.status=REQUESTED(0)",
                source="src/laboratory/reservation.py:24 ShelfObjectReservation",
            ),
            Step(
                id="reservar_por_procedimiento",
                name="Solicitar la reserva desde un procedimiento",
                actors=("profesor", "estudiante"),
                routes=("academic:generate_reservation",),
                permissions=("reservations_management.add_reservedproducts",),
                transition="→ Reservations(is_massive=True) con sus ReservedProducts",
                source="src/academic/views.py:727,825",
            ),
            Step(
                id="ver_mis_reservas",
                name="Consultar mis reservas",
                actors=SOLICITANTES,
                routes=("laboratory:my_reservations",),
                permissions=("reservations_management.view_reservedproducts",),
                source="src/laboratory/views/my_reservations.py:14 MyReservationView",
            ),
            Step(
                id="revisar_cola",
                name="Ver la cola de reservas por estado",
                actors=APROBADORES + ("regente", "solo_lectura"),
                routes=("reservations_management:reservations_list",),
                permissions=("reservations_management.view_reservations",),
                source="src/reservations_management/views.py:34-57",
            ),
            Step(
                id="aprobar",
                name="Aceptar o rechazar la reserva completa",
                actors=APROBADORES,
                routes=("reservations_management:manage_reservation",),
                permissions=("reservations_management.change_reservations",),
                transition=(
                    "REQUESTED → ACCEPTED | DENIED; productos → BORROWED | DENIED"
                ),
                source="src/reservations_management/views.py:60-109",
            ),
            Step(
                id="aprobar_por_producto",
                name="Aceptar o rechazar un producto suelto de la reserva",
                actors=APROBADORES,
                routes=("reservations_management:product_action",),
                permissions=("reservations_management.change_reservedproducts",),
                transition="ReservedProducts.status → BORROWED | DENIED",
                source="src/reservations_management/views.py:125-163",
            ),
            Step(
                id="recibir_devolucion",
                name="Registrar la devolución y reponer el stock",
                actors=("administrador_laboratorio", "tecnico_laboratorio"),
                routes=(
                    "reservations_management:return_product",
                    "reservations_management:increase_stock",
                ),
                permissions=("reservations_management.change_reservedproducts",),
                transition="BORROWED → RETURNED(4), stock devuelto al ShelfObject",
                source=(
                    "src/reservations_management/views.py:166-269; "
                    "functions.py:485,580"
                ),
            ),
            Step(
                id="cerrar",
                name="Cerrar la reserva",
                actors=("administrador_laboratorio",),
                routes=("reservations_management:close_reservation",),
                permissions=("reservations_management.change_reservations",),
                transition="→ CLOSED(3)",
                source="src/reservations_management/views.py:271-291",
            ),
            Step(
                id="validar_disponibilidad",
                name="Comprobar cantidad y disponibilidad antes de confirmar",
                actors=SOLICITANTES + APROBADORES,
                routes=(
                    "reservations_management:validate_reservation",
                    "reservations_management:get_product_name_and_quantity",
                ),
                permissions=(),
                source="src/reservations_management/functions.py",
            ),
        ),
        notes=(
            "HALLAZGO-RES-1: `ManageReservationView` (views.py:60) no revalida el "
            "laboratorio. El filtro `get_lab_ids` solo existe en el listado "
            "(views.py:44), así que un gestor puede aprobar una reserva de un "
            "laboratorio sobre el que no tiene alcance.",
            "HALLAZGO-RES-2: quien entrega y quien recibe la devolución comparten "
            "`change_reservedproducts`; quien aprueba y quien cierra comparten "
            "`change_reservations`. Los cuatro actores del negocio son dos permisos.",
            "HALLAZGO-RES-3: `ACCEPTED == BORROWED == 1` y `CLOSED == SELECTED == 3` "
            "(models.py:9-14): comparar `status` sin saber de qué modelo es acierta "
            "por accidente.",
            "HALLAZGO-RES-4: **la misma acción entra por dos permisos que no tienen "
            "nada que ver.** Reservar desde el estante exige "
            "`laboratory.add_shelfobject` (`reservation.py:23`) —un permiso de "
            "inventario: quien puede reservar es, por construcción, quien puede meter "
            "cosas en un estante—, mientras que reservar desde un procedimiento exige "
            "`reservations_management.add_reservedproducts` "
            "(`academic/views.py:606-609`). Un rol al que se le dé el permiso de "
            "reservas seguirá sin poder reservar desde el estante, y uno que solo "
            "gestione inventario podrá reservar sin tener ningún permiso de "
            "reservaciones.",
            "Ver «mis reservas» exige `view_reservedproducts` mientras que ver la cola "
            "exige `view_reservations`: son dos permisos distintos para dos vistas del "
            "mismo dato, lo que sí separa correctamente al solicitante del gestor.",
        ),
    ),
    Feature(
        id="RES-02",
        name="Iniciar y expirar reservas automáticamente",
        module="reservations_management",
        kind="celery",
        description=(
            "El planificador marca como prestados los productos cuya reserva empieza y "
            "deniega los que expiran sin stock disponible. Es el único actor del flujo "
            "que no es una persona, y no lo cubre ninguna prueba de navegador."
        ),
        states=RESERVATION_STATES,
        priority="P2",
        steps=(
            Step(
                id="iniciar_prestamo",
                name="Marcar como prestado al llegar la fecha de inicio",
                actors=("sistema",),
                routes=(),
                transition="→ BORROWED(1)",
                source="src/reservations_management/tasks.py:184",
            ),
            Step(
                id="denegar_expirada",
                name="Denegar la reserva que expira sin stock",
                actors=("sistema",),
                routes=(),
                transition="→ DENIED(2)",
                source="src/reservations_management/tasks.py:92,211",
            ),
        ),
    ),
)
