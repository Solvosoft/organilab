# encoding: utf-8
"""El inventario: objetos del catálogo, sus instancias en estantes, y lo que se hace con ellas.

`Object` es la ficha del catálogo —un reactivo, un material, un equipo—; `ShelfObject` es
la instancia física que está en un estante concreto con su cantidad, su lote y su fecha
de vencimiento. Casi todo el trabajo diario del laboratorio pasa por aquí.

Incluye los informes periódicos, que son el único flujo del módulo con un permiso de
aprobación diferenciado (`can_manage_inform_status`), y la carga masiva desde fichero.
"""

from presentation.feature_catalog import Feature, Step

OPERADORES = ("administrador_laboratorio", "tecnico_laboratorio",
              "asistente_laboratorio", "lectura_agregado_sustancias")
CONSULTA = OPERADORES + ("estudiante", "profesor", "regente", "solo_lectura",
                         "administrativo_superior")

FEATURES = (
    Feature(
        id="INV-01",
        name="Mantener el catálogo de objetos: reactivos, materiales y equipos",
        module="laboratory",
        kind="ui",
        description=(
            "La ficha maestra de cada cosa que puede haber en el laboratorio, con sus "
            "características y sus rasgos. Los tres listados —sustancias, materiales y "
            "equipos— son la misma pantalla filtrada por el tipo de objeto."
        ),
        priority="P1",
        doc="docs/source/desc_funcionalidades/materia_con.rst",
        steps=(
            Step(
                id="listar",
                name="Listar sustancias, materiales y equipos",
                actors=CONSULTA,
                routes=("laboratory:sustance_list", "laboratory:equipment_list",
                        "laboratory:object_view"),
                permissions=("laboratory.view_object",),
                source="src/laboratory/views/objects.py view_reactive_list, view_equipment_list",
            ),
            Step(
                id="crear",
                name="Dar de alta un objeto en el catálogo",
                actors=OPERADORES,
                routes=("laboratory:objectview_create",),
                permissions=("laboratory.add_object",),
                source="src/laboratory/views/objects.py ObjectCreateView",
            ),
            Step(
                id="editar",
                name="Editar o borrar un objeto del catálogo",
                actors=OPERADORES,
                routes=("laboratory:objectview_update", "laboratory:objectview_delete"),
                permissions=("laboratory.change_object", "laboratory.delete_object"),
                source="src/laboratory/views/objects.py ObjectUpdateView, ObjectDeleteView",
            ),
            Step(
                id="rasgos",
                name="Consultar los rasgos de los objetos",
                actors=CONSULTA,
                routes=("laboratory:objectfeatures_view",),
                permissions=("laboratory.view_objectfeatures",),
                source="src/laboratory/views/objectfeature.py",
            ),
            Step(
                id="proveedores",
                name="Consultar los proveedores",
                actors=CONSULTA,
                routes=("laboratory:provider_view",),
                permissions=("laboratory.view_provider",),
                source="src/laboratory/views/provider.py",
            ),
        ),
    ),
    Feature(
        id="INV-02",
        name="Operar un objeto en el estante: crear, aumentar, disminuir, mover y desechar",
        module="laboratory",
        kind="ui",
        description=(
            "El trabajo diario: poner una caja de reactivo en un estante, consumir "
            "parte, reponer, moverla a otro estante, consultar su detalle con su QR y "
            "su bitácora, y al final desecharla. Todo pasa por modales sobre la vista "
            "del laboratorio."
        ),
        priority="P1",
        doc="docs/source/desc_funcionalidades/admin_estan.rst",
        steps=(
            Step(
                id="listar",
                name="Ver los objetos de un estante",
                actors=CONSULTA,
                routes=("laboratory:list_shelfobject",),
                permissions=(),
                source="src/laboratory/views/shelfobject.py list_shelfobject",
            ),
            Step(
                id="crear",
                name="Colocar un objeto en el estante",
                actors=OPERADORES + ("estudiante", "depositante_residuos"),
                routes=("laboratory:shelfobject_create",),
                permissions=("laboratory.add_shelfobject",),
                source="src/laboratory/views/shelfobject.py ShelfObjectCreate",
            ),
            Step(
                id="detalle",
                name="Abrir el detalle del objeto, con su QR",
                actors=CONSULTA,
                routes=("laboratory:shelfobject_detail",
                        "laboratory:download_shelfobject_qr",
                        "laboratory:equipment_shelfobject_detail"),
                permissions=("laboratory.view_shelfobject",),
                source="src/laboratory/views/shelfobject.py ShelfObjectDetail",
            ),
            Step(
                id="modificar",
                name="Editar la cantidad, el límite y los datos del objeto",
                actors=OPERADORES + ("estudiante",),
                routes=("laboratory:shelfobject_edit",
                        "laboratory:shelfobject_searchupdate",
                        "laboratory:get_shelfobject_limit",
                        "laboratory:shelf_object_hcode"),
                permissions=("laboratory.change_shelfobject",),
                source="src/laboratory/views/shelfobject.py ShelfObjectEdit, edit_limit_object",
            ),
            Step(
                id="etiquetar",
                name="Generar la etiqueta del objeto",
                actors=CONSULTA,
                routes=("laboratory:generate_shelfobject_label",
                        "laboratory:shelfobject_label"),
                permissions=(),
                source="src/laboratory/views/shelfobject.py generate_shelfobject_label",
            ),
            Step(
                id="desechar",
                name="Borrar o desechar el objeto",
                actors=OPERADORES + ("depositante_residuos", "tesista_desechos"),
                routes=("laboratory:shelfobject_delete",
                        "laboratory:disposal_substance"),
                permissions=("laboratory.delete_shelfobject",),
                source="src/laboratory/views/shelfobject.py ShelfObjectDelete",
            ),
            Step(
                id="reactivos",
                name="Ver los reactivos del estante y su reorden",
                actors=OPERADORES,
                routes=("laboratory:shel_objects_reactives",),
                permissions=("laboratory.can_manage_reorder",),
                source="src/laboratory/views/shelfobject.py shelf_object_reagents",
            ),
        ),
        notes=(
            "La regla de descarte cambia el permiso según el estante: si el estante es "
            "de descarte, borrar exige `can_manage_disposal` en vez de "
            "`delete_shelfobject`. Depende del contenedor, no del objeto — es el único "
            "permiso del sistema que se decide por el sitio.",
        ),
    ),
    Feature(
        id="INV-03",
        name="Cargar inventario en masa desde un fichero",
        module="laboratory",
        kind="ui",
        description=(
            "La alternativa a dar de alta reactivo por reactivo: se sube un fichero, se "
            "revisa lo que se va a crear y se confirma. Es la vía de entrada de un "
            "laboratorio que empieza."
        ),
        priority="P2",
        steps=(
            Step(
                id="subir",
                name="Subir el fichero y previsualizar",
                actors=OPERADORES,
                routes=("laboratory:load_archive",),
                permissions=("laboratory.add_shelfobject",),
                source="src/laboratory/views/loadArchive.py load_archive",
            ),
            Step(
                id="confirmar",
                name="Confirmar y crear los objetos en el estante",
                actors=OPERADORES,
                routes=("laboratory:load_archive_create_shelfobjects",),
                permissions=("laboratory.add_shelfobject",),
                source="src/laboratory/views/loadArchive.py upload_reactives",
            ),
        ),
    ),
    Feature(
        id="INV-04",
        name="Vigilar existencias, vencimientos y límites",
        module="laboratory",
        kind="ui",
        description=(
            "El panel de existencias de reactivos, los avisos cuando algo baja del "
            "límite o está por vencer, y la posibilidad de silenciarlos. Buena parte "
            "del trabajo lo hace el planificador, no una persona."
        ),
        priority="P2",
        steps=(
            Step(
                id="panel_stock",
                name="Ver el panel de existencias de reactivos",
                actors=OPERADORES + ("regente",),
                routes=("laboratory:reactive_stock_list",),
                permissions=("laboratory.view_laboratory",),
                source="src/laboratory/views/objectlimits.py ReactiveStockDashboard",
            ),
            Step(
                id="silenciar",
                name="Silenciar los avisos de un objeto",
                actors=OPERADORES,
                routes=("laboratory:block_notification",),
                permissions=(),
                source="src/laboratory/views/objects.py block_notifications",
            ),
        ),
    ),
    Feature(
        id="INV-05",
        name="Vigilar el inventario automáticamente y avisar",
        module="laboratory",
        kind="celery",
        description=(
            "Las cinco tareas programadas del inventario: avisar cuando un producto "
            "baja de su límite, registrar el máximo diario, avisar de los "
            "vencimientos, preparar el reporte mensual de precursores y limpiar las "
            "relaciones huérfanas entre organización y laboratorio. Ninguna tiene "
            "pantalla; todas crean tareas pendientes o mandan correo."
        ),
        priority="P2",
        steps=(
            Step(
                id="limites",
                name="Avisar de los productos que llegaron a su límite",
                actors=("sistema",),
                routes=(),
                transition="crea PendingTask para los responsables del laboratorio",
                source="src/laboratory/tasks.py:69 notify_about_product_limit_reach",
            ),
            Step(
                id="stock_maximo",
                name="Registrar el stock máximo del día",
                actors=("sistema",),
                routes=(),
                source="src/laboratory/tasks.py add_maximum_object_stock_per_day",
            ),
            Step(
                id="vencimientos",
                name="Avisar por correo de los objetos por vencer",
                actors=("sistema",),
                routes=(),
                source="src/laboratory/tasks.py send_expiration_email",
            ),
            Step(
                id="precursores",
                name="Preparar el reporte mensual de precursores",
                actors=("sistema",),
                routes=(),
                source="src/laboratory/tasks.py:197 create_precursor_reports",
            ),
            Step(
                id="limpieza",
                name="Limpiar las relaciones huérfanas organización-laboratorio",
                actors=("sistema",),
                routes=(),
                source="src/laboratory/tasks.py remove_relation_organization_laboratory",
            ),
        ),
    ),
    Feature(
        id="INV-06",
        name="Redactar y aprobar informes periódicos",
        module="laboratory",
        kind="ui",
        description=(
            "Los informes del laboratorio, con su agendador de periodos: se programa "
            "cada cuánto toca, alguien lo completa y **alguien distinto** cambia su "
            "estado. Es el único flujo del módulo con un permiso de aprobación propio."
        ),
        states=(
            'Inform.status: "Eraser" → "In Review" → "Finalized" '
            "(`laboratory/models.py:1643-1674`)",
        ),
        priority="P2",
        doc="docs/source/administrative_usage/informs.rst",
        steps=(
            Step(
                id="programar",
                name="Programar el periodo de los informes",
                actors=("administrador_laboratorio", "asistente_laboratorio"),
                routes=("laboratory:add_period_scheduler",
                        "laboratory:edit_period_scheduler",
                        "laboratory:detail_period_scheduler",
                        "laboratory:inform_index"),
                permissions=("laboratory.add_informscheduler",
                             "laboratory.change_informscheduler",
                             "laboratory.view_informscheduler",
                             "laboratory.view_inform"),
                source="src/laboratory/views/inform_period.py",
            ),
            Step(
                id="crear",
                name="Crear el informe",
                actors=("administrador_laboratorio", "asistente_laboratorio",
                        "tecnico_laboratorio"),
                routes=("laboratory:add_informs", "laboratory:get_informs"),
                permissions=("laboratory.add_inform", "laboratory.view_inform"),
                transition='→ status="Eraser"',
                source="src/laboratory/views/informs.py create_informs",
            ),
            Step(
                id="completar",
                name="Completar el informe y cambiar su estado",
                actors=("administrador_laboratorio",),
                routes=("laboratory:complete_inform",),
                permissions=("laboratory.change_inform",),
                transition='"Eraser" → "In Review" → "Finalized"',
                source="src/laboratory/views/informs.py complete_inform",
            ),
            Step(
                id="borrar",
                name="Retirar un informe",
                actors=("administrador_laboratorio",),
                routes=("laboratory:remove_inform",),
                permissions=("laboratory.delete_inform",),
                source="src/laboratory/views/informs.py remove_inform",
            ),
        ),
        notes=(
            "El cambio de estado se protege con `laboratory.can_manage_inform_status` "
            "(`models.py:1674`) y se comprueba en la plantilla "
            "(`complete_inform.html:25`). Es el contraejemplo de HALLAZGO-ACAD-1: los "
            "mismos tres estados que `MyProcedure`, pero aquí el paso de aprobación sí "
            "tiene permiso propio.",
            "HALLAZGO-INV-1: **el repositorio no dice quién tiene ese permiso.** "
            "`update_roles.py` solo lo menciona en `:100`, dentro del "
            "`remove_permissions` de «Depositante de residuos» — es decir, dice quién "
            "*no* lo tiene. El conjunto de permisos de cada rol canónico no está "
            "versionado en ninguna parte: `update_roles.py` aplica deltas sobre roles "
            "que supone existentes (`filter(...).first()` → «not found, skipping») y "
            "`upload_org_and_users.py:45` hace `Rol.objects.get(...)`, que en una "
            "instalación limpia revienta. La definición vive solo en las bases de "
            "producción.",
        ),
    ),
    Feature(
        id="INV-07",
        name="Consultar los reportes de inventario del laboratorio",
        module="laboratory",
        kind="ui",
        description=(
            "Los reportes que viven en el propio módulo de laboratorio, antes de pasar "
            "por el ciclo asíncrono de `report`: inventario químico, códigos H, "
            "presencia de reactivos en la organización y cobertura de fichas."
        ),
        priority="P2",
        steps=(
            Step(
                id="indice",
                name="Abrir el índice de reportes del laboratorio",
                actors=CONSULTA,
                routes=("laboratory:reports", "laboratory:chemicalinventory",
                        "laboratory:organizationreactivepresence"),
                permissions=("laboratory.view_report",),
                source="src/laboratory/views/reports.py report_index",
            ),
            Step(
                id="hcode",
                name="Consultar y descargar los reportes de códigos H",
                actors=CONSULTA,
                routes=("laboratory:h_code_reports",
                        "laboratory:download_h_code_reports"),
                permissions=("laboratory.do_report",),
                source="src/laboratory/views/laboratory.py HCodeReports",
            ),
            Step(
                id="objetos",
                name="Descargar el reporte de objetos en estantes",
                actors=CONSULTA,
                routes=("laboratory:reports_shelf_objects",),
                permissions=("laboratory.do_report",),
                source="src/laboratory/views/reports.py report_shelf_objects",
            ),
            Step(
                id="cobertura_sds",
                name="Ver la cobertura de fichas de seguridad",
                actors=CONSULTA,
                routes=("laboratory:sds_coverage_svg",),
                permissions=(),
                source="src/laboratory/views/reports.py sds_coverage_svg",
            ),
        ),
    ),
    Feature(
        id="INV-08",
        name="Documentar protocolos del laboratorio",
        module="laboratory",
        kind="ui",
        description=(
            "Los protocolos que el laboratorio documenta y adjunta. Usan borrado "
            "lógico: al eliminarlos van a la papelera de LAB-07."
        ),
        priority="P3",
        steps=(
            Step(
                id="listar",
                name="Listar protocolos",
                actors=CONSULTA,
                routes=("laboratory:protocol_list",),
                permissions=("laboratory.view_protocol",),
                source="src/laboratory/protocol/views.py protocol_list",
            ),
            Step(
                id="crear_editar",
                name="Crear o editar un protocolo",
                actors=OPERADORES,
                routes=("laboratory:protocol_create", "laboratory:protocol_update"),
                permissions=("laboratory.add_protocol", "laboratory.change_protocol"),
                source="src/laboratory/protocol/views.py",
            ),
            Step(
                id="borrar",
                name="Borrar un protocolo (va a la papelera)",
                actors=OPERADORES,
                routes=("laboratory:protocol_delete",),
                permissions=("laboratory.delete_protocol",),
                source="src/laboratory/protocol/views.py ProtocolDeleteView",
            ),
        ),
    ),
)
