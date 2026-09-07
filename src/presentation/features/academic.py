# encoding: utf-8
"""Procedimientos académicos: plantillas de práctica y su ejecución.

Dos actores claros —quien diseña la guía de práctica y quien la ejecuta— y **un tercero
que el código no tiene**: `MyProcedure` declara los mismos tres estados que un flujo de
revisión (`Eraser` → `In Review` → `Finalized`, `academic/models.py:33-37`), pero no hay
ningún revisor. Ver ACAD-02.
"""

from presentation.feature_catalog import Feature, Step

PROCEDURE_STATES = (
    'MyProcedure.status: "Eraser" → "In Review" → "Finalized" '
    "(`academic/models.py:33-37`)",
)

AUTORES = ("profesor", "administrador_laboratorio", "asistente_laboratorio")
EJECUTORES = ("estudiante", "profesor", "tecnico_laboratorio",
              "asistente_laboratorio")

FEATURES = (
    Feature(
        id="ACAD-01",
        name="Diseñar una plantilla de procedimiento con sus pasos",
        module="academic",
        kind="ui",
        description=(
            "El docente crea la plantilla de una práctica, le añade pasos ordenados y "
            "declara qué objetos del inventario requiere cada uno. Es lo que después "
            "se instancia para cada grupo y lo que dispara la reserva del material."
        ),
        priority="P2",
        doc="docs/source/administrative_usage/procedure.rst",
        steps=(
            Step(
                id="crear_plantilla",
                name="Crear la plantilla del procedimiento",
                actors=AUTORES,
                routes=("academic:procedure_create",),
                permissions=("academic.add_procedure",),
                source="src/academic/views.py:292 ProcedureCreateView",
            ),
            Step(
                id="listar_plantillas",
                name="Listar y consultar plantillas",
                actors=AUTORES + ("estudiante", "solo_lectura"),
                routes=("academic:procedure_list", "academic:procedure_detail",
                        "academic:get_procedure"),
                permissions=("academic.view_procedure",),
                source="src/academic/views.py:282 ProcedureListView",
            ),
            Step(
                id="editar_plantilla",
                name="Editar la plantilla",
                actors=AUTORES,
                routes=("academic:procedure_update",),
                permissions=("academic.change_procedure",),
                source="src/academic/views.py:335 ProcedureUpdateView",
            ),
            Step(
                id="anadir_pasos",
                name="Añadir pasos a la plantilla",
                actors=AUTORES,
                routes=("academic:procedure_step", "academic:add_steps_wrapper"),
                permissions=("academic.add_procedurestep",),
                source="src/academic/views.py:380 ProcedureStepCreateView",
            ),
            Step(
                id="editar_paso",
                name="Editar un paso",
                actors=AUTORES,
                routes=("academic:update_step",),
                permissions=("academic.change_procedurestep",),
                source="src/academic/views.py:454 ProcedureStepUpdateView",
            ),
            Step(
                id="borrar",
                name="Borrar un paso o la plantilla completa",
                actors=AUTORES,
                routes=("academic:delete_step", "academic:delete_procedure"),
                permissions=("academic.delete_procedurestep",
                             "academic.delete_procedure"),
                source="src/academic/views.py delete_step, delete_procedure",
            ),
        ),
    ),
    Feature(
        id="ACAD-02",
        name="Ejecutar un procedimiento y reservar el material que necesita",
        module="academic",
        kind="ui",
        description=(
            "A partir de una plantilla se crea «mi procedimiento» para un laboratorio "
            "concreto, se genera de golpe la reserva de todo el material que los pasos "
            "requieren, y se va completando hasta darlo por finalizado."
        ),
        states=PROCEDURE_STATES,
        priority="P2",
        doc="docs/source/general_usage/procedure.rst",
        steps=(
            Step(
                id="instanciar",
                name="Crear mi procedimiento a partir de una plantilla",
                actors=EJECUTORES,
                routes=("academic:add_my_procedures",),
                permissions=("academic.add_myprocedure",),
                transition='→ MyProcedure.status="Eraser"',
                source="src/academic/views.py:104 create_my_procedures",
            ),
            Step(
                id="listar_mis",
                name="Ver mis procedimientos",
                actors=EJECUTORES,
                routes=("academic:get_my_procedures",),
                permissions=("academic.view_myprocedure",),
                source="src/academic/views.py get_my_procedures",
            ),
            Step(
                id="reservar_material",
                name="Generar la reserva de todo el material del procedimiento",
                actors=EJECUTORES,
                routes=("academic:generate_reservation",),
                permissions=("reservations_management.add_reservedproducts",),
                transition="crea Reservations(is_massive=True) — entra en RES-01",
                source="src/academic/views.py:606-610,727,825",
            ),
            Step(
                id="completar",
                name="Completar los pasos y cambiar el estado",
                actors=EJECUTORES,
                routes=("academic:complete_my_procedure",),
                permissions=("academic.change_myprocedure",),
                transition='"Eraser" → "In Review" → "Finalized", según el POST',
                source="src/academic/views.py:205-256",
            ),
            Step(
                id="retirar",
                name="Quitar mi procedimiento",
                actors=EJECUTORES,
                routes=("academic:remove_my_procedure",),
                permissions=("academic.delete_myprocedure",),
                source="src/academic/views.py remove_my_procedure",
            ),
        ),
        notes=(
            "HALLAZGO-ACAD-1: **no hay rol revisor.** `MyProcedure` declara los tres "
            "estados de un flujo de revisión, pero `complete_my_procedure` "
            "(`views.py:253`) toma el `status` directamente del POST bajo el mismo "
            "`change_myprocedure` que sirve para editarlo. Quien ejecuta el "
            "procedimiento se lo aprueba a sí mismo: el estado «In Review» no tiene "
            "quien lo revise. Compárese con `laboratory.Inform` "
            "(`laboratory/models.py:1643-1674`), que tiene los mismos tres estados "
            "**y sí** un permiso de aprobación aparte "
            "(`laboratory.can_manage_inform_status`).",
            "La reserva masiva nace aquí pero se aprueba y se cierra en RES-01: es el "
            "único flujo del sistema que cruza dos módulos con actores distintos.",
        ),
    ),
)
