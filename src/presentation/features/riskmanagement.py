# encoding: utf-8
"""Gestión de riesgo: zonas, incidentes, edificios, regencia y evaluaciones IPER.

El IPER (identificación de peligros y evaluación de riesgos, norma INTE T55) es el otro
flujo multi-actor del sistema, y el único con **tres actores separados por permisos de
verdad**: quien solicita el llenado (`request_iper`), el laboratorio que lo llena
(`change_iperassessment`) y quien audita sin poder tocar (`view_all_iper` +
`add_iperobservation`, con `view_riskzone` explícitamente retirado).

Es también el módulo con más rutas sin ninguna prueba unitaria del proyecto.
"""

from presentation.feature_catalog import Feature, Step

IPER_STATES = (
    'IPERAssessment.status: "draft" → "completed" → "obsolete" '
    "(`risk_management/models.py:470-476`)",
)

GESTORES_RIESGO = ("administrativo_superior", "administrador_laboratorio",
                   "regente", "asistente_laboratorio")
CONSULTA_RIESGO = GESTORES_RIESGO + ("solo_lectura", "tecnico_laboratorio")

FEATURES = (
    Feature(
        id="RISK-01",
        name="Definir las zonas de riesgo de la organización",
        module="risk_management",
        kind="ui",
        description=(
            "El mapa de dónde está el peligro: se dan de alta las zonas, su tipo y sus "
            "restricciones de prioridad, se asocian a laboratorios y se consultan en un "
            "panel con su reporte."
        ),
        priority="P2",
        doc="docs/source/desc_funcionalidades/riesgo_gest.rst",
        steps=(
            Step(
                id="listar_zonas",
                name="Listar y abrir el detalle de una zona de riesgo",
                actors=CONSULTA_RIESGO,
                routes=("riskmanagement:riskzone_list",
                        "riskmanagement:riskzone_detail"),
                permissions=("risk_management.view_riskzone",),
                source="src/risk_management/views.py ListZone, ZoneDetail",
            ),
            Step(
                id="crear_zona",
                name="Crear una zona de riesgo y su tipo",
                actors=GESTORES_RIESGO,
                routes=("riskmanagement:riskzone_create",
                        "riskmanagement:zone_type_add"),
                permissions=("risk_management.add_riskzone",
                             "risk_management.add_zonetype"),
                source="src/risk_management/views.py ZoneCreate, add_zone_type_view",
            ),
            Step(
                id="editar_zona",
                name="Editar o borrar una zona",
                actors=GESTORES_RIESGO,
                routes=("riskmanagement:riskzone_update",
                        "riskmanagement:riskzone_delete"),
                permissions=("risk_management.change_riskzone",
                             "risk_management.delete_riskzone"),
                source="src/risk_management/views.py ZoneEdit, ZoneDelete",
            ),
            Step(
                id="panel",
                name="Ver el panel de zonas y su reporte",
                actors=CONSULTA_RIESGO,
                routes=("riskmanagement:zone_dashboard",
                        "riskmanagement:risk_report"),
                permissions=("laboratory.view_report",),
                source="src/risk_management/views.py ZoneDashboard, RiskZoneReport",
            ),
            Step(
                id="jornadas",
                name="Consultar las jornadas de trabajo de la zona",
                actors=CONSULTA_RIESGO,
                routes=("riskmanagement:workday_list",),
                permissions=("risk_management.view_workday",),
                source="src/risk_management/views.py workday_view",
            ),
        ),
        notes=(
            "`zone_dashboard` no declara ningún permiso inspeccionable, a diferencia "
            "del resto del módulo.",
        ),
    ),
    Feature(
        id="RISK-02",
        name="Reportar y dar seguimiento a un incidente",
        module="risk_management",
        kind="ui",
        description=(
            "Alguien registra lo que pasó en un laboratorio, se consulta el histórico y "
            "se descarga el reporte. **No hay flujo de aprobación**: el incidente no "
            "tiene estado ni quien lo valide, solo el CRUD y sus permisos."
        ),
        priority="P2",
        steps=(
            Step(
                id="reportar",
                name="Registrar un incidente",
                actors=CONSULTA_RIESGO + ("estudiante", "profesor"),
                routes=("riskmanagement:incident_create",),
                permissions=("risk_management.add_incidentreport",),
                source="src/risk_management/incidents.py IncidentReportCreate",
            ),
            Step(
                id="consultar",
                name="Listar incidentes y abrir su detalle",
                actors=CONSULTA_RIESGO,
                routes=("riskmanagement:incident_list",
                        "riskmanagement:incident_detail"),
                permissions=("risk_management.view_incidentreport",),
                source="src/risk_management/incidents.py IncidentReportList, Detail",
            ),
            Step(
                id="corregir",
                name="Corregir o eliminar un incidente",
                actors=GESTORES_RIESGO,
                routes=("riskmanagement:incident_update",
                        "riskmanagement:incident_delete"),
                permissions=("risk_management.change_incidentreport",
                             "risk_management.delete_incidentreport"),
                source="src/risk_management/incidents.py IncidentReportEdit, Delete",
            ),
            Step(
                id="descargar",
                name="Descargar el reporte de incidentes",
                actors=CONSULTA_RIESGO,
                routes=("riskmanagement:incident_report",),
                permissions=("laboratory.do_report",),
                source="src/risk_management/incidents.py report_incidentreport",
            ),
        ),
        notes=(
            "HALLAZGO-RISK-1: el incidente no tiene estado ni aprobador "
            "(`models.py:120`). Quien lo reporta y quien lo corrige se distinguen solo "
            "por `add` frente a `change`; nadie lo cierra ni lo valida.",
        ),
    ),
    Feature(
        id="RISK-03",
        name="Mantener edificios, estructuras y regentes",
        module="risk_management",
        kind="ui",
        description=(
            "Los datos maestros del módulo: los edificios y sus estructuras físicas, y "
            "el registro de regentes con su tipo profesional. El regente importa más "
            "allá de este módulo: es destinatario implícito de tareas pendientes."
        ),
        priority="P3",
        steps=(
            Step(
                id="edificios",
                name="Listar, crear y editar edificios",
                actors=GESTORES_RIESGO,
                routes=("riskmanagement:buildings_list",
                        "riskmanagement:buildings_create",
                        "riskmanagement:buildings_update"),
                permissions=("risk_management.view_buildings",
                             "risk_management.add_buildings"),
                source="src/risk_management/views.py buildings_view, buildings_actions",
            ),
            Step(
                id="estructuras",
                name="Listar, crear y editar estructuras",
                actors=GESTORES_RIESGO,
                routes=("riskmanagement:structures_list",
                        "riskmanagement:structures_create",
                        "riskmanagement:structures_update"),
                permissions=("risk_management.view_structure",
                             "risk_management.add_structure"),
                source="src/risk_management/views.py structure_view, structure_actions",
            ),
            Step(
                id="regentes",
                name="Consultar los regentes del laboratorio",
                actors=CONSULTA_RIESGO,
                routes=("riskmanagement:regents",),
                permissions=("risk_management.view_regent",),
                source="src/risk_management/views.py regent_view",
            ),
        ),
        notes=(
            "Editar un edificio o una estructura exige `add_*`, no `change_*` "
            "(`buildings_actions`, `structure_actions`): la vista de alta y la de "
            "edición son la misma y comparten el permiso de alta. Un rol al que se le "
            "quiera dar solo edición no se puede configurar.",
        ),
    ),
    Feature(
        id="IPER-01",
        name="Solicitar, llenar y auditar una evaluación IPER",
        module="risk_management",
        kind="ui",
        description=(
            "El flujo de la norma INTE T55, y el que mejor separa actores de todo "
            "Organilab: alguien de la organización **solicita** a los laboratorios de "
            "una zona que llenen su IPER —lo que genera una tarea pendiente para cada "
            "responsable—, el laboratorio la **llena** identificando peligros y "
            "valorando el riesgo, la marca como completada, y un auditor externo la "
            "**observa** sin poder modificarla. Al revisarla se clona la versión "
            "anterior, que queda obsoleta."
        ),
        states=IPER_STATES,
        priority="P1",
        doc="plans/IPER_DESIGN.md",
        steps=(
            Step(
                id="solicitar",
                name="Solicitar a los laboratorios de una zona que llenen su IPER",
                actors=("administrador_iper", "administrativo_superior"),
                routes=("riskmanagement:iper_request_zone",),
                permissions=("risk_management.request_iper",),
                transition=(
                    "crea una PendingTask por laboratorio, dirigida al responsable "
                    "de cada uno"
                ),
                source="src/risk_management/iper_views.py:560-585",
            ),
            Step(
                id="crear",
                name="Crear la evaluación del laboratorio",
                actors=("administrador_laboratorio", "regente_lab",
                        "administrador_iper"),
                routes=("riskmanagement:iper_create",),
                permissions=("risk_management.add_iperassessment",),
                transition='→ status="draft"',
                source="src/risk_management/iper_views.py IPERAssessmentCreate",
            ),
            Step(
                id="peligros",
                name="Identificar peligros y valorar el riesgo",
                actors=("administrador_laboratorio", "regente_lab",
                        "administrador_iper"),
                routes=("riskmanagement:iper_hazard_create",
                        "riskmanagement:iper_hazard_update",
                        "riskmanagement:iper_hazard_delete",
                        "riskmanagement:iper_update"),
                permissions=("risk_management.change_iperassessment",),
                source="src/risk_management/iper_views.py iper_hazard_action",
            ),
            Step(
                id="completar",
                name="Marcar la evaluación como completada (o devolverla a borrador)",
                actors=("administrador_laboratorio", "regente_lab",
                        "administrador_iper"),
                routes=("riskmanagement:iper_toggle_status",),
                permissions=("risk_management.change_iperassessment",),
                transition=(
                    '"draft" ⇄ "completed"; una obsoleta ya no puede cambiar '
                    "(`iper_views.py:350-360`)"
                ),
                source="src/risk_management/iper_views.py:347-368",
            ),
            Step(
                id="revisar_versionando",
                name="Clonar la evaluación para actualizarla",
                actors=("administrador_laboratorio", "regente_lab",
                        "administrador_iper"),
                routes=("riskmanagement:iper_clone",),
                permissions=("risk_management.add_iperassessment",),
                transition='la versión anterior pasa a "obsolete"',
                source="src/risk_management/iper_views.py iper_clone_for_update",
            ),
            Step(
                id="auditar",
                name="Observar la evaluación sin poder modificarla",
                actors=("auditor_iper",),
                routes=("riskmanagement:iper_observation_add",),
                permissions=("risk_management.add_iperobservation",),
                source="src/risk_management/iper_views.py iper_observation_add",
            ),
            Step(
                id="consultar",
                name="Listar evaluaciones, ver el detalle y su histórico",
                actors=("auditor_iper", "administrador_iper",
                        "administrador_laboratorio", "regente", "solo_lectura"),
                routes=("riskmanagement:iper_list", "riskmanagement:iper_detail",
                        "riskmanagement:iper_history", "riskmanagement:iper_lab_help"),
                permissions=("risk_management.view_iperassessment",),
                source="src/risk_management/iper_views.py IPERAssessmentList, Detail",
            ),
            Step(
                id="panel",
                name="Ver el panel consolidado de IPER",
                actors=("administrador_iper", "administrativo_superior",
                        "auditor_iper"),
                routes=("riskmanagement:iper_dashboard",),
                permissions=("risk_management.view_iper_dashboard",),
                source="src/risk_management/iper_views.py IPERDashboard",
            ),
            Step(
                id="anonimato",
                name="Alternar el anonimato de la evaluación",
                actors=("administrador_laboratorio", "administrador_iper"),
                routes=("riskmanagement:iper_toggle_anonymous",),
                permissions=("risk_management.change_iperassessment",),
                source="src/risk_management/iper_views.py iper_toggle_anonymous",
            ),
            Step(
                id="catalogo",
                name="Mantener el catálogo IPER de la organización raíz",
                actors=("administrador_iper",),
                routes=("riskmanagement:iper_catalog_add",),
                permissions=("risk_management.manage_iper_catalog",),
                source="src/risk_management/iper_views.py iper_catalog_add",
            ),
            Step(
                id="borrar",
                name="Eliminar una evaluación",
                actors=("administrador_iper", "administrativo_superior"),
                routes=("riskmanagement:iper_delete",),
                permissions=("risk_management.delete_iperassessment",),
                source="src/risk_management/iper_views.py IPERAssessmentDelete",
            ),
        ),
        notes=(
            "Es el flujo con la separación de actores mejor implementada del sistema: "
            "cuatro permisos propios (`view_all_iper`, `request_iper`, "
            "`view_iper_dashboard`, `manage_iper_catalog`, `models.py:531-539`) y dos "
            "roles dedicados que además **se autocrean** si no existen "
            "(`update_roles.py:1231,1254`), a diferencia del resto del catálogo de "
            "roles. Al `Auditor IPER` se le retira `view_riskzone` a propósito "
            "(`:1243`): puede auditar la evaluación sin ver el mapa de zonas.",
            "Contraste con RES-01: aquí solicitar, llenar y auditar son tres permisos "
            "distintos; en reservaciones, cuatro actores del negocio son dos permisos.",
        ),
    ),
    Feature(
        id="IPER-02",
        name="Recordar por correo las evaluaciones IPER que toca actualizar",
        module="risk_management",
        kind="celery",
        description=(
            "Cada mañana el planificador busca las evaluaciones periódicas cuyo plazo "
            "vence y avisa a quien tiene que actualizarlas."
        ),
        priority="P3",
        steps=(
            Step(
                id="recordar",
                name="Enviar los recordatorios de actualización",
                actors=("sistema",),
                routes=(),
                transition="crea PendingTask y envía correo a los responsables",
                source="src/risk_management/tasks.py:42-67 send_iper_update_reminders",
            ),
        ),
    ),
    Feature(
        id="RISK-04",
        name="Generar la bitácora diaria de establecimientos",
        module="risk_management",
        kind="celery",
        description=(
            "Tarea programada que consolida los registros de establecimiento del día. "
            "No tiene pantalla: solo se observa por sus efectos."
        ),
        priority="P3",
        steps=(
            Step(
                id="consolidar",
                name="Crear los reportes de establecimiento",
                actors=("sistema",),
                routes=(),
                source="src/risk_management/tasks.py create_establishment_reports",
            ),
        ),
    ),
)
